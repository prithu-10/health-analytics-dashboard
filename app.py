import os
import re
import sqlite3
import random
import requests
from datetime import datetime, timedelta
from functools import wraps

import pandas as pd
NEWS_API_KEY = "52e6d15f18884782a55ffa3f371342f1"
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# Optional Google OAuth
GOOGLE_ENABLED = False
try:
    from flask_dance.contrib.google import make_google_blueprint, google
    GOOGLE_ENABLED = True
except Exception:
    GOOGLE_ENABLED = False

app = Flask(__name__)
app.secret_key = "healthify_final_secret_key_change_me"

DB_NAME = "users.db"
data = pd.DataFrame()

# -----------------------------
# Relief fund data by country
# -----------------------------
RELIEF_FUNDS = {
    "India": [
        {
            "name": "Ayushman Bharat (PM-JAY)",
            "description": "Public health insurance support for eligible low-income families.",
            "eligibility": "Economically vulnerable households based on SECC criteria and scheme rules."
        },
        {
            "name": "State Health Relief Schemes",
            "description": "Some states provide medical support, reimbursement, or critical care assistance.",
            "eligibility": "Depends on state, income category, hospital type, and documentation."
        }
    ],
    "United States": [
        {
            "name": "Medicaid / CHIP",
            "description": "Government-supported healthcare assistance for eligible low-income individuals and families.",
            "eligibility": "Income-based and state-specific eligibility."
        },
        {
            "name": "ACA Marketplace Subsidies",
            "description": "Premium assistance for qualifying individuals purchasing insurance.",
            "eligibility": "Based on household income and insurance status."
        }
    ],
    "Brazil": [
        {
            "name": "SUS Public Healthcare Support",
            "description": "Universal public healthcare access and support through the national system.",
            "eligibility": "Available broadly through the public healthcare system."
        }
    ],
    "Germany": [
        {
            "name": "Statutory Health Insurance Support",
            "description": "Coverage and healthcare support through public health insurance frameworks.",
            "eligibility": "Depends on insurance enrollment, income category, and residence status."
        }
    ],
    "France": [
        {
            "name": "Protection Maladie Universelle / Public Coverage",
            "description": "Public healthcare support and reimbursement mechanisms.",
            "eligibility": "Depends on residency and insurance eligibility rules."
        }
    ],
    "Japan": [
        {
            "name": "National Health Insurance Support",
            "description": "Government-backed health coverage support under the public insurance system.",
            "eligibility": "Depends on residency, enrollment, and insurance category."
        }
    ]
}


# -----------------------------
# Database
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            phone TEXT,
            role TEXT,
            password TEXT,
            google_id TEXT,
            two_factor_enabled INTEGER DEFAULT 0,
            country TEXT DEFAULT 'India',
            previous_medical_conditions TEXT DEFAULT '',
            last_login TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Helpers
# -----------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def validate_password(password: str):
    letters = len(re.findall(r"[A-Za-z]", password))
    has_number = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]", password))

    if letters < 4:
        return False, "Password must contain at least 4 letters."
    if not has_number:
        return False, "Password must contain at least 1 number."
    if not has_special:
        return False, "Password must contain at least 1 special character."

    return True, ""


