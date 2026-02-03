"""
Device Fault Classification Model
Classifies device issues for AI-guided repair workflows

This classifier predicts device fault categories to enable:
- Intelligent diagnostics recommendations
- Guided repair flow routing
- Device onboarding issue detection
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
from pathlib import Path


class DeviceFaultClassifier:
    """Multi-class classifier for device fault diagnosis"""
    
    def __init__(self, model_path=None):
        """
        Initialize the classifier
        
        Args:
            model_path: Path to load pre-trained model. If None, creates new model.
        """
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.model_path = model_path
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._initialize_new_model()
    
    def _initialize_new_model(self):
        """Initialize a new Random Forest classifier"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
    
    def train(self, X_train, y_train, validation_split=0.2):
        """
        Train the classifier on labeled data
        
        Args:
            X_train: Training features (DataFrame or array)
            y_train: Training labels (Series or array)
            validation_split: Fraction of data to use for validation
        
        Returns:
            dict: Training metrics including accuracy and cross-validation scores
        """
        # Store feature names if DataFrame provided
        if isinstance(X_train, pd.DataFrame):
            self.feature_names = X_train.columns.tolist()
            X_train = X_train.values
        
        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train model
        self.model.fit(X_train_scaled, y_train_encoded)
        
        # Calculate metrics
        train_pred = self.model.predict(X_train_scaled)
        train_accuracy = accuracy_score(y_train_encoded, train_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train_encoded, cv=5
        )
        
        metrics = {
            'train_accuracy': train_accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'cv_scores': cv_scores
        }
        
        return metrics
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate classifier on test data
        
        Args:
            X_test: Test features
            y_test: Test labels
        
        Returns:
            dict: Classification metrics and detailed report
        """
        if self.model is None:
            raise ValueError("Model must be trained first")
        
        if isinstance(X_test, pd.DataFrame):
            X_test = X_test.values
        
        X_test_scaled = self.scaler.transform(X_test)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        predictions = self.model.predict(X_test_scaled)
        
        accuracy = accuracy_score(y_test_encoded, predictions)
        
        report = {
            'accuracy': accuracy,
            'classification_report': classification_report(
                y_test_encoded, predictions, 
                target_names=self.label_encoder.classes_
            ),
            'confusion_matrix': confusion_matrix(y_test_encoded, predictions),
            'predictions': self.label_encoder.inverse_transform(predictions)
        }
        
        return report
    
    def predict(self, X):
        """
        Make predictions on new data
        
        Args:
            X: Features (DataFrame or array)
        
        Returns:
            array: Predicted fault categories
        """
        if self.model is None:
            raise ValueError("Model must be trained first")
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return self.label_encoder.inverse_transform(predictions)
    
    def predict_proba(self, X):
        """
        Get prediction probabilities for each fault class
        
        Args:
            X: Features (DataFrame or array)
        
        Returns:
            DataFrame: Probabilities for each class
        """
        if self.model is None:
            raise ValueError("Model must be trained first")
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        X_scaled = self.scaler.transform(X)
        probas = self.model.predict_proba(X_scaled)
        
        return pd.DataFrame(
            probas,
            columns=self.label_encoder.classes_
        )
    
    def get_feature_importance(self):
        """
        Get feature importance scores
        
        Returns:
            DataFrame: Features ranked by importance
        """
        if self.model is None:
            raise ValueError("Model must be trained first")
        
        if self.feature_names is None:
            feature_names = [f"feature_{i}" for i in range(self.model.n_features_in_)]
        else:
            feature_names = self.feature_names
        
        importances = self.model.feature_importances_
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_model(self, filepath):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_names
        }
        
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load pre-trained model from disk"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.feature_names = model_data['feature_names']
        
        print(f"Model loaded from {filepath}")


def create_sample_data():
    """Create sample device fault data for demonstration"""
    np.random.seed(42)
    
    n_samples = 500
    
    # Create synthetic device metrics
    data = {
        'battery_health': np.random.uniform(20, 100, n_samples),
        'thermal_temp': np.random.uniform(25, 85, n_samples),
        'memory_usage': np.random.uniform(30, 95, n_samples),
        'cpu_load': np.random.uniform(10, 100, n_samples),
        'signal_strength': np.random.uniform(-120, -30, n_samples),
        'error_count': np.random.poisson(5, n_samples),
        'uptime_hours': np.random.uniform(1, 1000, n_samples),
    }
    
    X = pd.DataFrame(data)
    
    # Create labels based on feature patterns
    y = []
    for idx in range(len(X)):
        if X.iloc[idx]['battery_health'] < 30:
            y.append('battery_fault')
        elif X.iloc[idx]['thermal_temp'] > 75:
            y.append('thermal_issue')
        elif X.iloc[idx]['memory_usage'] > 90:
            y.append('memory_fault')
        elif X.iloc[idx]['error_count'] > 10:
            y.append('software_error')
        else:
            y.append('healthy')
    
    return X, pd.Series(y)


if __name__ == "__main__":
    print("Device Fault Classifier - Demo\n")
    
    # Create sample data
    print("Generating sample device data...")
    X, y = create_sample_data()
    print(f"Data shape: {X.shape}")
    print(f"Fault classes: {y.unique()}\n")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train classifier
    print("Training classifier...")
    classifier = DeviceFaultClassifier()
    metrics = classifier.train(X_train, y_train)
    
    print(f"Training Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"Cross-Val Mean: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})\n")
    
    # Evaluate
    print("Evaluating on test set...")
    eval_metrics = classifier.evaluate(X_test, y_test)
    print(f"Test Accuracy: {eval_metrics['accuracy']:.4f}\n")
    print("Classification Report:")
    print(eval_metrics['classification_report'])
    
    # Feature importance
    print("\nTop Features:")
    importance = classifier.get_feature_importance()
    print(importance.head())
    
    # Save model
    model_dir = Path(__file__).parent / "models"
    classifier.save_model(str(model_dir / "device_fault_classifier.pkl"))
