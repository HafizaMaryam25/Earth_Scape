🌍 EarthScape Climate Agency

EarthScape Climate Agency is an end-to-end Big Data, Machine Learning, and Climate Analytics platform built with Python.

The project combines climate-data ingestion, distributed-processing concepts, MapReduce analytics, machine-learning models, real-time telemetry simulation, authentication, REST APIs, and an interactive web dashboard into a single application.

Project status: Local development / portfolio project
Live deployment: Not currently deployed

📌 Overview

EarthScape is designed as a centralized platform for exploring climate data, detecting anomalies, analyzing greenhouse-gas trends, forecasting temperature behavior, and monitoring simulated real-time environmental telemetry.

The system demonstrates practical implementation of:

Data engineering pipelines

Simulated Hadoop HDFS architecture

MapReduce processing

Machine learning

REST API development

Authentication and authorization

Data visualization

Real-time data simulation

SQL Server LocalDB integration

✨ Key Features

📊 Climate Data & Analytics

Multi-source climate data ingestion

Historical climate datasets covering multiple zones and years

Data cleaning and missing-value handling

Climate-zone based data partitioning

Greenhouse-gas analysis

Weather-station data processing

🗄️ Big Data Processing

Simulated Hadoop HDFS architecture

DataNode and NameNode concepts

Partitioned climate datasets

Replication and block metadata

HDFS health and cluster monitoring

MapReduce job execution

⚙️ MapReduce Jobs

The project includes MapReduce workflows for:

Temperature Anomaly & Baseline Analysis

GHG Emissions & Warming Correlation

Extreme Weather & Climate Risk Analysis

🤖 Machine Learning

Three machine-learning pipelines are implemented:

Model

Purpose

Gradient Boosting Regressor

Temperature forecasting

Isolation Forest + RobustScaler

Climate anomaly detection

Random Forest Regressor

Climate impact / risk prediction

Pre-trained model artifacts are stored in the models/ directory.

📡 Real-Time Monitoring

Simulated IoT sensor telemetry

Temperature monitoring

CO₂ monitoring

Humidity monitoring

Pressure monitoring

Wind monitoring

PM2.5 monitoring

Real-time anomaly detection

🔐 Authentication & Authorization

User registration

Login and logout

Password hashing

Session-based authentication

Role-based authorization

Administrator and Climate Analyst roles

Protected API endpoints

📈 Interactive Dashboard

The frontend provides:

Climate KPI cards

Historical charts

Climate-zone analysis

Weather-station map

ML prediction tools

MapReduce job monitoring

Live telemetry

Alerts

Support tickets

System monitoring

🛠️ Technology Stack

Backend & Data

Python 3.10+

NumPy

Pandas

Scikit-learn

Joblib

Python HTTP Server

SQL Server LocalDB

pyodbc

bcrypt

Machine Learning

Gradient Boosting

Isolation Forest

RobustScaler

Random Forest

Feature engineering

Model evaluation

Frontend

HTML5

CSS3

JavaScript

Chart.js

Leaflet.js

Big Data Concepts

Hadoop HDFS simulation

Data partitioning

Replication

MapReduce

Distributed-processing concepts

Development Tools

Git

GitHub

VS Code / Visual Studio

Jupyter Notebook

🏗️ Architecture

                     ┌──────────────────────┐
                     │      Web Browser     │
                     │ Dashboard / Charts   │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │     server.py        │
                     │ REST API + Web Server │
                     └──────────┬───────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
 ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
 │ Data Ingestion │    │  HDFS Simulator│    │ Authentication │
 │ & Processing   │    │  & MapReduce   │    │ & SQL Database │
 └───────┬────────┘    └───────┬────────┘    └────────────────┘
         │                     │
         ▼                     ▼
 ┌────────────────┐    ┌────────────────┐
 │ Climate Data   │    │ MapReduce Jobs │
 │ Raw / Cleaned  │    │ & Analytics    │
 └───────┬────────┘    └───────┬────────┘
         │                     │
         └──────────────┬──────┘
                        ▼
                ┌────────────────┐
                │ Machine        │
                │ Learning       │
                │ Models         │
                └───────┬────────┘
                        │
                        ▼
                ┌────────────────┐
                │ Predictions &  │
                │ Insights       │
                └────────────────┘

📁 Project Structure

