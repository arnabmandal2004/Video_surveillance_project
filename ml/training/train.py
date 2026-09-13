"""
Trains YOLO11n on the processed VisDrone YOLO dataset (produced by
prepare_visdrone.py). Does not touch the existing detection/tracking/event
pipeline; only produces a new weights file that detector.py/tracker.py can
optionally be pointed at via --model_path / config.MODEL_PATH.

Usage:
    python ml/training/train.py --epochs 5          # fast pilot
    python ml/training/train.py --epochs 20          # longer run later
"""
import argparse
import shutil
from pathlib import Path

import torch
from ultralytics import YOLO

from ml.utils import config


def resolve_device(device_arg: str) -> str:
    if device_arg != "auto":
        return device_arg
    return "0" if torch.cuda.is_available() else "cpu"


def main():
    parser = argparse.ArgumentParser(description="Train YOLO11n on VisDrone (processed YOLO dataset)")
    parser.add_argument("--data", default=str(config.VISDRONE_DATASET_YAML))
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--epochs", type=int, default=config.TRAIN_EPOCHS_DEFAULT)
    parser.add_argument("--imgsz", type=int, default=config.TRAIN_IMGSZ_DEFAULT)
    parser.add_argument("--batch", type=int, default=config.TRAIN_BATCH_DEFAULT)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--workers", type=int, default=config.TRAIN_WORKERS_DEFAULT)
    parser.add_argument("--project", default=str(config.TRAINING_RUNS_DIR))
    parser.add_argument("--name", default="visdrone_yolo11n")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"dataset.yaml not found at {data_path}. "
            f"Run ml/training/prepare_visdrone.py first."
        )

    device = resolve_device(args.device)

    print("=" * 50)
    print("SentinelAI - YOLO11n training on VisDrone")
    print("=" * 50)
    print(f"Data:    {data_path}")
    print(f"Model:   {args.model}")
    print(f"Epochs:  {args.epochs}")
    print(f"Imgsz:   {args.imgsz}")
    print(f"Batch:   {args.batch}")
    print(f"Device:  {device}  (CUDA available: {torch.cuda.is_available()})")
    print(f"Workers: {args.workers}")
    print(f"Project: {args.project}")
    print(f"Name:    {args.name}")
    print()

    # This will auto-download the pretrained checkpoint if `args.model` is a
    # bare name like "yolo11n.pt" and it isn't already cached locally.
    model = YOLO(args.model)

    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        exist_ok=True,
    )

    save_dir = Path(model.trainer.save_dir)
    best_path = save_dir / "weights" / "best.pt"

    if not best_path.exists():
        print(f"\nWARNING: expected best.pt not found at {best_path}. "
              f"Check the training run directory manually.")
        return

    config.TRAINED_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_path, config.TRAINED_MODEL_PATH)

    print("\nTraining complete.")
    print(f"Run directory:  {save_dir}")
    print(f"Best weights:   {best_path}")
    print(f"Copied to:      {config.TRAINED_MODEL_PATH}")
    print("(Original yolo11n.pt was not modified.)")


if __name__ == "__main__":
    main()