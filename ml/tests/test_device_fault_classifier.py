import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ML_DIR = Path(__file__).resolve().parents[1]
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))


from device_fault_classifier import DeviceFaultClassifier, DeviceFaultDataProcessor, DeviceFaultModelBundle, DeviceFaultTrainingPipeline  # noqa: E402
from predict import DeviceFaultPredictor  # noqa: E402


class ThresholdEstimator:
    def fit(self, X, y, sample_weight=None):
        numeric_columns = X.select_dtypes(include=['number']).columns.tolist()
        self.feature_name = numeric_columns[0] if numeric_columns else X.columns[0]
        self.threshold = float(pd.Series(X[self.feature_name]).median())
        self.classes_ = np.array(sorted(set(y)))
        return self

    def predict(self, X):
        low_class = self.classes_[0]
        high_class = self.classes_[-1]
        first_feature = pd.Series(X[self.feature_name]).to_numpy()
        return np.where(first_feature > self.threshold, high_class, low_class)

    def predict_proba(self, X):
        predictions = self.predict(X)
        probabilities = np.full((len(predictions), len(self.classes_)), 0.05, dtype=float)
        for index, predicted_class in enumerate(predictions):
            class_index = list(self.classes_).index(predicted_class)
            probabilities[index, :] = 0.05
            probabilities[index, class_index] = 0.95
        return probabilities


def build_fridge_frame():
    rows = []
    for idx in range(12):
        is_fault = idx >= 6
        rows.append(
            {
                'internal_temperature': 3.5 + idx,
                'ambient_temp': 21.0 + (idx % 3),
                'compressor_load': 95.0 + (idx * 10),
                'door_open_time': 10.0 + idx,
                'humidity': 35.0 + idx,
                'fan_rpm': 1400.0 + (idx * 5),
                'vibration_level': 0.8 if not is_fault else 2.1,
                'line_voltage': 228.0 + (idx % 4),
                'Label': 'Healthy' if not is_fault else 'Compressor_Fault',
            }
        )
    return pd.DataFrame(rows)


