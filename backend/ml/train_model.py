"""Train a RandomForest heat-risk regression model on synthetic data.

Run from the backend/ directory:
    python ml/train_model.py

Generates synthetic, physically-plausible samples, trains a
RandomForestRegressor with a StandardScaler, and saves the artifacts plus a
training sample CSV. The backend works even without these files thanks to the
rule-based fallback, but training improves prediction quality.
"""

import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

ML_DIR = BASE_DIR / "ml"
DATA_DIR = BASE_DIR / "app" / "data"
MODEL_PATH = ML_DIR / "model.joblib"
SCALER_PATH = ML_DIR / "scaler.joblib"
SAMPLE_CSV = DATA_DIR / "model_training_sample.csv"

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


def _clamp(value, low, high):
    return np.maximum(low, np.minimum(high, value))


def synthetic_score(row: dict) -> float:
    """Weighted rule-based score (0-100).

    LST 30% | Vegetation 20% | Built-up 20% | Water 10% | Weather 15% | Wind 5%.
    """
    lst_c = _clamp((row["lst_temperature"] - 28) / 20, 0, 1)
    veg_c = _clamp(
        0.5 * _clamp((0.6 - row["ndvi"]) / 0.6, 0, 1)
        + 0.5 * _clamp((25 - row["green_cover_percentage"]) / 25, 0, 1),
        0, 1,
    )
    built_c = _clamp(0.5 * _clamp(row["ndbi"], 0, 1) + 0.5 * _clamp(row["built_up_density"], 0, 1), 0, 1)
    water_c = _clamp(
        0.5 * _clamp((0.15 - row["ndwi"]) / 0.15, 0, 1)
        + 0.5 * _clamp(row["water_body_distance_km"] / 5.0, 0, 1),
        0, 1,
    )
    weather_c = _clamp((row["air_temperature"] - 28) / 17, 0, 1)
    wind_c = _clamp((12 - row["wind_speed"]) / 12, 0, 1)

    weighted = (
        0.30 * lst_c + 0.20 * veg_c + 0.20 * built_c
        + 0.10 * water_c + 0.15 * weather_c + 0.05 * wind_c
    )
    return float(_clamp(weighted * 100, 0, 100))


def generate_data(n_samples: int = 2000, seed: int = 42):
    """Generate synthetic feature rows and target scores."""
    rng = np.random.default_rng(seed)
    rows, targets = [], []
    for _ in range(n_samples):
        row = {
            "lst_temperature": rng.uniform(28, 48),
            "ndvi": rng.uniform(0.05, 0.7),
            "ndbi": rng.uniform(0.2, 0.9),
            "ndwi": rng.uniform(0.0, 0.4),
            "built_up_density": rng.uniform(0.2, 0.95),
            "green_cover_percentage": rng.uniform(3, 55),
            "water_body_distance_km": rng.uniform(0.2, 5.0),
            "air_temperature": rng.uniform(28, 45),
            "humidity": rng.uniform(25, 70),
            "wind_speed": rng.uniform(2, 14),
        }
        score = synthetic_score(row)
        score = float(_clamp(score + rng.normal(0, 3), 0, 100))  # small noise
        rows.append([row[name] for name in FEATURE_ORDER])
        targets.append(score)
    return np.array(rows, dtype=float), np.array(targets, dtype=float)


def main() -> None:
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    print("Generating synthetic training data...")
    X, y = generate_data()

    # Save a training sample CSV for inspection / reproducibility.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(X, columns=FEATURE_ORDER)
    df["heat_risk_score"] = np.round(y, 2)
    df.to_csv(SAMPLE_CSV, index=False)
    print(f"Saved training sample -> {SAMPLE_CSV} ({len(df)} rows)")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print("Training RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=200, max_depth=14, random_state=42, n_jobs=-1)
    model.fit(X_train_s, y_train)

    preds = model.predict(X_test_s)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    ML_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print("Model training successful.")
    print(f"  MAE: {mae:.2f} | R2: {r2:.3f}")
    print(f"  Saved model  -> {MODEL_PATH}")
    print(f"  Saved scaler -> {SCALER_PATH}")


if __name__ == "__main__":
    main()
