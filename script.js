function setThemeFromStorage() {
  const savedTheme = localStorage.getItem("theme");
  const themeToggle = document.getElementById("themeToggle");

  if (savedTheme === "light") {
    document.body.classList.add("light-mode");
    if (themeToggle) themeToggle.textContent = "☀️ Light";
  } else {
    document.body.classList.remove("light-mode");
    if (themeToggle) themeToggle.textContent = "🌙 Dark";
  }
}

function initTheme() {
  const themeToggle = document.getElementById("themeToggle");
  setThemeFromStorage();

  if (!themeToggle) return;

  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("light-mode");

    if (document.body.classList.contains("light-mode")) {
      themeToggle.textContent = "☀️ Light";
      localStorage.setItem("theme", "light");
    } else {
      themeToggle.textContent = "🌙 Dark";
      localStorage.setItem("theme", "dark");
    }
  });
}

function setValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;

  const num = Number(value);
  if (isNaN(num)) {
    el.textContent = "--";
  } else {
    el.textContent = `${Math.round(num)}/100`;
  }
}

function updateReactiveModules(data) {
  const trend = Number(data.trend_pressure) || 0;
  const recovery = Number(data.recovery_readiness) || 0;

  const strainStatus = document.getElementById("strainStatus");
  const strainSub = document.getElementById("strainSub");
  const recoveryViewStatus = document.getElementById("recoveryViewStatus");
  const recoveryViewSub = document.getElementById("recoveryViewSub");

  if (strainStatus && strainSub) {
    if (trend >= 70) {
      strainStatus.textContent = "High";
      strainSub.textContent = "Variant / public health pressure rising";
    } else if (trend >= 40) {
      strainStatus.textContent = "Moderate";
      strainSub.textContent = "Monitor regional stress movement";
    } else {
      strainStatus.textContent = "Low";
      strainSub.textContent = "Situation relatively stable";
    }
  }

  if (recoveryViewStatus && recoveryViewSub) {
    if (recovery < 40) {
      recoveryViewStatus.textContent = "Critical";
      recoveryViewSub.textContent = "Recovery system needs support";
    } else if (recovery < 70) {
      recoveryViewStatus.textContent = "Watch";
      recoveryViewSub.textContent = "Recovery needs monitoring";
    } else {
      recoveryViewStatus.textContent = "Stable";
      recoveryViewSub.textContent = "Recovery trend acceptable";
    }
  }
}

function updatePredictionInsight(data) {
  const predText = document.getElementById("predictionInsight");
  if (!predText) return;

  const risk = Number(data.health_risk_score) || 0;
  const strain = Number(data.healthcare_strain) || 0;
  const recovery = Number(data.recovery_readiness) || 0;
  const shield = Number(data.vaccination_shield) || 0;

  if (risk >= 70 || strain >= 70) {
    predText.textContent =
      "Scenario indicates high future stress. More deaths or lower protection sharply worsens public-health burden.";
  } else if (shield >= 70 && recovery >= 60) {
    predText.textContent =
      "Scenario looks relatively favorable. Improved protection supports better recovery readiness and lower risk.";
  } else {
    predText.textContent =
      "Scenario shows mixed outcomes. Protection and mortality inputs are influencing system pressure together.";
  }
}

