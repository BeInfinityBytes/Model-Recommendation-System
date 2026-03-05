"""
Generate range and unique value analysis for all model parameters.

This script:
- Connects to the Model Data MongoDB (scraped HuggingFace models)
- Computes min/max for numeric fields
- Computes unique-values + count for categorical fields
- Writes results to range_analysis.json
"""

import json
from pymongo import MongoClient
import os
import sys
# --------------------------------------------
# FIX: Ensure "src" is importable
# --------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from src.shared.config.settings import settings  # Load .env settings


# -----------------------------
# PARAMETERS TO ANALYZE
# -----------------------------
TARGET_FIELDS = [
    "tasks",
    "parameter_bucket",
    "parameter_count",
    "context_window_bucket",
    "context_window",
    "base_architecture_type",
    "knowledge_cutoff",
    "tool_usage",
    "language_support",
    "reasoning_level_bucket",
    "code_proficiency_bucket",
    "math_proficiency_bucket",
    "general_knowledge_bucket",
    "primary_focus",
    "domain_expertise",
    "content_generation",
    "language_count",
    "license",
    "inference_provider",
]


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def flatten_value(value):
    """Return a list regardless of string/list/null."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def update_range(stats, value):
    """Update min/max for numeric fields."""
    if isinstance(value, (int, float)):
        stats["min"] = value if stats["min"] is None else min(
            stats["min"], value)
        stats["max"] = value if stats["max"] is None else max(
            stats["max"], value)


def update_uniques(unique_set, value):
    """Collect unique string values."""
    for item in flatten_value(value):
        if item not in (None, ""):
            unique_set.add(str(item))


# -----------------------------
# MAIN PROCESS
# -----------------------------
def generate_range_report():
    """Generate range/unique-value summary for all model parameters."""

    client = MongoClient(settings.MODEL_DATA_MONGO_URI)
    db = client[settings.MODEL_DATA_DB]
    collection = db[settings.MODEL_DATA_COLLECTION]

    documents = list(collection.find({}))
    output = {}

    for field in TARGET_FIELDS:
        # Detect type using the first non-null field value
        sample_value = next(
            (doc[field]
             for doc in documents if field in doc and doc[field] is not None),
            None,
        )

        # Case: field missing everywhere
        if sample_value is None:
            output[field] = {"type": "Limited",
                             "unique_values": [], "count": 0}
            continue

        # -------------------------
        # Range Field (int/float)
        # -------------------------
        if isinstance(sample_value, (int, float)):
            stats = {"type": "Range", "min": None, "max": None}

            for doc in documents:
                if field in doc:
                    update_range(stats, doc[field])

            output[field] = stats
            continue

        # -------------------------
        # Limited Field (list/string)
        # -------------------------
        unique_values = set()

        for doc in documents:
            if field in doc:
                update_uniques(unique_values, doc[field])

        output[field] = {
            "type": "Limited",
            "unique_values": sorted(unique_values),
            "count": len(unique_values),
        }

    return output


# -----------------------------
# WRITE OUTPUT JSON
# -----------------------------
if __name__ == "__main__":
    report = generate_range_report()

    with open("range_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("range_analysis.json generated successfully!")
