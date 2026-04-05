from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

FAULT_LABEL_MAP = {
    0: 'Normal (no fault)',
    1: 'Battery fault',
    2: 'CPU fault',
    3: 'Network fault',
    4: 'Overheat fault',
    '0': 'Normal (no fault)',
    '1': 'Battery fault',
    '2': 'CPU fault',
    '3': 'Network fault',
    '4': 'Overheat fault',
}

FEATURE_SCHEMAS = {
    'device_fault_metrics': [
        'CPU_Usage (%)', 'Memory_Usage (%)', 'Battery_Level (%)',
        'Network_Latency (ms)', 'Packet_Loss (%)', 'Temperature (°C)',
        'Uptime (hrs)', 'Workload_Intensity', 'Error_Count',
    ],
    'smart_device_usage': [
        'temperature', 'power_consumption', 'user_activity', 'device_mode', 'anomaly_flag',
    ],
    'smart_fridge': [
        'internal_temp', 'external_temp', 'compressor_power', 'door_open_duration',
        'humidity', 'fan_speed', 'vibration_level', 'voltage',
    ],
    'multi_device': [
        'device_type',
        'internal_temp', 'external_temp', 'compressor_power', 'door_open_duration', 'humidity', 'fan_speed', 'vibration_level', 'voltage',
        'cpu_usage_pct', 'mem_usage_pct', 'temp_celsius', 'packet_loss_pct', 'latency_ms', 'throughput_mbps', 'voltage_v', 'uptime_hours', 'error_count_per_min',
        'water_temp', 'drum_speed_rpm', 'drain_time_sec', 'water_level_pct', 'power_consumption_watts', 'door_lock_status', 'cycle_time_remaining',
    ],
}

SPARSE_FEATURE_SCHEMAS = {'multi_device'}
OPTIONAL_FEATURE_SCHEMAS = {'multi_device'}
SCHEMA_REQUIRED_FEATURES = {
    'multi_device': ['device_type'],
}

COLUMN_ALIASES = {
    'internal_temperature': 'internal_temp',
    'outside_temp': 'external_temp',
    'ambient_temp': 'external_temp',
    'compressor_current': 'compressor_power',
    'compressor_load': 'compressor_power',
    'door_open_time': 'door_open_duration',
    'door_open_seconds': 'door_open_duration',
    'fan_rpm': 'fan_speed',
    'line_voltage': 'voltage',
}


@dataclass
class DatasetProfile:
    schema_name: str
    feature_names: list[str]
    target_column: str | None = None
    preserve_missing_numeric: bool = False
    allow_missing_features: bool = False


@dataclass
class DeviceFaultModelBundle:
    model: Any
    label_encoder: LabelEncoder
    categorical_encoders: dict[str, LabelEncoder]
    feature_names: list[str]
    target_names: list[str] | None = None
    numeric_fill_values: dict[str, float] | None = None
    schema_name: str | None = None
    preserve_missing_numeric: bool = False
    allow_missing_features: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            'model': self.model,
            'label_encoder': self.label_encoder,
            'categorical_encoders': self.categorical_encoders,
            'feature_names': self.feature_names,
            'target_names': self.target_names,
            'numeric_fill_values': self.numeric_fill_values or {},
            'schema_name': self.schema_name,
            'preserve_missing_numeric': self.preserve_missing_numeric,
            'allow_missing_features': self.allow_missing_features,
        }

    def save(self, filepath: str | Path) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.to_dict(), path)

    @classmethod
    def load(cls, filepath: str | Path) -> 'DeviceFaultModelBundle':
        model_data = joblib.load(filepath)
        return cls(
            model=model_data['model'],
            label_encoder=model_data['label_encoder'],
            categorical_encoders=model_data.get('categorical_encoders', {}),
            feature_names=model_data['feature_names'],
            target_names=model_data.get('target_names'),
            numeric_fill_values=model_data.get('numeric_fill_values', {}),
            schema_name=model_data.get('schema_name'),
            preserve_missing_numeric=model_data.get('preserve_missing_numeric', False),
            allow_missing_features=model_data.get('allow_missing_features', False),
        )