class DeviceFaultClassifierTests(unittest.TestCase):
    def setUp(self):
        self.processor = DeviceFaultDataProcessor()

    def test_data_processor_normalizes_aliases_and_detects_schema(self):
        df = build_fridge_frame()
        X, y, profile = self.processor.prepare_training_data(df, target_col='Label')

        self.assertEqual(profile.schema_name, 'smart_fridge')
        self.assertEqual(
            profile.feature_names,
            ['internal_temp', 'external_temp', 'compressor_power', 'door_open_duration', 'humidity', 'fan_speed', 'vibration_level', 'voltage'],
        )
        self.assertEqual(profile.target_column, 'Label')
        self.assertEqual(len(X.columns), 8)
        self.assertEqual(sorted(y.unique().tolist()), ['Compressor_Fault', 'Healthy'])

    def test_training_pipeline_trains_and_saves_model_bundle(self):
        df = build_fridge_frame()
        pipeline = DeviceFaultTrainingPipeline(
            data_processor=self.processor,
            classifier_factory=lambda: DeviceFaultClassifier(
                data_processor=self.processor,
                estimator_factory=ThresholdEstimator,
            ),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / 'unit_test_model.pkl'
            results = pipeline.train_from_dataframe(
                df,
                train_target='Label',
                test_size=0.25,
                cv_splits=2,
                model_out=model_path,
            )

            self.assertTrue(model_path.exists())
            self.assertIn('train_accuracy', results['metrics'])
            self.assertIn('accuracy', results['evaluation'])

            bundle = DeviceFaultModelBundle.load(model_path)
            self.assertEqual(bundle.feature_names[0], 'internal_temp')
            self.assertEqual(sorted(bundle.label_encoder.classes_.tolist()), ['Compressor_Fault', 'Healthy'])

    def test_multi_device_schema_preserves_sparse_columns(self):
        df = pd.DataFrame(
            [
                {
                    'device_type': 'fridge',
                    'fault_category': 'healthy',
                    'fault_label': 'healthy',
                    'internal_temp': 4.0,
                    'external_temp': 22.0,
                    'compressor_power': 140.0,
                    'door_open_duration': 5.0,
                    'humidity': 45.0,
                    'fan_speed': 2500.0,
                    'vibration_level': 0.02,
                    'voltage': 230.0,
                },
                {
                    'device_type': 'router',
                    'fault_category': 'connectivity_issue',
                    'fault_label': 'connectivity_drop',
                    'cpu_usage_pct': 35.0,
                    'mem_usage_pct': 60.0,
                    'temp_celsius': 48.0,
                    'packet_loss_pct': 12.0,
                    'latency_ms': 250.0,
                    'throughput_mbps': 5.0,
                    'voltage_v': 12.0,
                    'uptime_hours': 200.0,
                    'error_count_per_min': 3.0,
                },
            ]
        )

        X, y, profile = self.processor.prepare_training_data(df, target_col='fault_label', feature_schema='multi_device')
        self.assertEqual(profile.schema_name, 'multi_device')
        self.assertTrue(profile.preserve_missing_numeric)
        self.assertTrue(profile.allow_missing_features)
        self.assertIn('device_type', X.columns)
        self.assertTrue(pd.isna(X.loc[1, 'internal_temp']))
        self.assertTrue(pd.isna(X.loc[0, 'cpu_usage_pct']))
        self.assertEqual(sorted(y.tolist()), ['connectivity_drop', 'healthy'])

    def test_multi_device_predictor_accepts_partial_sparse_input(self):
        records = []
        for idx in range(6):
            records.append(
                {
                    'device_type': 'fridge',
                    'fault_category': 'healthy' if idx < 3 else 'mechanical_issue',
                    'fault_label': 'healthy' if idx < 3 else 'compressor_fault',
                    'internal_temp': 4.0 + idx,
                    'external_temp': 22.0,
                    'compressor_power': 140.0 + (idx * 15),
                    'door_open_duration': 5.0 + idx,
                    'humidity': 45.0,
                    'fan_speed': 2500.0,
                    'vibration_level': 0.02 if idx < 3 else 0.15,
                    'voltage': 230.0,
                }
            )
            records.append(
                {
                    'device_type': 'router',
                    'fault_category': 'healthy' if idx < 3 else 'connectivity_issue',
                    'fault_label': 'healthy' if idx < 3 else 'connectivity_drop',
                    'cpu_usage_pct': 20.0 + idx,
                    'mem_usage_pct': 30.0 + idx,
                    'temp_celsius': 40.0 + idx,
                    'packet_loss_pct': 0.0 if idx < 3 else 15.0,
                    'latency_ms': 15.0 if idx < 3 else 250.0,
                    'throughput_mbps': 220.0 if idx < 3 else 5.0,
                    'voltage_v': 12.0,
                    'uptime_hours': 100.0 + idx,
                    'error_count_per_min': 0.0 if idx < 3 else 4.0,
                }
            )

        df = pd.DataFrame(records)
        X, y, profile = self.processor.prepare_training_data(df, target_col='fault_label', feature_schema='multi_device')
        classifier = DeviceFaultClassifier(data_processor=self.processor, estimator_factory=ThresholdEstimator)
        classifier.train(X, y, cv_splits=2, dataset_profile=profile)

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / 'multi_device_predictor.pkl'
            classifier.save(model_path)

            predictor = DeviceFaultPredictor(model_path, data_processor=self.processor)
            result = predictor.predict_single(
                device_type='router',
                cpu_usage_pct=50.0,
                mem_usage_pct=65.0,
                temp_celsius=55.0,
                packet_loss_pct=20.0,
                latency_ms=300.0,
                throughput_mbps=3.0,
                voltage_v=12.0,
                uptime_hours=250.0,
                error_count_per_min=6.0,
            )

            self.assertIn(result['prediction'], y.unique().tolist())
            self.assertIn('probabilities', result)

    def test_predictor_can_load_saved_bundle_and_predict(self):
        df = build_fridge_frame()
        X, y, _ = self.processor.prepare_training_data(df, target_col='Label')
        classifier = DeviceFaultClassifier(data_processor=self.processor, estimator_factory=ThresholdEstimator)
        classifier.train(X, y, cv_splits=2)

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / 'predictor_model.pkl'
            classifier.save(model_path)

            predictor = DeviceFaultPredictor(model_path, data_processor=self.processor)
            result = predictor.predict_single(
                internal_temp=12.0,
                external_temp=23.0,
                compressor_power=180.0,
                door_open_duration=20.0,
                humidity=42.0,
                fan_speed=1450.0,
                vibration_level=2.2,
                voltage=230.0,
            )

            self.assertIn(result['prediction'], ['Healthy', 'Compressor_Fault'])
            self.assertIn('probabilities', result)
            self.assertTrue(result['suggestions'])


if __name__ == '__main__':
    unittest.main()