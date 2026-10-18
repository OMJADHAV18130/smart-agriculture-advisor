"""
Dataset loader for the crop reference table.

Loads backend/data/cleaned_crop_recommendation.csv (2,200 rows of real
agricultural readings: N, P, K, temperature, humidity, ph, rainfall, label)
and computes per-crop TYPICAL RANGES (10th-90th percentile).

IMPORTANT: this module performs NO machine learning. It only aggregates the
CSV into simple descriptive ranges, which are used to:

  1. produce symbolic facts such as ("temperature_vs_crop", "above") that
     feed the IF-THEN rules in knowledge_base.py, and
  2. show a "dataset reference" panel in the UI.

All reasoning still happens in the rule engine - the dataset only supplies
descriptive statistics, so the project stays a rule-based expert system.

Crops that are not present in the CSV (e.g. Wheat, Tomato, Other) fall back
to ranges computed across ALL crops in the file, clearly flagged as such.

Only the Python standard library is used (csv / statistics-free math).
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

from .config import settings
from .engine import Fact

DATA_FILE = settings.DATA_FILE_PATH
NUMERIC_COLUMNS = ("N", "P", "K", "temperature", "humidity", "ph", "rainfall")

# Human-friendly units used when describing a deviation to the user.
UNITS = {"temperature": "°C", "humidity": "%", "ph": ""}

METRIC_LABELS = {
    "N": "Nitrogen (N)",
    "P": "Phosphorus (P)",
    "K": "Potassium (K)",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "ph": "Soil pH",
    "rainfall": "Rainfall",
}

# English + Marathi display names for every crop in the CSV.
# (label in CSV) -> (English name, Marathi name)
CROP_NAMES: Dict[str, tuple] = {
    "apple": ("Apple", "सफरचंद"),
    "banana": ("Banana", "केळी"),
    "blackgram": ("Black Gram", "उडीद"),
    "chickpea": ("Chickpea", "चणा"),
    "coconut": ("Coconut", "नारळ"),
    "coffee": ("Coffee", "कॉफी"),
    "cotton": ("Cotton", "कापूस"),
    "grapes": ("Grapes", "द्राक्ष"),
    "jute": ("Jute", "पाट"),
    "kidneybeans": ("Kidney Beans", "राजमा"),
    "lentil": ("Lentil", "मसरू"),
    "maize": ("Maize", "मक्का"),
    "mango": ("Mango", "आंबा"),
    "mothbeans": ("Moth Beans", "मृगची"),
    "mungbean": ("Mung Bean", "मूग"),
    "muskmelon": ("Muskmelon", "खरबूज"),
    "orange": ("Orange", "संत्री"),
    "papaya": ("Papaya", "पपई"),
    "pigeonpeas": ("Pigeon Pea", "तूर"),
    "pomegranate": ("Pomegranate", "डाळिंब"),
    "rice": ("Rice", "तांदूळ"),
    "watermelon": ("Watermelon", "टरबूज"),
}


def crop_display_name(label: str) -> tuple:
    """(English, Marathi) names for a dataset crop label, with fallbacks."""
    return CROP_NAMES.get(label, (label.title(), label))

_cache: Optional[dict] = None


def _percentile(sorted_values: List[float], p: float) -> float:
    """Simple linear-interpolation percentile of an already-sorted list."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def _stats(values: List[float]) -> dict:
    ordered = sorted(values)
    return {
        "min": round(ordered[0], 2),
        "max": round(ordered[-1], 2),
        "p10": round(_percentile(ordered, 10), 2),
        "p90": round(_percentile(ordered, 90), 2),
    }


def _load() -> dict:
    """Read the CSV once and cache the per-crop ranges (thread-safe enough
    for a demo: worst case the file is read twice)."""
    global _cache
    if _cache is not None:
        return _cache

    if not DATA_FILE.exists():
        _cache = {"loaded": False, "file": DATA_FILE.name, "total_rows": 0,
                  "crops": {}, "all_crops": {"rows": 0, "ranges": {}}}
        return _cache

    columns: Dict[str, List[float]] = {c: [] for c in NUMERIC_COLUMNS}
    by_crop: Dict[str, Dict[str, List[float]]] = {}
    total = 0

    with DATA_FILE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = (row.get("label") or "").strip().lower()
            if not label:
                continue
            total += 1
            by_crop.setdefault(label, {c: [] for c in NUMERIC_COLUMNS})
            for col in NUMERIC_COLUMNS:
                try:
                    value = float(row[col])
                except (KeyError, TypeError, ValueError):
                    continue
                columns[col].append(value)
                by_crop[label][col].append(value)

    crops = {}
    for label, cols in by_crop.items():
        crops[label] = {
            "rows": len(next(iter(cols.values()))),
            "ranges": {c: _stats(v) for c, v in cols.items() if v},
        }

    _cache = {
        "loaded": True,
        "file": DATA_FILE.name,
        "total_rows": total,
        "crops": crops,
        "all_crops": {"rows": total, "ranges": {c: _stats(v) for c, v in columns.items() if v}},
    }
    return _cache