def get_user_by_username(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user


def get_user_by_identifier(identifier):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cur.fetchone()
    conn.close()
    return user


def generate_otp():
    return str(random.randint(100000, 999999))


def store_otp_for_session(username):
    otp = generate_otp()
    session["otp_user"] = username
    session["otp_code"] = otp
    session["otp_expiry"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    print(f"[OTP for {username}] => {otp}")


def otp_valid(code):
    otp_code = session.get("otp_code")
    expiry = session.get("otp_expiry")

    if not otp_code or not expiry:
        return False

    try:
        expiry_dt = datetime.fromisoformat(expiry)
    except Exception:
        return False

    if datetime.utcnow() > expiry_dt:
        return False

    return code == otp_code


def update_last_login(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET last_login = ? WHERE username = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username)
    )
    conn.commit()
    conn.close()


# -----------------------------
# CSV Loading
# -----------------------------
def find_csv_file():
    possible = [
        "covid_cleaned.csv",
        "cleaned_covid_data.csv",
        "covid_data.csv",
        "data.csv",
        "dataset.csv",
        "cleaned_data.csv"
    ]

    for name in possible:
        if os.path.exists(name):
            return name

    for file in os.listdir("."):
        if file.lower().endswith(".csv"):
            return file

    return None


def normalize_columns(df):
    rename_map = {}

    for col in df.columns:
        c = str(col).strip().lower()

        if c in ["country", "location", "nation"]:
            rename_map[col] = "Country"
        elif c in ["date", "day", "report_date"]:
            rename_map[col] = "Date"
        elif c in ["cases", "new_cases", "new cases", "total_cases", "confirmed"]:
            rename_map[col] = "Cases"
        elif c in ["deaths", "new_deaths", "total_deaths"]:
            rename_map[col] = "Deaths"
        elif c in ["positiverate", "positive_rate", "positivity", "test_positivity_rate"]:
            rename_map[col] = "PositiveRate"
        elif c in ["vaccinated", "vaccination", "people_vaccinated", "vaccination_rate", "vaccine_rate"]:
            rename_map[col] = "Vaccinated"
        elif c in ["hospitalbeds", "hospital_beds", "hospital beds"]:
            rename_map[col] = "HospitalBeds"
        elif c in ["population"]:
            rename_map[col] = "Population"
        elif c in ["medianage", "median_age"]:
            rename_map[col] = "MedianAge"
        elif c in ["stringency", "stringency_index"]:
            rename_map[col] = "Stringency"

    return df.rename(columns=rename_map)


def load_data():
    global data
    csv_file = find_csv_file()

    if not csv_file:
        print("No CSV file found.")
        data = pd.DataFrame()
        return

    try:
        df = pd.read_csv(csv_file)
        df = normalize_columns(df)

        if "Country" not in df.columns:
            print("CSV missing Country column.")
            data = pd.DataFrame()
            return

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        else:
            df["Date"] = pd.date_range(start="2020-01-01", periods=len(df), freq="D")

        for col in ["Cases", "Deaths", "PositiveRate", "Vaccinated", "HospitalBeds", "Population", "MedianAge", "Stringency"]:
            if col not in df.columns:
                df[col] = 0

        df["Country"] = df["Country"].astype(str).str.strip()
        for col in ["Cases", "Deaths", "PositiveRate", "Vaccinated", "HospitalBeds", "Population", "MedianAge", "Stringency"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df = df.dropna(subset=["Date"]).copy()
        df = df.sort_values(["Country", "Date"]).reset_index(drop=True)

        data = df
        print(f"Loaded dataset: {csv_file}")
        print("Columns:", list(df.columns))

    except Exception as e:
        print("Error loading CSV:", e)
        data = pd.DataFrame()


def get_country_df(country):
    if data.empty:
        return pd.DataFrame()
    df = data[data["Country"].astype(str).str.strip().str.lower() == country.strip().lower()].copy()
    return df.sort_values("Date").reset_index(drop=True)


# -----------------------------
# Current dashboard scores
# -----------------------------
def compute_scores(latest):
    cases = float(latest.get("Cases", 0))
    deaths = float(latest.get("Deaths", 0))
    positive_rate = float(latest.get("PositiveRate", 0))
    vaccinated = float(latest.get("Vaccinated", 0))
    hospital_beds = float(latest.get("HospitalBeds", 0))
    stringency = float(latest.get("Stringency", 0))
    median_age = float(latest.get("MedianAge", 0))
    population = float(latest.get("Population", 1)) or 1

    health_risk_score = min(100, max(0, 20 + positive_rate * 3 + deaths / 500 + median_age * 0.15))
    healthcare_strain = min(100, max(0, 10 + deaths / 400 + cases / 50000 + stringency * 0.25))
    recovery_readiness = min(100, max(0, 85 - positive_rate * 2 - deaths / 700 - median_age * 0.08 + hospital_beds * 0.01))
    vaccination_shield = min(100, max(0, vaccinated))
    trend_pressure = min(100, max(0, 15 + positive_rate * 2 + deaths / 600 + (cases / population) * 1000))

    return {
        "health_risk_score": round(health_risk_score, 2),
        "healthcare_strain": round(healthcare_strain, 2),
        "recovery_readiness": round(recovery_readiness, 2),
        "vaccination_shield": round(vaccination_shield, 2),
        "trend_pressure": round(trend_pressure, 2)
    }


# -----------------------------
# Google OAuth optional
# -----------------------------
if GOOGLE_ENABLED:
    google_bp = make_google_blueprint(
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        redirect_to="google_login"
    )
    app.register_blueprint(google_bp, url_prefix="/login")


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/live_news")
@login_required
def live_news():
    try:
        country = request.args.get("country", "India").strip()

        country_map = {
            "India": "in",
            "United States": "us",
            "Brazil": "br",
            "Japan": "jp",
            "Germany": "de",
            "France": "fr"
        }

        news_country = country_map.get(country, "in")

        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": news_country,
            "category": "health",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return jsonify({
                "articles": [],
                "error": data.get("message", "Unable to fetch news")
            })

        articles = []
        for article in data.get("articles", [])[:5]:
            articles.append({
                "title": article.get("title", "No title"),
                "source": (article.get("source") or {}).get("name", "Unknown source"),
                "url": article.get("url", "#"),
                "publishedAt": article.get("publishedAt", "")
            })

        return jsonify({
            "articles": articles,
            "country": country
        })

    except Exception as e:
        return jsonify({
            "articles": [],
            "error": str(e)
        }), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "Clinician").strip()
        two_factor = request.form.get("two_factor")

        user = get_user_by_identifier(identifier)

        if not user:
            flash("Account not found. Please create an account first.")
            return redirect(url_for("signup"))

        if user["role"] and user["role"] != role:
            flash("Selected role does not match this account.")
            return redirect(url_for("login"))

        if not user["password"]:
            flash("This account uses Google sign-in. Please use Google login.")
            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):
            flash("Invalid password.")
            return redirect(url_for("login"))

        use_2fa = bool(two_factor) or bool(user["two_factor_enabled"])

        if use_2fa:
            store_otp_for_session(user["username"])
            session["pending_login_user"] = user["username"]
            flash("OTP generated. For demo, check terminal.")
            return redirect(url_for("verify_otp"))

        session["user"] = user["username"]
        update_last_login(user["username"])
        return redirect(url_for("dashboard"))

    return render_template("login.html", google_enabled=GOOGLE_ENABLED)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "Clinician").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        country = request.form.get("country", "India").strip()
        previous_medical_conditions = request.form.get("previous_medical_conditions", "").strip()
        two_factor_enabled = 1 if request.form.get("two_factor_enabled") else 0

        if not full_name or not username or not email or not phone or not password or not confirm_password:
            flash("All fields are required.")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("signup"))

        valid, msg = validate_password(password)
        if not valid:
            flash(msg)
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (
                    full_name, username, email, phone, role, password,
                    two_factor_enabled, country, previous_medical_conditions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, username, email, phone, role, hashed_password,
                two_factor_enabled, country, previous_medical_conditions
            ))
            conn.commit()
            conn.close()

            flash("Account created successfully. Please log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username or email already exists.")
            return redirect(url_for("signup"))

    return render_template("signup.html", google_enabled=GOOGLE_ENABLED)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        user = get_user_by_identifier(identifier)
        if not user:
            flash("Account not found.")
            return redirect(url_for("forgot_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("forgot_password"))

        valid, msg = validate_password(new_password)
        if not valid:
            flash(msg)
            return redirect(url_for("forgot_password"))

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(new_password), user["id"]))
        conn.commit()
        conn.close()

        flash("Password reset successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_login_user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        code = request.form.get("otp", "").strip()

        if otp_valid(code):
            username = session["pending_login_user"]
            session["user"] = username
            update_last_login(username)

            session.pop("pending_login_user", None)
            session.pop("otp_user", None)
            session.pop("otp_code", None)
            session.pop("otp_expiry", None)

            flash("OTP verified successfully.")
            return redirect(url_for("dashboard"))

        flash("Invalid or expired OTP.")
        return redirect(url_for("verify_otp"))

    return render_template("verify_otp.html")


@app.route("/resend_otp")
def resend_otp():
    username = session.get("pending_login_user")
    if not username:
        return redirect(url_for("login"))

    store_otp_for_session(username)
    flash("OTP regenerated. Check terminal.")
    return redirect(url_for("verify_otp"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/google-login")
def google_login():
    if not GOOGLE_ENABLED:
        flash("Google auth is not configured yet.")
        return redirect(url_for("login"))

    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch Google profile.")
        return redirect(url_for("login"))

    info = resp.json()
    email = info.get("email")
    google_id = info.get("id")
    name = info.get("name", "Google User")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()

    if not user:
        username = email.split("@")[0]
        try:
            cur.execute("""
                INSERT INTO users (
                    full_name, username, email, phone, role, password,
                    google_id, two_factor_enabled, country, previous_medical_conditions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, username, email, "", "Clinician", "",
                google_id, 0, "India", ""
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

    conn.close()

    session["user"] = user["username"]
    update_last_login(user["username"])
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_user_by_username(session["user"])
    return render_template("dashboard.html", username=user["username"], full_name=user["full_name"])


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = session["user"]
    user = get_user_by_username(username)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "Clinician").strip()
        country = request.form.get("country", "India").strip()
        previous_medical_conditions = request.form.get("previous_medical_conditions", "").strip()
        two_factor_enabled = 1 if request.form.get("two_factor_enabled") else 0

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET full_name = ?, phone = ?, role = ?, country = ?, previous_medical_conditions = ?, two_factor_enabled = ?
            WHERE username = ?
        """, (full_name, phone, role, country, previous_medical_conditions, two_factor_enabled, username))
        conn.commit()
        conn.close()

        flash("Profile updated successfully.")
        return redirect(url_for("profile"))

    funds = RELIEF_FUNDS.get(user["country"], [])
    return render_template("profile.html", user=user, funds=funds)


@app.route("/get_data")
@login_required
def get_data():
    country = request.args.get("country", "India")
    df = get_country_df(country)

    if df.empty:
        return jsonify({
            "health_risk_score": 0,
            "healthcare_strain": 0,
            "recovery_readiness": 0,
            "vaccination_shield": 0,
            "trend_pressure": 0
        })

    latest = df.iloc[-1]
    scores = compute_scores(latest)
    return jsonify(scores)


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        req = request.get_json()
        country = req.get("country", "India")
        vacc_input = float(req.get("vaccInput", 0))
        death_input = float(req.get("deathInput", 0))
        year = int(req.get("year", 2027))

        df = get_country_df(country)
        if df.empty:
            return jsonify({
                "health_risk_score": 0,
                "healthcare_strain": 0,
                "recovery_readiness": 0,
                "vaccination_shield": 0,
                "trend_pressure": 0,
                "reinfection_risk": 0,
                "long_covid_impact": 0,
                "collapse_risk": 0,
                "mental_stress": 0,
                "future_heart_risk": 0,
                "future_lung_risk": 0,
                "future_diabetes_risk": 0,
                "future_neuro_mental_risk": 0,
                "future_long_covid_burden": 0
            })

        latest = df.iloc[-1]
        base_deaths = float(latest.get("Deaths", 0))
        base_positive = float(latest.get("PositiveRate", 0))
        base_hospital_beds = float(latest.get("HospitalBeds", 0))
        base_median_age = float(latest.get("MedianAge", 0))

        year_factor = max(0, year - 2024)

        vaccination_shield = min(100, max(0, 20 + vacc_input * 0.6 - year_factor * 1))
        healthcare_strain = min(100, max(0, 10 + (base_deaths / 500) + death_input * 0.8 + year_factor * 3 + base_median_age * 0.1))
        trend_pressure = min(100, max(0, 15 + (base_positive * 3) + death_input * 0.7 - vacc_input * 0.4 + year_factor * 2))
        health_risk_score = min(100, max(0, 25 + death_input * 0.9 - vacc_input * 0.5 + year_factor * 2 + base_median_age * 0.08))
        recovery_readiness = min(100, max(0, 50 + vacc_input * 0.4 - death_input * 0.6 - year_factor * 1.5 + base_hospital_beds * 0.02))

        reinfection_risk = min(100, max(0, 30 + death_input * 0.5 - vacc_input * 0.3 + year_factor * 2))
        long_covid_impact = min(100, max(0, 20 + base_positive * 2 + death_input * 0.4))
        collapse_risk = min(100, max(0, healthcare_strain * 0.7 + trend_pressure * 0.5))
        mental_stress = min(100, max(0, trend_pressure * 0.6 + health_risk_score * 0.4))

        future_heart_risk = min(100, max(0, 20 + health_risk_score * 0.35 + trend_pressure * 0.25 + death_input * 0.2))
        future_lung_risk = min(100, max(0, 25 + healthcare_strain * 0.25 + trend_pressure * 0.35 + death_input * 0.25 - vacc_input * 0.15))
        future_diabetes_risk = min(100, max(0, 15 + long_covid_impact * 0.30 + health_risk_score * 0.20 + year_factor * 2))
        future_neuro_mental_risk = min(100, max(0, 20 + mental_stress * 0.40 + long_covid_impact * 0.25 + trend_pressure * 0.20))
        future_long_covid_burden = min(100, max(0, 20 + long_covid_impact * 0.45 + reinfection_risk * 0.25 + year_factor * 1.5))

        return jsonify({
            "health_risk_score": round(health_risk_score, 2),
            "healthcare_strain": round(healthcare_strain, 2),
            "recovery_readiness": round(recovery_readiness, 2),
            "vaccination_shield": round(vaccination_shield, 2),
            "trend_pressure": round(trend_pressure, 2),
            "reinfection_risk": round(reinfection_risk, 2),
            "long_covid_impact": round(long_covid_impact, 2),
            "collapse_risk": round(collapse_risk, 2),
            "mental_stress": round(mental_stress, 2),
            "future_heart_risk": round(future_heart_risk, 2),
            "future_lung_risk": round(future_lung_risk, 2),
            "future_diabetes_risk": round(future_diabetes_risk, 2),
            "future_neuro_mental_risk": round(future_neuro_mental_risk, 2),
            "future_long_covid_burden": round(future_long_covid_burden, 2)
        })

    except Exception as e:
        print("Prediction route error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    load_data()
    app.run(host="0.0.0.0", port=5000)
