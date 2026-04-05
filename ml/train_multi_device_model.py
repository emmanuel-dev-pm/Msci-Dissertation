from argparse import Namespace
from pathlib import Path

from device_fault_classifier import run_training_and_evaluation


def resolve_multi_device_dataset_path() -> str:
    candidates = [
        Path('ml/multi_device_train_realistic_v2.csv'),
        Path.home() / 'Downloads' / 'multi_device_train_realistic_v2 (1).csv',
        Path.home() / 'Downloads' / 'multi_device_train_realistic_v2.csv',
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        'Could not find the multi-device training dataset. Place it in `ml/` '
        'or keep it in your Downloads folder.'
    )


if __name__ == '__main__':
    args = Namespace(
        train_csv=resolve_multi_device_dataset_path(),
        train_target='fault_label',
        eval_csv=None,
        eval_target='fault_label',
        model_out='ml/models/multi_device_fault_classifier.pkl',
        test_size=0.2,
        cv_splits=5,
        feature_schema='multi_device',
    )
    run_training_and_evaluation(args)