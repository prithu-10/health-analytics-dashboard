from flask import Flask, jsonify, render_template, redirect, url_for, request, session
import pandas as pd
import subprocess
from model import predict_future

# Run R script
subprocess.run(["Rscript", "eda.R"])


# OAuth
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = "secret"

google_bp = make_google_blueprint(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_SECRET",
    redirect_to="dashboard"
)
app.register_blueprint(google_bp, url_prefix="/login")

data = pd.read_csv("cleaned_data.csv")

@app.route("/")
def home():
    return render_template("login.html")

from flask_dance.contrib.google import google

@app.route("/dashboard")
def dashboard():
    if not google.authorized and 'user' not in session:
        return redirect('/')

    return render_template("dashboard.html")

users = {}

@app.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    pwd = request.form['password']

    if user in users and users[user] == pwd:
        session['user'] = user
        return redirect('/dashboard')
    return "Invalid credentials"

@app.route('/signup', methods=['GET','POST'])
def signup():
  
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        users[user] = pwd
        return redirect('/')

    return render_template("signup.html")

@app.route("/login/google")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()

    session['user'] = info['email']

    return redirect("/dashboard")

@app.route("/data")
def get_data():
    return data.to_json(orient='records')

@app.route("/predict")
def predict():
    return jsonify(predict_future())

@app.route("/full-data")
def full_data():
    import pandas as pd
    from flask import request

    country = request.args.get("country", "India")

    df = pd.read_csv("cleaned_data.csv")
    df = df[df["Country"] == country]
    df = df.sort_values("Date")

    from model import predict_future
    preds = predict_future()

    return {
        "dates": df["Date"].tolist(),
        "cases": df["Cases"].tolist(),
        "deaths": df["Deaths"].tolist(),
        "vaccinated": df["Vaccinated"].tolist(),
        "stringency": df["Stringency"].tolist(),
        "positive_rate": df["PositiveRate"].tolist(),
        "pred_cases": preds["cases"],
        "pred_deaths": preds["deaths"]
    }
    
@app.route("/stats")
def stats():
    import pandas as pd
    df = pd.read_csv("cleaned_data.csv")

    return {
        "total_cases": int(df["Confirmed"].iloc[-1]),
        "total_deaths": int(df["Deaths"].iloc[-1]) if "Deaths" in df else 0
    }
app.run(host='0.0.0.0', port=5000)
