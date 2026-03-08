import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from device_fault_classifier import DeviceFaultClassifier, load_and_inspect_csv, prepare_features

if __name__ == '__main__':
    # --- Execution Flow with Class Weights ---
    csv_path = 'ml/techare_training_data.csv'
    df = load_and_inspect_csv(csv_path)

    # 2. Preprocess
    X, y = prepare_features(df, target_col='decision_label')
    if y is None:
        raise ValueError('Target column `decision_label` not found in CSV.')

    # Validate that there are at least 2 classes and enough samples for stratified split
    if y.nunique() < 2:
        raise ValueError('Need at least two target classes to train.')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 3. Train with class weights to improve minority class detection
    # Calculate weights based on inverse class frequency
    class_counts = y_train.value_counts()
    total_samples = len(y_train)
    class_weights = {cls: total_samples / count for cls, count in class_counts.items()}

    print(f"Class weights: {class_weights}")

    classifier = DeviceFaultClassifier(class_weights=class_weights)
    metrics = classifier.train(X_train, y_train)

    # 4. Results
    print(f"Training Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"CV mean: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
    eval_results = classifier.evaluate(X_test, y_test)
    print("\nClassification Report:\n", eval_results['report'])
    print(f"\nTest Accuracy: {eval_results['accuracy']:.4f}")

    # 5. Save
    out_path = 'ml/device_fault_classifier_weighted.pkl'
    classifier.save(out_path)
    print(f"Saved weighted model to {out_path}")