class DeviceFaultDataProcessor:
    """Reusable preprocessing utilities for training, evaluation, and inference."""

    def __init__(
        self,
        fault_label_map: dict[Any, str] | None = None,
        feature_schemas: dict[str, list[str]] | None = None,
        column_aliases: dict[str, str] | None = None,
    ):
        self.fault_label_map = fault_label_map or FAULT_LABEL_MAP
        self.feature_schemas = feature_schemas or FEATURE_SCHEMAS
        self.column_aliases = column_aliases or COLUMN_ALIASES

    def get_schema_options(self, schema_name: str) -> dict[str, bool]:
        return {
            'preserve_missing_numeric': schema_name in SPARSE_FEATURE_SCHEMAS,
            'allow_missing_features': schema_name in OPTIONAL_FEATURE_SCHEMAS,
        }

    def get_required_schema_features(self, schema_name: str) -> list[str]:
        return SCHEMA_REQUIRED_FEATURES.get(schema_name, [])

    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {}
        for col in df.columns:
            rename_map[col] = col.strip().replace('\ufeff', '').replace('Â°', '°')
        return df.rename(columns=rename_map)

    def apply_column_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        existing_lookup = {col.lower(): col for col in df.columns}
        rename_map = {}

        for alias, canonical in self.column_aliases.items():
            existing_column = existing_lookup.get(alias.lower())
            if existing_column and canonical not in df.columns:
                rename_map[existing_column] = canonical

        return df.rename(columns=rename_map) if rename_map else df

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.apply_column_aliases(self.normalize_column_names(df.copy()))

    def infer_target_column(self, df: pd.DataFrame, preferred: str | None = None) -> str:
        candidates = []
        if preferred:
            candidates.append(preferred)
        candidates.extend(['Failure_Type', 'decision_label', 'Label', 'label', 'target', 'fault_label', 'fault_type'])

        for col in candidates:
            if col in df.columns:
                return col
        raise ValueError(f'Could not find target column in dataset. Tried: {candidates}')

    def resolve_target_names(self, label_classes: list[Any] | np.ndarray) -> list[str]:
        return [self.fault_label_map.get(cls, str(cls)) for cls in label_classes]

    def resolve_feature_schema(self, df: pd.DataFrame, preferred: str | None = None) -> tuple[str, list[str]]:
        available_columns = set(df.columns)
        ordered_schemas: list[tuple[str, list[str]]] = []

        if preferred and preferred in self.feature_schemas:
            required_features = self.get_required_schema_features(preferred)
            if preferred in OPTIONAL_FEATURE_SCHEMAS and all(feature in available_columns for feature in required_features):
                return preferred, self.feature_schemas[preferred]
            ordered_schemas.append((preferred, self.feature_schemas[preferred]))

        ordered_schemas.extend(
            (name, features) for name, features in self.feature_schemas.items() if name != preferred
        )

        for schema_name, feature_names in ordered_schemas:
            if all(feature in available_columns for feature in feature_names):
                return schema_name, feature_names

        overlap_summary = {
            schema_name: len([feature for feature in feature_names if feature in available_columns])
            for schema_name, feature_names in self.feature_schemas.items()
        }
        raise ValueError(
            'No compatible feature schema found in dataframe. '
            f'Available columns: {list(df.columns)}. '
            f'Schema overlap: {overlap_summary}'
        )

    def coerce_feature_columns(
        self,
        df: pd.DataFrame,
        feature_names: list[str],
        preserve_missing_numeric: bool = False,
    ) -> pd.DataFrame:
        normalized = df.copy()

        for col in feature_names:
            if col not in normalized.columns:
                normalized[col] = np.nan

            series = normalized[col]
            converted = pd.to_numeric(series, errors='coerce')
            non_null_count = int(series.notna().sum())

            if pd.api.types.is_numeric_dtype(series) or (non_null_count > 0 and int(converted.notna().sum()) == non_null_count):
                if preserve_missing_numeric:
                    normalized[col] = converted.astype(float)
                else:
                    fill_value = converted.median()
                    if pd.isna(fill_value):
                        fill_value = 0.0
                    normalized[col] = converted.fillna(fill_value)
            else:
                normalized[col] = series.fillna('Unknown').astype(str)

        return normalized

    def load_csv(self, csv_path: str | Path, inspect: bool = True) -> pd.DataFrame:
        df = pd.read_csv(csv_path)
        df = self.normalize_dataframe(df)

        if inspect:
            print(f'Loaded {csv_path}: {df.shape[0]} rows')
            try:
                target_col = self.infer_target_column(df)
                print(f'Detected target column: {target_col}')
                print('\nLabel distribution:\n', df[target_col].value_counts())
            except ValueError:
                pass

        return df

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        target_col: str = 'Failure_Type',
        feature_schema: str | None = None,
    ) -> tuple[pd.DataFrame, pd.Series | None, DatasetProfile]:
        normalized = self.normalize_dataframe(df)
        schema_name, feature_names = self.resolve_feature_schema(normalized, preferred=feature_schema)
        schema_options = self.get_schema_options(schema_name)
        normalized = self.coerce_feature_columns(
            normalized,
            feature_names,
            preserve_missing_numeric=schema_options['preserve_missing_numeric'],
        )
        resolved_target = self.infer_target_column(normalized, preferred=target_col) if target_col else self.infer_target_column(normalized)

        X = normalized[feature_names].copy()
        y = normalized[resolved_target] if resolved_target in normalized.columns else None
        return X, y, DatasetProfile(
            schema_name=schema_name,
            feature_names=feature_names,
            target_column=resolved_target,
            preserve_missing_numeric=schema_options['preserve_missing_numeric'],
            allow_missing_features=schema_options['allow_missing_features'],
        )

    def prepare_inference_frame(
        self,
        data: pd.DataFrame | dict[str, Any],
        feature_names: list[str],
        categorical_encoders: dict[str, LabelEncoder] | None = None,
        numeric_fill_values: dict[str, float] | None = None,
        preserve_missing_numeric: bool = False,
        allow_missing_features: bool = False,
    ) -> pd.DataFrame:
        if isinstance(data, dict):
            data = pd.DataFrame([data])

        normalized = self.normalize_dataframe(data)
        missing_features = [feature for feature in feature_names if feature not in normalized.columns]
        if allow_missing_features and missing_features:
            required_features = {'device_type'} if 'device_type' in feature_names else set()
            missing_required = [feature for feature in missing_features if feature in required_features]
            if missing_required:
                raise ValueError(
                    f'Missing required features for this model: {missing_required}. '
                    f'Expected features: {feature_names}'
                )
            for feature in missing_features:
                normalized[feature] = np.nan
            missing_features = []

        if missing_features:
            raise ValueError(
                f'Missing required features for this model: {missing_features}. '
                f'Expected features: {feature_names}'
            )

        X = normalized[feature_names].copy()
        categorical_encoders = categorical_encoders or {}
        numeric_fill_values = numeric_fill_values or {}

        for col in X.columns:
            if col in categorical_encoders:
                encoder = categorical_encoders[col]
                values = X[col].fillna('Unknown').astype(str)
                unseen_values = sorted(set(values) - set(encoder.classes_))
                if unseen_values:
                    raise ValueError(
                        f'Unsupported categorical value(s) for `{col}`: {unseen_values}. '
                        f'Allowed values: {list(encoder.classes_)}'
                    )
                X[col] = encoder.transform(values)
            else:
                X[col] = pd.to_numeric(X[col], errors='coerce')
                if preserve_missing_numeric:
                    X[col] = X[col].astype(float)
                else:
                    fill_value = numeric_fill_values.get(col, X[col].median())
                    if pd.isna(fill_value):
                        fill_value = 0.0
                    X[col] = X[col].fillna(fill_value)

        return X


