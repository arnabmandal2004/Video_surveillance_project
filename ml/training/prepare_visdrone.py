"""
Converts VisDrone2019-VID (video) ground-truth annotations into YOLO-format
detection labels, without ever modifying data/raw/.

VisDrone-VID annotation format (one .txt per sequence, in annotations/,
filename matches the sequence folder name):

    <frame_index>,<target_id>,<bbox_left>,<bbox_top>,<bbox_width>,<bbox_height>,
    <score>,<object_category>,<truncation>,<occlusion>

- frame_index is 1-indexed, matching frame image filenames like 0000001.jpg
- score == 0 means "ignore this box in evaluation" -> excluded from training labels
- object_category 0 (ignored-regions) and 11 (others) are excluded per the
  official VisDrone toolkit convention (see ml/utils/config.py for the mapping)

Because converting the FULL training set (many sequences x hundreds of frames
each) is expensive, this script supports frame-sampling for a fast pilot run,
and can also process everything with --full.

Usage examples:
    # Fast pilot: 5 sequences, every 30th frame
    python ml/training/prepare_visdrone.py --pilot

    # Custom sampling
    python ml/training/prepare_visdrone.py --frame-stride 10 --limit-sequences 20

    # Full dataset (all sequences, every frame) - slow, run only once time allows
    python ml/training/prepare_visdrone.py --full
"""
import argparse
import csv
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import yaml

from ml.utils import config


def _find_frame_path(seq_dir: Path, frame_index: int) -> Optional[Path]:
    """VisDrone frames are typically 7-digit zero-padded, 1-indexed .jpg files."""
    candidate = seq_dir / f"{frame_index:07d}.jpg"
    if candidate.exists():
        return candidate
    # Fallback: sorted directory listing indexed by frame_index (1-indexed)
    frames = sorted(seq_dir.glob("*.jpg"))
    if 1 <= frame_index <= len(frames):
        return frames[frame_index - 1]
    return None


