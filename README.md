# COVID Recovery Intelligence & Prediction System

## Overview

This project presents an end-to-end data science solution to analyze and predict COVID-19 recovery outcomes using **R programming, machine learning, and business intelligence tools**. It integrates clinical data with environmental factors to generate meaningful insights and support data-driven decision-making.

##  Problem Statement
COVID-19 recovery is influenced by multiple factors such as patient demographics, health conditions, and environmental variables. The objective of this project is to:

* Identify key factors affecting recovery
* Build a predictive model for outcome estimation
* Visualize trends and insights through an interactive dashboard

##  Dataset

* Public non-Kaggle dataset from reliable sources
* Contains **10,000+ records** and **8+ attributes**
* Includes both **numeric** (age, severity) and **categorical** (gender, symptoms, outcome) features

## API Integration

To enhance the dataset, a **weather API (Open-Meteo)** was integrated:

* Data fetched using `httr`
* JSON parsed using `jsonlite`
* Extracted weather attributes (temperature, wind, etc.)
* Merged with the primary dataset for enriched analysis

##  Methodology

###  Data Preprocessing

* Handling missing values
* Encoding categorical variables
* Feature transformation and selection

### Exploratory Data Analysis (EDA)

Performed using **ggplot2**:

* Distribution and trend analysis
* Correlation assessment
* Outlier detection
* Comparative category analysis

###  Modeling

* Implemented predictive models (classification/regression)
* Evaluated using metrics such as **accuracy, RMSE, and confusion matrix**

## Power BI Dashboard

An interactive dashboard was developed to present insights:

* Displays key statistics and recovery trends
* Includes model predictions
* Integrates **R-based custom visuals (ggplot2)** for advanced analytics

##  Deployment (Docker)

* Flask-based application containerized using Docker
* Ensures portability and reproducibility
* Power BI module excluded as per project guidelines

## Version Control (GitHub)

* Maintained with **10+ meaningful commits**
* Uses **main and development branches**
* Includes structured project files and documentation
* Sensitive data (API keys) secured using `.gitignore`

## Key Insights


* Recovery outcomes are influenced by both clinical and environmental factors
* Predictive modeling enables early risk assessment
* Visual analytics improve interpretability of results

## Contributors
Prithu
Saanvi
