import pandas as pd
from sklearn.linear_model import LinearRegression

data = pd.read_csv("cleaned_data.csv")

data['Date'] = pd.to_datetime(data['Date'])
data['Days'] = (data['Date'] - data['Date'].min()).dt.days

# 🔥 ADVANCED FEATURES
X = data[
    ['Days', 'Vaccinated', 'Deaths', 'Population',
     'MedianAge', 'HospitalBeds', 'PositiveRate', 'Stringency']
]

y_cases = data['Cases']
y_deaths = data['Deaths']

cases_model = LinearRegression().fit(X, y_cases)
deaths_model = LinearRegression().fit(X, y_deaths)

def predict_future():

    last = data.iloc[-1]

    prev_cases = last['Cases']
    prev_deaths = last['Deaths']

    preds_cases = []
    preds_deaths = []

    for i in range(1, 8):

        row = [[
            prev_cases,
            prev_deaths,
            last['Vaccinated'],
            last['Population'],
            last['MedianAge'],
            last['HospitalBeds'],
            last['PositiveRate'],
            last['Stringency']
        ]]

        pred_case = cases_model.predict(row)[0]
        pred_death = deaths_model.predict(row)[0]

        # 🔥 CLAMP VALUES (VERY IMPORTANT)
        pred_case = min(pred_case, prev_cases * 1.2)
        pred_death = min(pred_death, prev_deaths * 1.2)

        preds_cases.append(pred_case)
        preds_deaths.append(pred_death)

        prev_cases = pred_case
        prev_deaths = pred_death

    return {
        "cases": preds_cases,
        "deaths": preds_deaths
    }