import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, LabelBinarizer
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier

def load_and_inspect_csv(csv_path):
    """Load CSV and print a short summary of labels."""
    df = pd.read_csv(csv_path)
    print(f"Loaded {csv_path}: {df.shape[0]} rows")
    if 'Label' in df.columns:
        print("\nLabel distribution:\n", df['Label'].value_counts())
    return df

def prepare_features(df, target_col='decision_label'):
    """Prepare features and label series from dataframe.

    - Select only the expected features that actually exist in `df`.
    - Numeric columns are coerced to numeric and imputed with median.
    - Categorical/object columns are left as-is (CatBoost can handle them).
    """
    df = df.copy()

    # Expected features from techare_training_data.csv
    features = [
        'temperature', 'power_consumption', 'user_activity', 
        'device_mode', 'anomaly_flag'
    ]

    existing_features = [c for c in features if c in df.columns]
    if not existing_features:
        raise ValueError(f"None of the expected features found in dataframe. Expected one of: {features}")

    # Coerce numeric-like columns to numeric and impute missing values with median
    for col in existing_features:
        if not pd.api.types.is_object_dtype(df[col]) and not isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())

    X = df[existing_features].copy()
    y = df[target_col] if target_col in df.columns else None
    return X, y

class DeviceFaultClassifier:
    """Classifier using XGBoost for device fault diagnosis."""

    def __init__(self, n_estimators=200, max_depth=6, learning_rate=0.1, use_gpu=False, class_weights=None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.use_gpu = use_gpu
        self.class_weights = class_weights  # dict like {'Normal': 1, 'Warning': 2, 'Critical': 3}

        self.model = XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            verbosity=0,
            eval_metric='mlogloss'
        )
        self.label_encoder = LabelEncoder()
        self.categorical_encoders = {}  # Store encoders for categorical features
        self.feature_names = None

    def _encode_categoricals(self, X, fit=False):
        """Encode categorical columns to numeric for XGBoost."""
        X = X.copy()
        cat_cols = [c for c in X.columns if pd.api.types.is_object_dtype(X[c])]
        
        for col in cat_cols:
            if fit:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.categorical_encoders[col] = le
            else:
                le = self.categorical_encoders.get(col)
                if le:
                    X[col] = le.transform(X[col].astype(str))
        return X

    def train(self, X_train, y_train, cv_splits=5):
        self.feature_names = X_train.columns.tolist()
        
        # Encode categorical features
        X_train_encoded = self._encode_categoricals(X_train, fit=True)
        y_encoded = self.label_encoder.fit_transform(y_train)

        # Calculate sample weights if class_weights provided
        sample_weight = None
        if self.class_weights:
            sample_weight = np.ones(len(y_train))
            for class_name, weight in self.class_weights.items():
                if class_name in self.label_encoder.classes_:
                    class_idx = list(self.label_encoder.classes_).index(class_name)
                    mask = y_encoded == class_idx
                    sample_weight[mask] = weight
        
        # Fit final model
        self.model.fit(X_train_encoded, y_encoded, sample_weight=sample_weight)
        
        # Manual cross-validation
        skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=42)
        cv_scores = []
        for train_idx, val_idx in skf.split(X_train_encoded, y_encoded):
            X_tr, X_val = X_train_encoded.iloc[train_idx], X_train_encoded.iloc[val_idx]
            y_tr, y_val = y_encoded[train_idx], y_encoded[val_idx]
            
            model_cv = XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=42,
                verbosity=0,
                eval_metric='mlogloss'
            )
            
            # Apply weights to CV fold
            sw_cv = None
            if sample_weight is not None:
                sw_cv = sample_weight[train_idx]
            
            model_cv.fit(X_tr, y_tr, sample_weight=sw_cv)
            preds = model_cv.predict(X_val)
            cv_scores.append(accuracy_score(y_val, preds))
        
        train_acc = accuracy_score(y_encoded, self.model.predict(X_train_encoded))
        
        return {
            'train_accuracy': train_acc,
            'cv_mean': float(np.mean(cv_scores)),
            'cv_std': float(np.std(cv_scores))
        }

    def evaluate(self, X_test, y_test):
        X_test_encoded = self._encode_categoricals(X_test, fit=False)
        y_test_encoded = self.label_encoder.transform(y_test)
        predictions = self.model.predict(X_test_encoded)

        return {
            'accuracy': accuracy_score(y_test_encoded, predictions),
            'report': classification_report(y_test_encoded, predictions, target_names=self.label_encoder.classes_)
        }

    def save(self, filepath):
        model_data = {
            'model': self.model,
            'label_encoder': self.label_encoder,
            'categorical_encoders': self.categorical_encoders,
            'feature_names': self.feature_names
        }
        joblib.dump(model_data, filepath)

if __name__ == '__main__':
    # --- Execution Flow ---
    csv_path = 'ml/techare_training_data.csv'
    df = load_and_inspect_csv(csv_path)

    # 2. Preprocess
    X, y = prepare_features(df, target_col='decision_label')
    if y is None:
        raise ValueError('Target column `decision_label` not found in CSV. Please provide a dataset with a `decision_label` column.')

    # Validate that there are at least 2 classes and enough samples for stratified split
    if y.nunique() < 2:
        raise ValueError('Need at least two target classes to train.')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 3. Train using CatBoost
    classifier = DeviceFaultClassifier()
    metrics = classifier.train(X_train, y_train)

    # 4. Results
    print(f"Training Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"CV mean: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
    eval_results = classifier.evaluate(X_test, y_test)
    print("\nClassification Report:\n", eval_results['report'])
    print(f"\nTest Accuracy: {eval_results['accuracy']:.4f}")

    # 5. Save
    out_path = 'ml/device_fault_classifier_trained_cb.pkl'
    classifier.save(out_path)
    print(f"Saved trained model to {out_path}")