def dataset_info() -> dict:
    """Small summary used by GET /health."""
    data = _load()
    return {
        "loaded": data["loaded"],
        "file": data["file"],
        "rows": data["total_rows"],
        "crops": len(data["crops"]),
    }


def crop_labels() -> List[str]:
    """Sorted crop labels actually present in the CSV (empty if it failed
    to load). Used to validate the API's crop input."""
    return sorted(_load()["crops"].keys())


def crops_payload() -> dict:
    """Payload for GET /crops: every crop with English/Marathi names and
    its typical ranges."""
    data = _load()
    crops = []
    for label, info in sorted(data["crops"].items()):
        name_en, name_mr = crop_display_name(label)
        crops.append({
            "label": label,
            "name_en": name_en,
            "name_mr": name_mr,
            "rows": info["rows"],
            "ranges": info["ranges"],
        })
    return {
        "dataset": dataset_info(),
        "threshold_note": (
            "Typical ranges are the 10th-90th percentile of the CSV - "
            "descriptive statistics, not a trained model."
        ),
        "crops": crops,
    }


def reference_for(crop_label: str) -> dict:
    """Ranges for a crop, falling back to all-crop ranges when the CSV has
    no rows for that crop (e.g. Wheat, Tomato, Other)."""
    data = _load()
    if not data["loaded"]:
        return {"source": "unavailable", "rows": 0, "ranges": {}}
    key = (crop_label or "").strip().lower()
    if key in data["crops"]:
        info = data["crops"][key]
        return {"source": "crop", "rows": info["rows"], "ranges": info["ranges"]}
    return {"source": "all_crops", "rows": data["all_crops"]["rows"],
            "ranges": data["all_crops"]["ranges"]}


def compare(crop_label: str, temperature: float, humidity: float, ph: float) -> dict:
    """Compare field readings against the dataset reference for the crop.

    Returns symbolic facts for the rule engine plus human-readable
    deviation strings and the raw ranges for the UI.
    """
    ref = reference_for(crop_label)
    source_flag = {"crop": "crop_specific", "all_crops": "all_crops",
                   "unavailable": "unavailable"}[ref["source"]]

    if not ref["ranges"]:
        return {
            "facts": [("crop_ref_data", "unavailable"), ("crop_ref", "unknown"),
                      ("ph_ref", "unknown")],
            "deviations": [],
            "source": ref["source"],
            "rows_for_crop": ref["rows"],
            "ranges": {},
        }

    values = {"temperature": temperature, "humidity": humidity, "ph": ph}
    facts: List[Fact] = [("crop_ref_data", source_flag)]
    deviations: List[str] = []
    inside_all = True

    for metric, value in values.items():
        rng = ref["ranges"][metric]
        if value > rng["p90"]:
            band = "above"
        elif value < rng["p10"]:
            band = "below"
        else:
            band = "typical"
        facts.append((f"{metric}_vs_crop", band))
        if band != "typical":
            inside_all = False
            unit = UNITS.get(metric, "")
            deviations.append(
                f"{METRIC_LABELS[metric]} {value:g}{unit} is {band} the typical "
                f"{rng['p10']:g}-{rng['p90']:g}{unit} range for {crop_label}"
            )

    ph_rng = ref["ranges"]["ph"]
    ph_outside = ph < ph_rng["p10"] or ph > ph_rng["p90"]

    facts.append(("crop_ref", "inside" if inside_all else "outside"))
    facts.append(("ph_ref", "outside" if ph_outside else "inside"))

    return {
        "facts": facts,
        "deviations": deviations,
        "source": ref["source"],
        "rows_for_crop": ref["rows"] if ref["source"] == "crop" else 0,
        "ranges": ref["ranges"],
    }