DEFAULT_DATA_PROCESSOR = DeviceFaultDataProcessor()


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    return DEFAULT_DATA_PROCESSOR.normalize_column_names(df)


def apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    return DEFAULT_DATA_PROCESSOR.apply_column_aliases(df)


def infer_target_column(df: pd.DataFrame, preferred: str | None = None) -> str:
    return DEFAULT_DATA_PROCESSOR.infer_target_column(df, preferred=preferred)


def resolve_target_names(label_classes: list[Any] | np.ndarray) -> list[str]:
    return DEFAULT_DATA_PROCESSOR.resolve_target_names(label_classes)


def resolve_feature_schema(df: pd.DataFrame, preferred: str | None = None) -> tuple[str, list[str]]:
    return DEFAULT_DATA_PROCESSOR.resolve_feature_schema(df, preferred=preferred)


def coerce_feature_columns(df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
    return DEFAULT_DATA_PROCESSOR.coerce_feature_columns(df, feature_names)


def load_and_inspect_csv(csv_path: str | Path) -> pd.DataFrame:
    return DEFAULT_DATA_PROCESSOR.load_csv(csv_path, inspect=True)


def prepare_features(
    df: pd.DataFrame,
    target_col: str = 'Failure_Type',
    feature_schema: str | None = None,
) -> tuple[pd.DataFrame, pd.Series | None]:
    X, y, _ = DEFAULT_DATA_PROCESSOR.prepare_training_data(df, target_col=target_col, feature_schema=feature_schema)
    return X, y


class DeviceFaultClassifier:
    """Model wrapper responsible for encoding, training, evaluation, and persistence."""

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        use_gpu: bool = False,
        class_weights: dict[str, float] | None = None,
        estimator_factory: Callable[[], Any] | None = None,
        data_processor: DeviceFaultDataProcessor | None = None,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.use_gpu = use_gpu
        self.class_weights = class_weights
        self.data_processor = data_processor or DEFAULT_DATA_PROCESSOR
        self.estimator_factory = estimator_factory or self._default_estimator_factory

        self.model = self._create_estimator()
        self.label_encoder = LabelEncoder()
        self.categorical_encoders: dict[str, LabelEncoder] = {}
        self.feature_names: list[str] | None = None
        self.target_names: list[str] | None = None
        self.numeric_fill_values: dict[str, float] = {}
        self.dataset_profile: DatasetProfile | None = None

    def _default_estimator_factory(self) -> XGBClassifier:
        return XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            verbosity=0,
            eval_metric='mlogloss',
        )

    def _create_estimator(self) -> Any:
        return self.estimator_factory()

    def _encode_categoricals(self, X: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        encoded = X.copy()
        categorical_columns = [
            col
            for col in encoded.columns
            if pd.api.types.is_object_dtype(encoded[col])
            or pd.api.types.is_string_dtype(encoded[col])
            or isinstance(encoded[col].dtype, pd.CategoricalDtype)
        ]

        for col in categorical_columns:
            if fit:
                encoder = LabelEncoder()
                encoded[col] = encoder.fit_transform(encoded[col].astype(str))
                self.categorical_encoders[col] = encoder
            else:
                encoder = self.categorical_encoders.get(col)
                if encoder is None:
                    raise ValueError(f'Missing categorical encoder for column `{col}`.')

                values = encoded[col].astype(str)
                unseen_values = sorted(set(values) - set(encoder.classes_))
                if unseen_values:
                    raise ValueError(
                        f'Unsupported categorical value(s) for `{col}`: {unseen_values}. '
                        f'Allowed values: {list(encoder.classes_)}'
                    )
                encoded[col] = encoder.transform(values)

        return encoded

    def _build_sample_weights(self, y_train: pd.Series, y_encoded: np.ndarray) -> np.ndarray | None:
        if not self.class_weights:
            return None

        sample_weight = np.ones(len(y_train))
        classes = list(self.label_encoder.classes_)
        for class_name, weight in self.class_weights.items():
            if class_name in classes:
                class_idx = classes.index(class_name)
                sample_weight[y_encoded == class_idx] = weight
        return sample_weight

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        cv_splits: int = 5,
        dataset_profile: DatasetProfile | None = None,
    ) -> dict[str, float]:
        self.dataset_profile = dataset_profile
        self.feature_names = X_train.columns.tolist()
        if dataset_profile and dataset_profile.preserve_missing_numeric:
            self.numeric_fill_values = {}
        else:
            self.numeric_fill_values = {
                col: float(X_train[col].median())
                for col in self.feature_names
                if pd.api.types.is_numeric_dtype(X_train[col])
            }

        X_train_encoded = self._encode_categoricals(X_train, fit=True)
        y_encoded = self.label_encoder.fit_transform(y_train)
        self.target_names = self.data_processor.resolve_target_names(self.label_encoder.classes_)
        self.model = self._create_estimator()

        sample_weight = self._build_sample_weights(y_train, y_encoded)
        self.model.fit(X_train_encoded, y_encoded, sample_weight=sample_weight)

        min_class_count = int(pd.Series(y_train).value_counts().min())
        effective_cv_splits = min(cv_splits, min_class_count)
        if effective_cv_splits < 2:
            raise ValueError('Need at least two samples in each class for cross-validation.')

        skf = StratifiedKFold(n_splits=effective_cv_splits, shuffle=True, random_state=42)
        cv_scores: list[float] = []
        for train_idx, val_idx in skf.split(X_train_encoded, y_encoded):
            X_tr, X_val = X_train_encoded.iloc[train_idx], X_train_encoded.iloc[val_idx]
            y_tr, y_val = y_encoded[train_idx], y_encoded[val_idx]

            model_cv = self._create_estimator()
            weights_cv = sample_weight[train_idx] if sample_weight is not None else None
            model_cv.fit(X_tr, y_tr, sample_weight=weights_cv)
            predictions = model_cv.predict(X_val)
            cv_scores.append(float(accuracy_score(y_val, predictions)))

        train_accuracy = accuracy_score(y_encoded, self.model.predict(X_train_encoded))
        return {
            'train_accuracy': float(train_accuracy),
            'cv_mean': float(np.mean(cv_scores)),
            'cv_std': float(np.std(cv_scores)),
        }

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
        X_test_encoded = self._encode_categoricals(X_test, fit=False)
        y_test_encoded = self.label_encoder.transform(y_test)
        predictions = self.model.predict(X_test_encoded)

        return {
            'accuracy': float(accuracy_score(y_test_encoded, predictions)),
            'report': classification_report(y_test_encoded, predictions, target_names=self.target_names),
            'confusion_matrix': confusion_matrix(y_test_encoded, predictions),
        }

    def build_model_bundle(self) -> DeviceFaultModelBundle:
        return DeviceFaultModelBundle(
            model=self.model,
            label_encoder=self.label_encoder,
            categorical_encoders=self.categorical_encoders,
            feature_names=self.feature_names or [],
            target_names=self.target_names,
            numeric_fill_values=self.numeric_fill_values,
            schema_name=self.dataset_profile.schema_name if self.dataset_profile else None,
            preserve_missing_numeric=self.dataset_profile.preserve_missing_numeric if self.dataset_profile else False,
            allow_missing_features=self.dataset_profile.allow_missing_features if self.dataset_profile else False,
        )

    def save(self, filepath: str | Path) -> None:
        self.build_model_bundle().save(filepath)