ml_project/
│
├── data/
│   ├── raw/
│   │   ├── climate_historical_daily.csv
│   │   ├── climate_zones.json
│   │   ├── greenhouse_gases_emissions.csv
│   │   ├── sensor_stream_sample.json
│   │   └── weather_stations.json
│   │
│   └── processed/
│
├── models/
│   ├── temp_forecaster.joblib
│   ├── anomaly_detector.joblib
│   ├── impact_model.joblib
│   ├── evaluation_report.json
│   └── models_evaluation_summary.json
│
├── notebooks/
│   └── 01_climate_bigdata_eda_ml.ipynb
│
├── src/
│   ├── data/
│   │   ├── generator.py
│   │   ├── ingestion.py
│   │   └── static_data.py
│   │
│   ├── hadoop/
│   │   └── hdfs_manager.py
│   │
│   ├── mapreduce/
│   │   ├── mr_temp_anomalies.py
│   │   ├── mr_ghg_emissions.py
│   │   ├── mr_extreme_events.py
│   │   └── mr_job_runner.py
│   │
│   └── ml/
│       ├── forecast_model.py
│       ├── anomaly_model.py
│       ├── impact_model.py
│       ├── train_all.py
│       └── evaluate_all.py
│
├── web/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── db.py
├── server.py
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md

📸 Screenshots

The repository contains screenshots demonstrating the main areas of the application.

Login



Dashboard



Weather Station Map



Machine Learning — Forecast



Machine Learning — Anomaly Detection



Machine Learning — Impact Analysis



Real-Time Streaming



Alerts



🚀 Getting Started

Prerequisites

Install the following before running the project:

Python 3.10 or newer

SQL Server LocalDB

ODBC Driver 18 for SQL Server

Git

SQL Server LocalDB is commonly available with Visual Studio.

1. Clone the Repository

git clone YOUR_GITHUB_REPOSITORY_URL
cd ml_project

2. Create a Virtual Environment

Windows PowerShell

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Windows CMD

python -m venv .venv
.venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables

Create a local .env file based on .env.example.

Example:

DB_SERVER=YOUR_SQL_SERVER_INSTANCE
DB_NAME=YOUR_DATABASE_NAME
PORT=8000

Do not commit .env to GitHub.

The repository's .gitignore already excludes environment files.

5. Prepare Climate Data

If processed data needs to be regenerated:

python -m src.data.ingestion

6. Run MapReduce Jobs

python -m src.mapreduce.mr_job_runner

7. Train the Machine Learning Models

python -m src.ml.train_all

This generates the trained model artifacts inside models/.

8. Evaluate the Models

python -m src.ml.evaluate_all

9. Start the Application

python server.py

The application runs locally at:

http://localhost:8000

10. Run the Jupyter Notebook

Optional:

jupyter notebook notebooks/01_climate_bigdata_eda_ml.ipynb

🧪 Testing

The project currently uses manual functional testing for the web application.

Key areas to test include:

User registration

User login/logout

Role-based permissions

Dashboard loading

Climate data endpoints

MapReduce execution

ML predictions

Real-time telemetry

Alert generation

Support ticket functionality

🔒 Security

Sensitive local configuration is excluded from version control.

The following types of files are ignored:

.env
*.db
.venv/
__pycache__/

Never commit:

Database credentials

Production secrets

Private API keys

Local environment configuration

Authentication secrets

For production deployments, secrets should be managed through environment variables or a dedicated secret-management service.

📊 Machine Learning Results

The project includes trained models for:

Temperature Forecasting

A Gradient Boosting regression pipeline is used to predict temperature behavior from engineered climate features.

Anomaly Detection

An Isolation Forest pipeline with RobustScaler is used to identify unusual climate observations.

Climate Impact Prediction

A Random Forest regression pipeline provides climate vulnerability / impact scoring based on environmental features.

Model artifacts and evaluation reports are maintained in the models/ directory.

🎯 Project Goals

The main goals of this project are to demonstrate practical understanding of:

Data Science

Machine Learning

Data Engineering

Big Data concepts

Distributed data processing

REST API development

Database integration

Authentication and authorization

Data visualization

Software architecture

Git and GitHub workflows

📌 Project Status

Completed — Portfolio Project

The application is currently maintained as a local development and portfolio project.

The project demonstrates an end-to-end workflow from raw climate data ingestion to processing, machine-learning analysis, API delivery, and interactive visualization.

📄 License

This project is licensed under the MIT License.

See the LICENSE file for the complete license terms.

⭐ Repository

If you find this project interesting, feel free to explore the source code and follow my GitHub profile for more projects.