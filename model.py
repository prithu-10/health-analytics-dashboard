import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

data = pd.read_csv("cleaned_data.csv")
data["Date"] = pd.to_datetime(data["Date"])
data = data.sort_values(["Country", "Date"]).reset_index(drop=True)

feature_cols = [
    "Cases",
    "Deaths",
    "Vaccinated",
    "Population",
    "MedianAge",
    "HospitalBeds",
    "PositiveRate",
    "Stringency"
]

for col in feature_cols:
    data[col] = pd.to_numeric(data[col], errors="coerce")

data = data.dropna(subset=feature_cols)

scaler = MinMaxScaler()
scaled = pd.DataFrame(scaler.fit_transform(data[feature_cols]), columns=feature_cols)

data["Cases_N"] = scaled["Cases"]
data["Deaths_N"] = scaled["Deaths"]
data["Vaccinated_N"] = scaled["Vaccinated"]
data["Population_N"] = scaled["Population"]
data["MedianAge_N"] = scaled["MedianAge"]
data["HospitalBeds_N"] = scaled["HospitalBeds"]
data["PositiveRate_N"] = scaled["PositiveRate"]
data["Stringency_N"] = scaled["Stringency"]


def clamp_score(value):
    return max(0, min(100, round(value)))


def compute_scores(row):
    cases = row["Cases_N"]
    deaths = row["Deaths_N"]
    vaccinated = row["Vaccinated_N"]
    median_age = row["MedianAge_N"]
    hospital_beds = row["HospitalBeds_N"]
    positive_rate = row["PositiveRate_N"]
    stringency = row["Stringency_N"]

    health_risk = (
        0.28 * deaths +
        0.22 * positive_rate +
        0.18 * cases +
        0.16 * median_age +
        0.10 * stringency -
        0.16 * vaccinated -
        0.08 * hospital_beds
    ) * 100

    healthcare_strain = (
        0.34 * cases +
        0.24 * deaths +
        0.22 * positive_rate +
        0.10 * stringency -
        0.20 * hospital_beds -
        0.08 * vaccinated
    ) * 100

    recovery_readiness = (
        0.38 * vaccinated +
        0.22 * hospital_beds -
        0.16 * deaths -
        0.14 * positive_rate -
        0.10 * cases
    ) * 100 + 35

    vaccination_shield = (
        0.72 * vaccinated +
        0.18 * hospital_beds -
        0.10 * positive_rate
    ) * 100

    trend_pressure = (
        0.40 * cases +
        0.25 * deaths +
        0.20 * positive_rate +
        0.10 * stringency -
        0.10 * vaccinated
    ) * 100

    return {
        "health_risk_score": clamp_score(health_risk),
        "healthcare_strain": clamp_score(healthcare_strain),
        "recovery_readiness": clamp_score(recovery_readiness),
        "vaccination_shield": clamp_score(vaccination_shield),
        "trend_pressure": clamp_score(trend_pressure)
    }


def get_country_latest(country="India"):
    df_country = data[data["Country"] == country].copy()
    if df_country.empty:
        return None
    return df_country.iloc[-1]


def predict_future(country="India", vacc_input=0, death_input=0):
    row = get_country_latest(country)
    if row is None:
        return {
            "health_risk_score": 0,
            "healthcare_strain": 0,
            "recovery_readiness": 0,
            "vaccination_shield": 0,
            "trend_pressure": 0
        }

    sim = row.copy()

    max_vacc = data["Vaccinated"].max()
    max_deaths = data["Deaths"].max()

    sim["Vaccinated"] = max(0, sim["Vaccinated"] + float(vacc_input))
    if float(death_input) > 0:
        sim["Deaths"] = float(death_input)

    sim["Vaccinated_N"] = 0 if max_vacc == 0 else min(1, sim["Vaccinated"] / max_vacc)
    sim["Deaths_N"] = 0 if max_deaths == 0 else min(1, sim["Deaths"] / max_deaths)

    scores = compute_scores(sim)
    return scores