class SavedModelEvaluator:
    """Evaluates saved model bundles against external datasets."""

    def __init__(self, data_processor: DeviceFaultDataProcessor | None = None):
        self.data_processor = data_processor or DEFAULT_DATA_PROCESSOR

    def evaluate(self, model_path: str | Path, eval_csv_path: str | Path, target_col: str = 'decision_label') -> dict[str, Any]:
        print('\n=== FINAL EVALUATION ON SEPARATE EVALUATION DATASET ===')
        bundle = DeviceFaultModelBundle.load(model_path)

        eval_df = self.data_processor.load_csv(eval_csv_path, inspect=False)
        print(f'Loaded evaluation dataset: {eval_csv_path} ({eval_df.shape[0]} rows)')

        resolved_target_col = self.data_processor.infer_target_column(eval_df, preferred=target_col)
        if resolved_target_col != target_col:
            print(f'Using detected target column: {resolved_target_col}')

        X_eval = self.data_processor.prepare_inference_frame(
            eval_df,
            feature_names=bundle.feature_names,
            categorical_encoders=bundle.categorical_encoders,
            numeric_fill_values=bundle.numeric_fill_values,
            preserve_missing_numeric=bundle.preserve_missing_numeric,
            allow_missing_features=bundle.allow_missing_features,
        )
        y_eval = eval_df[resolved_target_col]
        y_eval_encoded = bundle.label_encoder.transform(y_eval)
        y_pred = bundle.model.predict(X_eval)

        target_names = bundle.target_names or self.data_processor.resolve_target_names(bundle.label_encoder.classes_)
        eval_accuracy = accuracy_score(y_eval_encoded, y_pred)
        eval_report = classification_report(y_eval_encoded, y_pred, target_names=target_names)
        eval_cm = confusion_matrix(y_eval_encoded, y_pred)

        print(f'\nEvaluation Accuracy: {eval_accuracy:.4f}')
        print('\nEvaluation Classification Report:\n', eval_report)
        print('\nEvaluation Confusion Matrix:\n', eval_cm)

        return {
            'accuracy': float(eval_accuracy),
            'report': eval_report,
            'confusion_matrix': eval_cm,
        }


class DeviceFaultTrainingPipeline:
    """Coordinates data loading, training, persistence, and optional external evaluation."""

    def __init__(
        self,
        data_processor: DeviceFaultDataProcessor | None = None,
        classifier_factory: Callable[[], DeviceFaultClassifier] | None = None,
        evaluator: SavedModelEvaluator | None = None,
    ):
        self.data_processor = data_processor or DEFAULT_DATA_PROCESSOR
        self.classifier_factory = classifier_factory or (lambda: DeviceFaultClassifier(data_processor=self.data_processor))
        self.evaluator = evaluator or SavedModelEvaluator(data_processor=self.data_processor)

    def load_training_data(self, csv_path: str | Path) -> pd.DataFrame:
        return self.data_processor.load_csv(csv_path, inspect=True)

    def train_from_dataframe(
        self,
        df: pd.DataFrame,
        train_target: str,
        test_size: float,
        cv_splits: int,
        model_out: str | Path | None = None,
        feature_schema: str | None = None,
    ) -> dict[str, Any]:
        X, y, profile = self.data_processor.prepare_training_data(
            df,
            target_col=train_target,
            feature_schema=feature_schema,
        )
        if y is None:
            raise ValueError(f'Target column `{train_target}` not found in CSV.')
        if y.nunique() < 2:
            raise ValueError('Need at least two target classes to train.')

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=42,
            stratify=y,
        )

        classifier = self.classifier_factory()
        metrics = classifier.train(X_train, y_train, cv_splits=cv_splits, dataset_profile=profile)
        evaluation = classifier.evaluate(X_test, y_test)

        if model_out:
            classifier.save(model_out)

        return {
            'classifier': classifier,
            'metrics': metrics,
            'evaluation': evaluation,
            'profile': profile,
        }

    def evaluate_external_candidates(self, model_path: str | Path, evaluation_candidates: list[str], target_col: str) -> None:
        existing_candidates = [candidate for candidate in evaluation_candidates if Path(candidate).exists()]

        if not existing_candidates:
            print(
                '\nSkipped final external evaluation: no evaluation dataset found. '
                f'Checked: {evaluation_candidates}'
            )
            return

        evaluated = False
        for evaluation_csv_path in existing_candidates:
            try:
                self.evaluator.evaluate(model_path, evaluation_csv_path, target_col=target_col)
                evaluated = True
                break
            except ValueError as exc:
                print(f'\nSkipping evaluation dataset {evaluation_csv_path}: {exc}')

        if not evaluated:
            print(
                '\nSkipped final external evaluation: no compatible evaluation dataset found. '
                f'Checked: {existing_candidates}'
            )

    def run(self, args: argparse.Namespace) -> dict[str, Any]:
        df = self.load_training_data(args.train_csv)
        results = self.train_from_dataframe(
            df,
            train_target=args.train_target,
            test_size=args.test_size,
            cv_splits=args.cv_splits,
            model_out=args.model_out,
            feature_schema=args.feature_schema,
        )

        metrics = results['metrics']
        evaluation = results['evaluation']
        print(f"Training Accuracy: {metrics['train_accuracy']:.4f}")
        print(f"CV mean: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
        print('\nInternal Test Classification Report:\n', evaluation['report'])
        print(f"\nInternal Test Accuracy: {evaluation['accuracy']:.4f}")
        print('\nInternal Test Confusion Matrix:\n', evaluation['confusion_matrix'])
        print(f'\nSaved trained model to {args.model_out}')

        evaluation_candidates = [args.eval_csv] if args.eval_csv else [
            str(Path.home() / 'Downloads' / 'evaluation_dataset.csv'),
            'ml/techare_evaluation_data.csv',
        ]
        self.evaluate_external_candidates(args.model_out, evaluation_candidates, target_col=args.eval_target)
        return results


def evaluate_saved_model(model_path: str | Path, eval_csv_path: str | Path, target_col: str = 'decision_label') -> dict[str, Any]:
    evaluator = SavedModelEvaluator()
    return evaluator.evaluate(model_path, eval_csv_path, target_col=target_col)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train and evaluate Device Fault Classifier.')
    parser.add_argument('--train-csv', default='ml/train_dataset.csv', help='Path to training CSV file.')
    parser.add_argument('--train-target', default='Failure_Type', help='Target column in training CSV.')
    parser.add_argument('--eval-csv', default=None, help='Optional path to evaluation CSV file.')
    parser.add_argument('--eval-target', default='Failure_Type', help='Preferred target column in evaluation CSV.')
    parser.add_argument('--model-out', default='ml/device_fault_classifier_trained_xgb.pkl', help='Output path for trained model.')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test split ratio for internal validation.')
    parser.add_argument('--cv-splits', type=int, default=5, help='Number of CV folds during training.')
    parser.add_argument('--feature-schema', default=None, help='Optional feature schema override for training data.')
    return parser.parse_args()


def run_training_and_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    pipeline = DeviceFaultTrainingPipeline()
    return pipeline.run(args)


if __name__ == '__main__':
    cli_args = parse_args()
    run_training_and_evaluation(cli_args)