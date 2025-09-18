# Reddit Sentiment Analysis Pipeline

This project implements a data pipeline that extracts Reddit posts, performs sentiment analysis, stores results in PostgreSQL, and visualizes insights using Grafana.
The pipeline is orchestrated with Apache Airflow and containerized with Docker Compose for reproducibility. It also integrates Prometheus + Grafana for monitoring.
It uses the `statsd-exporter` to collect Airflow metrics and exposes them to Prometheus, which Grafana then visualizes in a dashboard.

# Main Features
- Data Extraction: Collects Reddit posts using the praw API.

- Data Transformation: Cleans text and computes sentiment scores using VADER (NLTK).

- Data Loading: Stores structured results into a PostgreSQL database.

- Orchestration: Managed with Apache Airflow DAGs.

    - reddit_dag: Fetches and stores fresh Reddit posts.

    - analysis_dag: Performs sentiment analysis after reddit_dag completes.

- Monitoring: Grafana dashboards for real-time insights and Prometheus for metrics and health monitoring.

- Alerts: Email notifications on DAG failures via SMTP.

## Project File Structure and Architecture

```bash
.
├── dags/
│   ├── reddit_dag.py         
│   ├── analysis_dag.py  
│   │── test_dag.py
│   └── utils/             
├── logs/                     
├── plugins/
├── config/                  
├── docker-compose.yml 
├── prometheus.yml       
├── requirements.txt  
├── Dockerfile        
├── dashboard.json    
└── README.md                
```

![Architecture](https://res.cloudinary.com/depbmpoam/image/upload/v1758199956/Untitled_8_odnzlx.jpg)

## Project Setup
### 1. Clone this repository
```bash
git clone https://github.com/dkkinyua/RedditSentimentAnalysis
```

### 2. Setup Python environment and install dependencies

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 3. Run Docker services

```bash
docker compose up --build
```
Run with `--build` flag to build our custom Dockerfile image.
Access the following services at the following ports:
- Airflow: `http:localhost:8080`
- Prometheus: `http:localhost:9090`
- StatsD: `http:localhost:9102`
- Grafana: `http://localhost:3000`

## Airflow Cross DAG Dependencies
For this project, there's need for cross DAG dependencies between `reddit_dag` and `analyze_dag`. `reddit_dag` extracts, transforms and loads data into Postgres. `analyze_dag` loads data from Postgres and analyzes sentiment data using VADER

`ExternalTaskSensor` from `airflow.sensors.external_task` helps us achieve this. `ExternalTaskSensor` pokes the previous DAG run, `reddit_dag` to check if it is successful for `analyze_dag` to start running automatically.

```python
from airflow.sensors.external_task import ExternalTaskSensor

@dag(...)
def analyze_dag():
    wait_task = ExternalTaskSensor(
        task_id = 'wait_for_extraction',
        external_dag_id = 'reddit_data_pipeline',
        external_task_id = None, 
        mode = 'poke',
        poke_interval = 60,
        timeout = 3600
    )
```

## Grafana Analysis and Metric dashboards

The analysis dashboard is hosted on Grafana Cloud, the metrics dashboard is hosted on the Grafana service available at `http://localhost:3000.

The metric dashboard is available in the `dashboard.json` file. Add it in the Import section in Grafana

![Analytics dashboard](https://res.cloudinary.com/depbmpoam/image/upload/v1758206990/Screenshot_2025-09-18_152532_pudlww.png)

![Metrics dashboard](https://res.cloudinary.com/depbmpoam/image/upload/v1758206990/Screenshot_2025-09-18_152612_i9fhpj.png)

## Contributions
Request a pull request for contibutions