function updateFutureOutlook(data, year) {
  const el = document.getElementById("futureOutlook");
  if (!el) return;

  const risk = Number(data.health_risk_score) || 0;
  const shield = Number(data.vaccination_shield) || 0;
  const strain = Number(data.healthcare_strain) || 0;

  if (risk >= 70 || strain >= 70) {
    el.textContent = `Projected ${year} outlook suggests high public-health stress under the current simulation.`;
  } else if (shield >= 70) {
    el.textContent = `Projected ${year} outlook appears more stable due to stronger vaccination protection.`;
  } else {
    el.textContent = `Projected ${year} outlook is moderate and depends on vaccination growth and mortality pressure.`;
  }
}
async function loadLiveNews(country = "India") {
  try {
    const response = await fetch(`/live_news?country=${encodeURIComponent(country)}`);
    const data = await response.json();

    const list = document.getElementById("newsList");
    const status = document.getElementById("newsStatus");

    if (!list || !status) return;

    if (data.error) {
      status.textContent = `News unavailable: ${data.error}`;
      list.innerHTML = "";
      return;
    }

    const articles = data.articles || [];

    if (articles.length === 0) {
      status.textContent = `No live public health headlines found for ${country}.`;
      list.innerHTML = "";
      return;
    }

    status.textContent = `Showing latest health headlines for ${country}`;

    list.innerHTML = articles.map(article => `
      <div class="news-item">
        <h4>${article.title}</h4>
        <p>${article.source}${article.publishedAt ? " • " + article.publishedAt : ""}</p>
        <p><a href="${article.url}" target="_blank">Open article</a></p>
      </div>
    `).join("");
  } catch (error) {
    const status = document.getElementById("newsStatus");
    if (status) status.textContent = "Failed to load live news.";
    console.error("Live news error:", error);
  }
}

async function loadDashboardData(country = "India") {
  try {
    const response = await fetch(`/get_data?country=${encodeURIComponent(country)}`);
    const data = await response.json();

    setValue("healthRiskScore", data.health_risk_score);
    setValue("trendPressure", data.trend_pressure);
    setValue("vaccinationShieldTop", data.vaccination_shield);
    setValue("healthcareStrain", data.healthcare_strain);
    setValue("recoveryReadiness", data.recovery_readiness);
    setValue("vaccinationShield", data.vaccination_shield);

    const countryProjectionLabel = document.getElementById("countryProjectionLabel");
    if (countryProjectionLabel) {
      countryProjectionLabel.textContent = country;
    }

    updateReactiveModules(data);
  } catch (error) {
    console.error("Error loading dashboard data:", error);
  }
}

async function runPrediction() {
  try {
    const country = document.getElementById("countrySelect")?.value || "India";
    const vaccInput = parseFloat(document.getElementById("vaccInput")?.value) || 0;
    const deathInput = parseFloat(document.getElementById("deathInput")?.value) || 0;
    const year = parseInt(document.getElementById("projectionYear")?.value) || 2027;

    const response = await fetch("/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        country,
        vaccInput,
        deathInput,
        year
      })
    });

    const data = await response.json();

    setValue("predHealthRisk", data.health_risk_score);
    setValue("predHealthcareStrain", data.healthcare_strain);
    setValue("predRecoveryReadiness", data.recovery_readiness);
    setValue("predVaccinationShield", data.vaccination_shield);
    setValue("predTrendPressure", data.trend_pressure);

    setValue("reinfectionRisk", data.reinfection_risk);
    setValue("longCovid", data.long_covid_impact);
    setValue("collapseRisk", data.collapse_risk);
    setValue("mentalStress", data.mental_stress);

    setValue("futureHeartRisk", data.future_heart_risk);
    setValue("futureLungRisk", data.future_lung_risk);
    setValue("futureDiabetesRisk", data.future_diabetes_risk);
    setValue("futureNeuroRisk", data.future_neuro_mental_risk);
    setValue("futureLongCovidBurden", data.future_long_covid_burden);

    updateReactiveModules(data);
    updatePredictionInsight(data);
    updateFutureOutlook(data, year);
  } catch (error) {
    console.error("Prediction error:", error);
  }
}
document.addEventListener("DOMContentLoaded", function () {
  initTheme();

  const countrySelect = document.getElementById("countrySelect");
  const predictBtn = document.getElementById("predictBtn");

  if (countrySelect) {
    loadDashboardData(countrySelect.value);
    loadLiveNews(countrySelect.value);

    countrySelect.addEventListener("change", function () {
      loadDashboardData(countrySelect.value);
      loadLiveNews(countrySelect.value);
    });
  }

  if (predictBtn) {
    predictBtn.addEventListener("click", runPrediction);
  }
});

