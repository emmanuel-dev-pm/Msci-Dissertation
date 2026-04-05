from argparse import Namespace
from pathlib import Path

from device_fault_classifier import run_training_and_evaluation


def resolve_fridge_dataset_path():
    candidates = [
        Path('ml/fridge_train_data_realistic.csv'),
        Path.home() / 'Downloads' / 'fridge_train_data_realistic.csv'
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        'Could not find fridge dataset. Place `fridge_train_data_realistic.csv` in `ml/` '
        'or keep it in your Downloads folder.'
    )


if __name__ == '__main__':
    args = Namespace(
        train_csv=resolve_fridge_dataset_path(),
        train_target='Label',
        eval_csv=None,
        eval_target='Label',
        model_out='ml/models/smart_fridge_fault_classifier.pkl',
        test_size=0.2,
        cv_splits=5
    )
    run_training_and_evaluation(args)