def _parse_annotation_file(ann_path: Path) -> Dict[int, List[dict]]:
    """
    Returns {frame_index: [ {bbox_left, bbox_top, bbox_width, bbox_height,
                              category, score}, ... ] }
    Excludes ignored-regions/others categories and score==0 boxes.
    """
    frames: Dict[int, List[dict]] = {}
    with open(ann_path, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 8:
                continue
            frame_index = int(row[0])
            bbox_left = float(row[2])
            bbox_top = float(row[3])
            bbox_width = float(row[4])
            bbox_height = float(row[5])
            score = int(row[6])
            category = int(row[7])

            if score == 0:
                continue
            if category in config.VISDRONE_EXCLUDED_CATEGORY_IDS:
                continue
            if category not in config.VISDRONE_CATEGORY_ID_TO_YOLO_ID:
                continue
            if bbox_width <= 0 or bbox_height <= 0:
                continue

            frames.setdefault(frame_index, []).append({
                "bbox_left": bbox_left,
                "bbox_top": bbox_top,
                "bbox_width": bbox_width,
                "bbox_height": bbox_height,
                "category": category,
            })
    return frames


def _write_yolo_label(label_path: Path, boxes: List[dict], img_w: int, img_h: int):
    lines = []
    for b in boxes:
        yolo_id = config.VISDRONE_CATEGORY_ID_TO_YOLO_ID[b["category"]]
        x_center = (b["bbox_left"] + b["bbox_width"] / 2.0) / img_w
        y_center = (b["bbox_top"] + b["bbox_height"] / 2.0) / img_h
        w_norm = b["bbox_width"] / img_w
        h_norm = b["bbox_height"] / img_h
        # Clamp to [0, 1] in case of annotation edge-cases at frame borders
        x_center = min(max(x_center, 0.0), 1.0)
        y_center = min(max(y_center, 0.0), 1.0)
        w_norm = min(max(w_norm, 0.0), 1.0)
        h_norm = min(max(h_norm, 0.0), 1.0)
        lines.append(f"{yolo_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
    label_path.write_text("\n".join(lines), encoding="utf-8")


def process_split(
    sequences_dir: Path,
    annotations_dir: Path,
    out_images_dir: Path,
    out_labels_dir: Path,
    frame_stride: int,
    limit_sequences: Optional[int],
    max_images: Optional[int],
) -> int:
    out_images_dir.mkdir(parents=True, exist_ok=True)
    out_labels_dir.mkdir(parents=True, exist_ok=True)

    if not sequences_dir.exists():
        raise FileNotFoundError(f"Sequences dir not found: {sequences_dir}")
    if not annotations_dir.exists():
        raise FileNotFoundError(f"Annotations dir not found: {annotations_dir}")

    sequence_dirs = sorted([d for d in sequences_dir.iterdir() if d.is_dir()])
    if limit_sequences:
        sequence_dirs = sequence_dirs[:limit_sequences]

    written = 0
    for seq_dir in sequence_dirs:
        ann_path = annotations_dir / f"{seq_dir.name}.txt"
        if not ann_path.exists():
            print(f"  [skip] no annotation file for sequence: {seq_dir.name}")
            continue

        frame_annotations = _parse_annotation_file(ann_path)

        for frame_index in sorted(frame_annotations.keys()):
            if frame_stride > 1 and (frame_index - 1) % frame_stride != 0:
                continue

            boxes = frame_annotations[frame_index]
            if not boxes:
                continue

            frame_path = _find_frame_path(seq_dir, frame_index)
            if frame_path is None:
                continue

            img = cv2.imread(str(frame_path))
            if img is None:
                continue
            img_h, img_w = img.shape[:2]

            out_name = f"{seq_dir.name}_{frame_index:07d}"
            out_image_path = out_images_dir / f"{out_name}.jpg"
            out_label_path = out_labels_dir / f"{out_name}.txt"

            # Copy (never move) the raw frame into the processed dataset
            shutil.copy2(frame_path, out_image_path)
            _write_yolo_label(out_label_path, boxes, img_w, img_h)

            written += 1
            if max_images and written >= max_images:
                print(f"  Reached max_images={max_images}, stopping this split.")
                return written

        print(f"  [{seq_dir.name}] processed")

    return written


def write_dataset_yaml():
    data = {
        "path": str(config.PROCESSED_VISDRONE_DIR),
        "train": str(Path("images") / "train"),
        "val": str(Path("images") / "val"),
        "nc": len(config.YOLO_CLASS_NAMES),
        "names": config.YOLO_CLASS_NAMES,
    }
    with open(config.VISDRONE_DATASET_YAML, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print(f"Wrote dataset.yaml -> {config.VISDRONE_DATASET_YAML}")


def main():
    parser = argparse.ArgumentParser(description="Convert VisDrone-VID annotations to YOLO format")
    parser.add_argument("--frame-stride", type=int, default=10,
                         help="Use every Nth annotated frame per sequence (default: 10)")
    parser.add_argument("--limit-sequences", type=int, default=None,
                         help="Limit number of sequences per split (pilot use)")
    parser.add_argument("--max-images", type=int, default=None,
                         help="Hard cap on images written per split")
    parser.add_argument("--pilot", action="store_true",
                         help="Shortcut: --frame-stride 30 --limit-sequences 5 --max-images 300")
    parser.add_argument("--full", action="store_true",
                         help="Process the complete dataset (--frame-stride 1, no limits)")
    args = parser.parse_args()

    if args.pilot:
        frame_stride, limit_sequences, max_images = 30, 5, 300
    elif args.full:
        frame_stride, limit_sequences, max_images = 1, None, None
    else:
        frame_stride = args.frame_stride
        limit_sequences = args.limit_sequences
        max_images = args.max_images

    print("=" * 50)
    print("VisDrone-VID -> YOLO dataset preparation")
    print("=" * 50)
    print(f"frame_stride={frame_stride} limit_sequences={limit_sequences} max_images={max_images}")
    print(f"Classes ({len(config.YOLO_CLASS_NAMES)}): {config.YOLO_CLASS_NAMES}")

    print("\n[Train split]")
    n_train = process_split(
        config.VID_TRAIN_SEQUENCES_DIR, config.VID_TRAIN_ANNOTATIONS_DIR,
        config.PROCESSED_VISDRONE_IMAGES_TRAIN, config.PROCESSED_VISDRONE_LABELS_TRAIN,
        frame_stride, limit_sequences, max_images,
    )

    print("\n[Val split]")
    n_val = process_split(
        config.VID_VAL_SEQUENCES_DIR, config.VID_VAL_ANNOTATIONS_DIR,
        config.PROCESSED_VISDRONE_IMAGES_VAL, config.PROCESSED_VISDRONE_LABELS_VAL,
        frame_stride, limit_sequences, max_images,
    )

    write_dataset_yaml()

    print("\nDone.")
    print(f"Train images written: {n_train}")
    print(f"Val images written:   {n_val}")
    print(f"Processed dataset root: {config.PROCESSED_VISDRONE_DIR}")
    if n_train == 0 or n_val == 0:
        print("\nWARNING: one of the splits has 0 images. Check dataset paths/annotations before training.")


if __name__ == "__main__":
    main()