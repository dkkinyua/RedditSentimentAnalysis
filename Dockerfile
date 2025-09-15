FROM apache/airflow:2.10.5-python3.10
# run as root to first install packages then switch to Airflow
USER root 

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# switch to airflow to build image
USER airflow
WORKDIR /opt/airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt