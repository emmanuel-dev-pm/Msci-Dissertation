from pathlib import Path

import pandas as pd

from device_fault_classifier import DEFAULT_DATA_PROCESSOR, DeviceFaultModelBundle

class DeviceFaultPredictor:
    """Load trained model and make predictions on new data."""

    def __init__(self, model_path, data_processor=None):
        self.model_path = model_path
        self.data_processor = data_processor or DEFAULT_DATA_PROCESSOR
        self.load_model()

    def load_model(self):
        """Load the trained model and encoders."""
        bundle = DeviceFaultModelBundle.load(self.model_path)
        self.model_bundle = bundle
        self.model = bundle.model
        self.label_encoder = bundle.label_encoder
        self.categorical_encoders = bundle.categorical_encoders
        self.feature_names = bundle.feature_names
        self.target_names = bundle.target_names or []
        self.numeric_fill_values = bundle.numeric_fill_values or {}
        self.schema_name = bundle.schema_name
        self.preserve_missing_numeric = bundle.preserve_missing_numeric
        self.allow_missing_features = bundle.allow_missing_features
        print(f"Loaded model from {self.model_path}")

    def preprocess_input(self, data):
        """Preprocess input data for prediction."""
        return self.data_processor.prepare_inference_frame(
            data,
            feature_names=self.feature_names,
            categorical_encoders=self.categorical_encoders,
            numeric_fill_values=self.numeric_fill_values,
            preserve_missing_numeric=self.preserve_missing_numeric,
            allow_missing_features=self.allow_missing_features,
        )

    def get_suggestions(self, prediction, features):
        """Generate repair suggestions based on fault type and feature values."""
        suggestions = []
        normalized_prediction = str(prediction).strip().lower()
        
        if normalized_prediction in {'normal', 'normal (no fault)', 'healthy'}:
            suggestions.append("Device is operating normally. No action required.")
            return suggestions
        
        if normalized_prediction == 'warning':
            suggestions.append("Monitor device closely for the next 24-48 hours.")
            suggestions.append("Check for unusual patterns in usage or environment.")
        
        if normalized_prediction == 'critical':
            suggestions.append("Immediate attention required. Consider powering down the device.")
            suggestions.append("Contact technical support or manufacturer for assistance.")

        fridge_fault_actions = {
            'gas_leak': [
                "Potential refrigerant issue detected. Inspect the cooling circuit immediately.",
                "Move food to backup cooling if the fridge stops maintaining temperature."
            ],
            'compressor_fault': [
                "Compressor behavior looks abnormal. Check compressor relay, wiring, and motor health.",
                "Minimize repeated power cycling until the compressor is inspected."
            ],
            'door_seal_leak': [
                "Inspect the door gasket for gaps, tears, or debris.",
                "Reduce unnecessary door opening until the seal issue is fixed."
            ],
            'sensor_failure': [
                "Sensor readings appear inconsistent. Check thermistor placement and sensor wiring.",
                "Recalibrate or replace the faulty sensor if readings remain unstable."
            ],
            'connectivity_drop': [
                "Network stability is degraded. Check WAN link quality and router placement.",
                "Inspect ISP connectivity and restart the router if drops continue."
            ],
            'packet_loss_issue': [
                "Packet loss is elevated. Check cabling, interference, and upstream congestion.",
                "Run a network health test and inspect QoS or bandwidth saturation."
            ],
            'firmware_fault': [
                "Firmware behavior looks abnormal. Verify firmware version and apply a stable update.",
                "Review device logs for crashes or recent failed upgrades."
            ],
            'power_supply_fault': [
                "Power delivery appears unstable. Check the adapter, cable, and outlet voltage.",
                "Replace the power supply if voltage fluctuation persists."
            ],
            'motor_failure': [
                "Motor performance is abnormal. Inspect the drive motor and belt assembly.",
                "Stop heavy-load cycles until the motor system is checked."
            ],
            'heater_fault': [
                "Heating behavior is outside the expected range. Inspect the heating element and thermostat.",
                "Avoid hot wash cycles until the heating circuit is verified."
            ],
            'door_lock_error': [
                "Door lock control failed. Inspect the latch, sensor, and lock actuator.",
                "Do not force the door; power-cycle the appliance after inspection."
            ],
            'imbalanced_load': [
                "Load balance is poor. Redistribute the laundry and check suspension stability.",
                "Inspect drum alignment if imbalance repeats on light loads."
            ],
            'drainage_blockage': [
                "Drain flow appears restricted. Check the pump filter, hose, and drain path for blockage.",
                "Clear standing water before running another cycle."
            ],
            'battery fault': ["Check battery health and charging behavior."],
            'cpu fault': ["Inspect CPU load, firmware, and background processes."],
            'network fault': ["Check connectivity, latency, and packet loss."],
            'overheat fault': ["Improve ventilation and inspect cooling components."],
            'overheating': ["Temperature is above normal. Improve ventilation and inspect cooling airflow."],
        }

        if normalized_prediction in fridge_fault_actions:
            suggestions.extend(fridge_fault_actions[normalized_prediction])
        
        temp_candidates = [
            features.get('temperature'),
            features.get('internal_temp'),
            features.get('temp_celsius'),
            features.get('Temperature (°C)'),
            features.get('water_temp'),
        ]
        power_candidates = [
            features.get('power_consumption'),
            features.get('compressor_power'),
            features.get('power_consumption_watts'),
        ]
        temp = next((value for value in temp_candidates if value is not None), None)
        power = next((value for value in power_candidates if value is not None), None)
        activity = features.get('user_activity', '')
        mode = features.get('device_mode', '')
        anomaly = features.get('anomaly_flag', 0)
        humidity = features.get('humidity', 0)
        vibration = features.get('vibration_level', 0)
        door_open_duration = features.get('door_open_duration', 0)
        
        if temp is not None and temp > 30:
            suggestions.append("High temperature detected. Ensure proper ventilation and cooling.")
        elif temp is not None and temp < 15:
            suggestions.append("Low temperature detected. Check environmental conditions.")
        
        if power is not None and power > 400:
            suggestions.append("High power consumption. Check for power-hungry processes or hardware issues.")
        elif power is not None and power < 50:
            suggestions.append("Low power consumption. Verify power supply and connections.")
        
        if anomaly == 1:
            suggestions.append("Anomaly flag is set. Review recent logs for error details.")

        if humidity > 60:
            suggestions.append("High humidity detected. Check for condensation and inspect door sealing.")

        if vibration > 1.8:
            suggestions.append("Elevated vibration detected. Inspect compressor mounts and fan balance.")

        if door_open_duration > 90:
            suggestions.append("Door has been open for an extended period. Check door usage and seal integrity.")
        
        if activity == 'Idle' and power > 200:
            suggestions.append("Device is idle but consuming high power. Check for background processes.")
        
        if mode == 'Manual' and normalized_prediction in ['warning', 'critical']:
            suggestions.append("Device is in manual mode. Consider switching to auto mode or checking manual settings.")
        
        return suggestions

    def predict(self, data):
        """Make predictions on preprocessed data."""
        X = self.preprocess_input(data)
        predictions_encoded = self.model.predict(X)
        predictions = self.label_encoder.inverse_transform(predictions_encoded)

        # Get prediction probabilities
        probabilities = self.model.predict_proba(X)
        class_names = self.label_encoder.classes_

        return predictions, probabilities, class_names

    def predict_single(self, **kwargs):
        """Make prediction on single data point."""
        data = pd.DataFrame([kwargs])
        predictions, probabilities, class_names = self.predict(data)

        prediction = predictions[0]
        suggestions = self.get_suggestions(prediction, kwargs)

        result = {
            'prediction': prediction,
            'probabilities': {class_names[i]: prob for i, prob in enumerate(probabilities[0])},
            'suggestions': suggestions
        }

        return result


