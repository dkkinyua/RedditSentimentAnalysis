import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import smtplib
import numpy as np
import pandas as pd
from airflow.decorators import dag, task
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from utils.extract import get_sentiment

load_dotenv()
DB_URL = os.getenv("DB_URL")
SENDER = os.getenv("SENDER")
RECIPIENT = os.getenv("RECIPIENT")
EMAIL_PWD = os.getenv("EMAIL_PWD")

default_args = {
    "owner": "Denzel Kinyua",
    "retries": 5,
    "retry_delay": timedelta(minutes=10),
    "start_date": datetime(2025, 8, 27),
}

@dag(
    dag_id="reddit_sentiment_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["reddit", "sentiment", "nlp"],
)
def analyze_dag():
    @task
    def analyze_text():
        """fetch posts from Postgres, analyze sentiment, and save results back to a different psql table."""
        engine = create_engine(DB_URL)
        analyzer = SentimentIntensityAnalyzer()

        try:
            # Load from DB
            df = pd.read_sql_table("reddit_posts", con=engine, schema="reddit")

            # Clean text off the N/A tags
            df["text"] = df["text"].replace("N/A", np.nan)
            df.dropna(subset=["text"], inplace=True)

            # Apply sentiment
            scores = df["text"].apply(lambda x: analyzer.polarity_scores(x))
            df["compound"] = scores.apply(lambda x: x["compound"])
            df["neg"] = scores.apply(lambda x: x["neg"])
            df["neu"] = scores.apply(lambda x: x["neu"])
            df["pos"] = scores.apply(lambda x: x["pos"])
            df["sentiment"] = df["compound"].apply(get_sentiment)

            # Save results
            df.to_sql(
                "reddit_sentiment_analysis",
                con=engine,
                schema="reddit",
                if_exists="append",
                index=False,
            )
            return "Data loaded successfully!"
        except Exception as e:
            raise RuntimeError(f"Error analyzing or saving data: {e}")

    @task
    def send_email(message: str):
        """Send a notification email with DAG run results."""
        try:
            subject = "DAG Run Complete"
            body = f"""
            DAG Run complete: {message}
            Please go to the Airflow UI to check the pipeline.
            """

            msg = MIMEMultipart()
            msg["From"] = SENDER
            msg["To"] = RECIPIENT
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER, EMAIL_PWD)
                server.sendmail(SENDER, RECIPIENT, msg.as_string())

            print("Email sent successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to send email: {e}")

    message = analyze_text()
    email = send_email(message)

    message >> email

analyze = analyze_dag()
