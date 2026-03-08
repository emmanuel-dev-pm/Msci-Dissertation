import pandas as pd
import joblib
import sys
import os

class DeviceFaultPredictor:
    """Load trained model and make predictions on new data."""

    def __init__(self, model_path):
        self.model_path = model_path
        self.load_model()

    def load_model(self):
        """Load the trained model and encoders."""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.categorical_encoders = model_data.get('categorical_encoders', {})
            self.feature_names = model_data['feature_names']
            print(f"Loaded model from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)

    def preprocess_input(self, data):
        """Preprocess input data for prediction."""
        # Convert to DataFrame if dict
        if isinstance(data, dict):
            data = pd.DataFrame([data])

        # Select expected features
        expected_features = ['temperature', 'power_consumption', 'user_activity', 'device_mode', 'anomaly_flag']
        available_features = [f for f in expected_features if f in data.columns]

        if not available_features:
            raise ValueError(f"No expected features found. Expected: {expected_features}")

        X = data[available_features].copy()

        # Convert numeric columns to float
        for col in ['temperature', 'power_consumption', 'anomaly_flag']:
            if col in X.columns:
                X[col] = pd.to_numeric(X[col], errors='coerce')

        # Encode categorical features - use simple mapping since encoders weren't saved
        user_activity_map = {'Sleep': 0, 'Idle': 1, 'Active': 2}
        device_mode_map = {'Standby': 0, 'Manual': 1, 'Auto': 2}

        if 'user_activity' in X.columns:
            X['user_activity'] = X['user_activity'].map(user_activity_map).fillna(0).astype(int)
        if 'device_mode' in X.columns:
            X['device_mode'] = X['device_mode'].map(device_mode_map).fillna(0).astype(int)

        return X

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

        result = {
            'prediction': predictions[0],
            'probabilities': {class_names[i]: prob for i, prob in enumerate(probabilities[0])}
        }

        return result

if __name__ == '__main__':
    # Example usage
    model_path = 'ml/device_fault_classifier_trained_cb.pkl'  # or 'ml/device_fault_classifier_weighted.pkl'

    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        print("Available models:")
        for f in os.listdir('ml'):
            if f.endswith('.pkl'):
                print(f"  ml/{f}")
        sys.exit(1)

    predictor = DeviceFaultPredictor(model_path)

    # Example prediction
    sample_data = {
        'temperature': 25.0,
        'power_consumption': 300.0,
        'user_activity': 'Active',
        'device_mode': 'Auto',
        'anomaly_flag': 0
    }

    result = predictor.predict_single(**sample_data)
    print("Sample Prediction:")
    print(f"Predicted class: {result['prediction']}")
    print("Probabilities:")
    for cls, prob in result['probabilities'].items():
        print(f"  {cls}: {prob:.4f}")

    # Batch prediction example
    print("\nFor batch predictions, create a CSV file with columns:")
    print("temperature,power_consumption,user_activity,device_mode,anomaly_flag")
    print("Then load it and call predictor.predict(df)")