def build_sample_input(feature_names):
    sample_values = {
        'temperature': 25.0,
        'power_consumption': 300.0,
        'user_activity': 'Active',
        'device_mode': 'Auto',
        'anomaly_flag': 0,
        'device_type': 'fridge',
        'internal_temp': 4.5,
        'external_temp': 23.0,
        'compressor_power': 115.0,
        'door_open_duration': 20.0,
        'humidity': 40.0,
        'fan_speed': 1500.0,
        'vibration_level': 1.0,
        'voltage': 230.0,
        'CPU_Usage (%)': 45.0,
        'Memory_Usage (%)': 50.0,
        'Battery_Level (%)': 75.0,
        'Network_Latency (ms)': 75.0,
        'Packet_Loss (%)': 0.5,
        'Temperature (°C)': 38.0,
        'Uptime (hrs)': 120.0,
        'Workload_Intensity': 2,
        'Error_Count': 1,
        'cpu_usage_pct': 35.0,
        'mem_usage_pct': 40.0,
        'temp_celsius': 42.0,
        'packet_loss_pct': 0.2,
        'latency_ms': 12.0,
        'throughput_mbps': 150.0,
        'voltage_v': 12.1,
        'uptime_hours': 300.0,
        'error_count_per_min': 0.0,
        'water_temp': 40.0,
        'drum_speed_rpm': 1200.0,
        'drain_time_sec': 100.0,
        'water_level_pct': 50.0,
        'power_consumption_watts': 1800.0,
        'door_lock_status': 1.0,
        'cycle_time_remaining': 25.0,
    }
    return {feature: sample_values.get(feature, 0) for feature in feature_names}

if __name__ == '__main__':
    # Example usage
    model_path = 'ml/device_fault_classifier_trained_cb.pkl'  # or 'ml/device_fault_classifier_weighted.pkl'

    if not Path(model_path).exists():
        print(f"Model file not found: {model_path}")
        print("Available models:")
        for f in Path('ml').glob('*.pkl'):
            print(f"  {f.as_posix()}")
        raise FileNotFoundError(model_path)

    predictor = DeviceFaultPredictor(model_path)

    sample_data = build_sample_input(predictor.feature_names)

    result = predictor.predict_single(**sample_data)
    print("Sample Prediction:")
    print(f"Predicted class: {result['prediction']}")
    print("Probabilities:")
    for cls, prob in result['probabilities'].items():
        print(f"  {cls}: {prob:.4f}")
    print(f"Suggestions: {result['suggestions']}")

    # Batch prediction example
    print("\nFor batch predictions, create a CSV file with columns:")
    print(",".join(predictor.feature_names))
    print("Then load it and call predictor.predict(df)")