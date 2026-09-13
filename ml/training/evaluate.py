"""
Evaluates a trained YOLO model on the processed VisDrone validation set,
and optionally compares it against the pretrained COCO baseline.

IMPORTANT CAVEAT (documented, not glossed over): yolo11n.pt is trained on
COCO's 80 classes. The VisDrone dataset.yaml defines 10 different classes.
Ultralytics' model.val() expects the checkpoint's class count to match the
dataset's class count, so a direct baseline-vs-trained mAP comparison on the
VisDrone validation set is only meaningful for the *trained* model. When
--compare is used, this script still attempts baseline validation, but if it
fails due to the class-count mismatch, the failure and its exact message are
recorded in the output JSON instead of fabricating numbers.

Usage:
    python ml/training/evaluate.py
    python ml/training/evaluate.py --model ml/models/sentinel_visdrone_best.pt
    python ml/training/evaluate.py --compare
    python ml/training/evaluate.py --test-video "D:\\Video_survillance\\uav0000086_00000_v.mp4"
"""
import argparse
import json
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO

from ml.utils import config
from ml.tracking.tracker import Tracker


def resolve_device(device_arg: str) -> str:
    if device_arg != "auto":
        return device_arg
    return "0" if torch.cuda.is_available() else "cpu"


def load_dataset_class_count(data_yaml_path: str) -> int:
    with open(data_yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return int(data.get("nc", len(data.get("names", []))))


def evaluate_model(model_path: str, data_path: str, device: str, imgsz: int, batch: int) -> dict:
    """
    Runs Ultralytics validation for a single model. Returns a dict with either
    real metrics, or an 'error' key describing exactly why evaluation failed
    (e.g. class-count mismatch). Never fabricates numbers.
    """
    result = {"model": model_path, "data": data_path}

    dataset_nc = load_dataset_class_count(data_path)
    result["dataset_num_classes"] = dataset_nc

    try:
        model = YOLO(model_path)
        model_nc = len(model.names)
        result["model_num_classes"] = model_nc

        if model_nc != dataset_nc:
            result["warning"] = (
                f"Model has {model_nc} classes but dataset defines {dataset_nc}. "
                f"Attempting validation anyway; if it fails, see 'error' below."
            )

        metrics = model.val(data=data_path, imgsz=imgsz, batch=batch, device=device, verbose=False)

        result["precision"] = float(metrics.box.mp)
        result["recall"] = float(metrics.box.mr)
        result["mAP50"] = float(metrics.box.map50)
        result["mAP50_95"] = float(metrics.box.map)

        speed = getattr(metrics, "speed", None)
        if speed:
            result["speed_ms_per_image"] = {k: float(v) for k, v in speed.items()}

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"

    return result


def save_results(result: dict, json_path: Path, txt_path: Path):
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    lines = [f"Model: {result.get('model')}", f"Data: {result.get('data')}"]
    if "error" in result:
        lines.append(f"ERROR: {result['error']}")
    else:
        lines += [
            f"Precision: {result.get('precision'):.4f}",
            f"Recall:    {result.get('recall'):.4f}",
            f"mAP50:     {result.get('mAP50'):.4f}",
            f"mAP50-95:  {result.get('mAP50_95'):.4f}",
        ]
        if "speed_ms_per_image" in result:
            lines.append(f"Speed (ms/img): {result['speed_ms_per_image']}")
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text("\n".join(lines), encoding="utf-8")


def run_test_video(model_path: str, video_path: str):
    print(f"\nRunning trained-model inference + BoT-SORT tracking on: {video_path}")
    out_path = config.OUTPUT_DETECTION_DIR / "trained_visdrone_demo.mp4"
    tracker = Tracker(model_path=model_path)
    n = 0
    for _, _, tracked in tracker.track_video(video_path, output_video_path=str(out_path)):
        n += len(tracked)
    print(f"Wrote annotated video with trained model to: {out_path} ({n} track-observations)")


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained YOLO model on VisDrone validation set")
    parser.add_argument("--model", default=str(config.TRAINED_MODEL_PATH))
    parser.add_argument("--data", default=str(config.VISDRONE_DATASET_YAML))
    parser.add_argument("--device", default="auto")
    parser.add_argument("--imgsz", type=int, default=config.TRAIN_IMGSZ_DEFAULT)
    parser.add_argument("--batch", type=int, default=config.TRAIN_BATCH_DEFAULT)
    parser.add_argument("--compare", action="store_true",
                         help="Also evaluate baseline yolo11n.pt and write baseline_vs_trained.json")
    parser.add_argument("--test-video", default=None,
                         help="Path to a video to run the trained model + BoT-SORT + save annotated output")
    args = parser.parse_args()

    device = resolve_device(args.device)

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"dataset.yaml not found at {data_path}. Run ml/training/prepare_visdrone.py first."
        )

    trained_model_path = Path(args.model)
    if not trained_model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found at {trained_model_path}. Run ml/training/train.py first, "
            f"or pass --model pointing at an existing checkpoint."
        )

    print("=" * 50)
    print("Evaluating trained model")
    print("=" * 50)
    trained_result = evaluate_model(str(trained_model_path), str(data_path), device, args.imgsz, args.batch)
    print(json.dumps(trained_result, indent=2))

    save_results(
        trained_result,
        config.EVAL_OUTPUT_DIR / "trained_model_metrics.json",
        config.EVAL_OUTPUT_DIR / "trained_model_metrics.txt",
    )
    print(f"\nSaved: {config.EVAL_OUTPUT_DIR / 'trained_model_metrics.json'}")
    print(f"Saved: {config.EVAL_OUTPUT_DIR / 'trained_model_metrics.txt'}")

    if args.compare:
        print("\n" + "=" * 50)
        print("Evaluating baseline (yolo11n.pt) for comparison")
        print("NOTE: baseline is COCO-pretrained (80 classes) vs this dataset's "
              f"{load_dataset_class_count(str(data_path))} classes - see caveat in file docstring.")
        print("=" * 50)
        baseline_result = evaluate_model("yolo11n.pt", str(data_path), device, args.imgsz, args.batch)
        print(json.dumps(baseline_result, indent=2))

        comparison = {"baseline": baseline_result, "trained": trained_result}
        comparison_path = config.EVAL_OUTPUT_DIR / "baseline_vs_trained.json"
        comparison_path.parent.mkdir(parents=True, exist_ok=True)
        with open(comparison_path, "w") as f:
            json.dump(comparison, f, indent=2)
        print(f"\nSaved: {comparison_path}")

    if args.test_video:
        run_test_video(str(trained_model_path), args.test_video)


if __name__ == "__main__":
    main()