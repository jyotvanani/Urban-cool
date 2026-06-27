"""Evaluate the trained heat-risk model with sample predictions.

Run from the backend/ directory:
    python ml/evaluate_model.py

Loads model.joblib (+ scaler) and prints predictions for sample zones. If the
model is missing, prints a readable message instead of crashing.
"""

import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

ML_DIR = BASE_DIR / "ml"
MODEL_PATH = ML_DIR / "model.joblib"
SCALER_PATH = ML_DIR / "scaler.joblib"

FEATURE_ORDER = [
    "lst_temperature",
    "ndvi",
    "ndbi",
    "ndwi",
    "built_up_density",
    "green_cover_percentage",
    "water_body_distance_km",
    "air_temperature",
    "humidity",
    "wind_speed",
]

SAMPLES = [
    {
        "label": "Dense severe zone",
        "lst_temperature": 44.0, "ndvi": 0.12, "ndbi": 0.78, "ndwi": 0.06,
        "built_up_density": 0.88, "green_cover_percentage": 8,
        "water_body_distance_km": 4.0, "air_temperature": 40.0,
        "humidity": 35, "wind_speed": 5.5,
    },
    {
        "label": "Balanced moderate zone",
        "lst_temperature": 38.0, "ndvi": 0.34, "ndbi": 0.52, "ndwi": 0.22,
        "built_up_density": 0.6, "green_cover_percentage": 27,
        "water_body_distance_km": 1.0, "air_temperature": 36.0,
        "humidity": 48, "wind_speed": 9.0,
    },
    {
        "label": "Green low-risk zone",
        "lst_temperature": 34.5, "ndvi": 0.49, "ndbi": 0.39, "ndwi": 0.31,
        "built_up_density": 0.44, "green_cover_percentage": 41,
        "water_body_distance_km": 0.7, "air_temperature": 33.5,
        "humidity": 60, "wind_speed": 11.5,
    },
]


def categorize(score: float) -> str:
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Moderate"
    if score <= 80:
        return "High"
    return "Severe"


def main() -> None:
    if not MODEL_PATH.exists():
        print("Model file not found at", MODEL_PATH)
        print("Run 'python ml/train_model.py' first to create it.")
        print("The backend will still work using the rule-based fallback.")
        return

    try:
        import joblib

        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH) if SCALER_PATH.exists() else None
        print("Model loaded successfully from", MODEL_PATH)
    except Exception as exc:
        print("Failed to load model:", exc)
        return

    print("\nSample predictions:")
    for sample in SAMPLES:
        features = np.array([[sample[name] for name in FEATURE_ORDER]], dtype=float)
        if scaler is not None:
            features = scaler.transform(features)
        score = float(np.clip(model.predict(features)[0], 0, 100))
        print(f"  {sample['label']:<24} -> score {score:6.2f}  ({categorize(score)})")

    print("\nModel evaluation complete. Model is working.")


if __name__ == "__main__":
    main()
