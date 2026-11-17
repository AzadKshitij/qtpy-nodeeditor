"""Compare two rendered PNGs, with an optional per-channel tolerance."""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qtpy.QtGui import QImage  # noqa: E402


def load(path: str) -> QImage:
    image = QImage(path)
    if image.isNull():
        raise SystemExit("cannot read %s" % path)
    return image.convertToFormat(QImage.Format.Format_RGBA8888)


def compare(expected_path: str, actual_path: str, tolerance: int = 0) -> dict:
    expected = load(expected_path)
    actual = load(actual_path)
    if expected.size() != actual.size():
        return {
            "same_size": False,
            "changed_pixels": -1,
            "max_channel_delta": 255,
            "mean_channel_delta": 255.0,
        }

    left = expected.constBits()
    right = actual.constBits()
    left.setsize(expected.sizeInBytes())
    right.setsize(actual.sizeInBytes())
    left_bytes = bytes(left)
    right_bytes = bytes(right)

    if left_bytes == right_bytes:
        return {
            "same_size": True,
            "identical": True,
            "changed_pixels": 0,
            "max_channel_delta": 0,
            "mean_channel_delta": 0.0,
        }

    changed = 0
    maximum = 0
    total = 0
    for offset in range(0, len(left_bytes), 4):
        delta = max(
            abs(left_bytes[offset] - right_bytes[offset]),
            abs(left_bytes[offset + 1] - right_bytes[offset + 1]),
            abs(left_bytes[offset + 2] - right_bytes[offset + 2]),
        )
        total += delta
        maximum = max(maximum, delta)
        if delta > tolerance:
            changed += 1

    pixels = expected.width() * expected.height()
    return {
        "same_size": True,
        "identical": False,
        "changed_pixels": changed,
        "changed_percent": round(100.0 * changed / pixels, 4),
        "max_channel_delta": maximum,
        "mean_channel_delta": round(total / pixels, 4),
        "tolerance": tolerance,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected")
    parser.add_argument("actual")
    parser.add_argument("--tolerance", type=int, default=0)
    parser.add_argument("--max-changed-percent", type=float, default=0.0)
    args = parser.parse_args(argv)

    result = compare(args.expected, args.actual, args.tolerance)
    print(result)
    if not result.get("same_size"):
        return 2
    if result["changed_pixels"] < 0:
        return 2
    if result["changed_pixels"] > 0 and result.get("changed_percent", 0.0) > args.max_changed_percent:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
