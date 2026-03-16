from pathlib import Path

import numpy as np
import pandas as pd
import pytest


DATASET_PATH = Path(__file__).resolve().parents[1] / "Datasets" / "car_rental_cleaned_dataset.csv"


def transform_df(df):
    required_defaults = {
        "Reservation_ID": "",
        "Customer_ID": "",
        "Vehicle_ID": "",
        "Vehicle_Class": "Unknown",
        "Booking_Status": "Unknown",
        "Booking_TS": pd.NaT,
        "Pickup_TS": pd.NaT,
        "Return_TS": pd.NaT,
        "Odo_Start": np.nan,
        "Odo_End": np.nan,
        "Fuel_Level": np.nan,
        "Rate": np.nan,
        "Promo_Code": "",
        "City": "Unknown",
        "GPS_Lat": np.nan,
        "GPS_Lon": np.nan,
        "Speed": np.nan,
        "Damage_Flag": "None",
        "Notes": "",
        "Vehicle_ID_Invalid": False,
        "Duration_Hours": np.nan,
        "Distance_Driven": np.nan,
        "Refuel_Event": "",
        "Driver_Behavior": "Unknown",
        "Total_Amount": np.nan,
    }

    out = df.copy()

    for col, default in required_defaults.items():
        if col not in out.columns:
            out[col] = default

    for col in ["Booking_TS", "Pickup_TS", "Return_TS", "Prev_Return", "Promo_Expiry"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")

    for col in [
        "Duration_Hours",
        "Distance_Driven",
        "Odo_Start",
        "Odo_End",
        "Rate",
        "Total_Amount",
        "Fuel_Level",
        "Speed",
        "GPS_Lat",
        "GPS_Lon",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    bool_values = out["Vehicle_ID_Invalid"].astype(str).str.lower().str.strip()
    out["vehicle_id_invalid_flag"] = bool_values.isin(["true", "1", "yes"])

    out["is_completed"] = out["Booking_Status"].eq("Completed")
    out["rental_hours"] = out["Duration_Hours"]
    mask_missing_hours = out["rental_hours"].isna() & out["Pickup_TS"].notna() & out["Return_TS"].notna()
    out.loc[mask_missing_hours, "rental_hours"] = (
        (out.loc[mask_missing_hours, "Return_TS"] - out.loc[mask_missing_hours, "Pickup_TS"]).dt.total_seconds() / 3600
    )
    out["rental_hours"] = out["rental_hours"].clip(lower=0)

    out["distance_km"] = out["Distance_Driven"].clip(lower=0)
    out["lead_time_hours"] = ((out["Pickup_TS"] - out["Booking_TS"]).dt.total_seconds() / 3600).clip(lower=0)
    out["booking_month"] = out["Booking_TS"].dt.to_period("M").astype(str)
    out["pickup_date"] = out["Pickup_TS"].dt.date

    return out


@pytest.fixture(scope="module")
def source_df():
    assert DATASET_PATH.exists(), f"Dataset not found: {DATASET_PATH}"
    df = pd.read_csv(DATASET_PATH)
    assert len(df) > 0
    return df


@pytest.fixture(scope="module")
def transformed(source_df):
    return transform_df(source_df)


def test_dataset_loads(source_df):
    assert len(source_df) > 0
    assert "Reservation_ID" in source_df.columns


def test_adds_missing_defaults(transformed):
    out = transformed

    assert "Customer_ID" in out.columns
    assert "Vehicle_Class" in out.columns
    assert "Distance_Driven" in out.columns
    assert "vehicle_id_invalid_flag" in out.columns
    assert "is_completed" in out.columns
    assert "rental_hours" in out.columns
    assert "distance_km" in out.columns
    assert "lead_time_hours" in out.columns
    assert "booking_month" in out.columns
    assert "pickup_date" in out.columns


def test_coercion_and_boolean_flag(transformed):
    out = transformed

    assert pd.api.types.is_datetime64_any_dtype(out["Booking_TS"])
    assert pd.api.types.is_datetime64_any_dtype(out["Pickup_TS"])
    assert pd.api.types.is_datetime64_any_dtype(out["Return_TS"])
    assert pd.api.types.is_numeric_dtype(out["Rate"])
    assert pd.api.types.is_numeric_dtype(out["Distance_Driven"])
    assert pd.api.types.is_bool_dtype(out["vehicle_id_invalid_flag"])

    raw_values = out["Vehicle_ID_Invalid"].astype(str).str.lower().str.strip()
    expected_flag = raw_values.isin(["true", "1", "yes"])
    assert expected_flag.equals(out["vehicle_id_invalid_flag"])


def test_clips_and_computes_basic_metrics(transformed):
    out = transformed

    assert (out["rental_hours"].dropna() >= 0).all()
    assert (out["distance_km"].dropna() >= 0).all()
    assert (out["lead_time_hours"].dropna() >= 0).all()
    assert pd.api.types.is_bool_dtype(out["is_completed"])


def test_missing_duration_is_filled_from_timestamps(transformed):
    out = transformed
    mask = out["Duration_Hours"].isna() & out["Pickup_TS"].notna() & out["Return_TS"].notna()
    subset = out.loc[mask, ["Pickup_TS", "Return_TS", "rental_hours"]]

    if subset.empty:
        pytest.skip("No rows with missing duration and valid timestamps in dataset")

    expected = ((subset["Return_TS"] - subset["Pickup_TS"]).dt.total_seconds() / 3600).clip(lower=0)
    assert np.allclose(subset["rental_hours"].to_numpy(), expected.to_numpy(), equal_nan=True)


def test_temporal_features_created(transformed):
    out = transformed

    assert out["booking_month"].notna().any()
    assert out["pickup_date"].notna().any()
