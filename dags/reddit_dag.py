import os
import praw
import smtplib
import pandas as pd
from airflow.decorators import dag, task
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.extract import clean_text
from sqlalchemy import create_engine

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
DB_URL = os.getenv("DB_URL")

default_args = {
    'owner': 'Denzel Kinyua',
    'retries': 5,
    'retry_delay': timedelta(minutes=10),
    'start_date': datetime(2025, 9, 16)
}

@dag(dag_id='reddit_data_pipeline', default_args=default_args, schedule_interval='@daily', catchup=False)
def reddit_analysis_dag():
    @task
    def extract_data():
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=SECRET_KEY,
            user_agent='data pipeline by u/user'
        )

        limit = 50
        data = []
        subs = ["kenya", "nairobi"]
        for sub in subs:
            subreddit = reddit.subreddit(sub)
            for s in subreddit.top(time_filter='day', limit=limit):
                data.append({
                    'id': s.id,
                    'title': clean_text(s.title) if s.title else 'N/A',
                    'text': clean_text(s.selftext) if s.selftext else 'N/A',
                    'url': s.url,
                    'score': s.score,
                    'subreddit': sub,
                    'time_created': s.created_utc
                })

        return data
    
    @task
    def transform_data(data):
        df = pd.DataFrame(data)
        df["time_created"] = pd.to_datetime(df["time_created"].astype(float), unit='s', origin='unix')
        engine = create_engine(DB_URL)

        try:
            df.to_sql(name='reddit_posts', con=engine, schema='reddit', if_exists='append', index=False) # change if_exists to 'append'
            return "Data loaded successfully!"
        except Exception as e:
            print(f"Error loading data to db: {e}")
            raise

    @task
    def send_email(message):
        try:
            subject = 'DAG Run Complete'
            body = f"""
                    DAG Run complete: {message}
                    Please go to the Airflow UI to check the pipeline out
                """
            sender = os.getenv("SENDER")
            receiver = os.getenv("RECIPIENT") 
            password = os.getenv("EMAIL_PWD")

            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = receiver
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            # SSL connection (port 465)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())

            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise
    
    data = extract_data()
    message = transform_data(data)
    email = send_email(message)

    data >> message >> email

reddit_dag = reddit_analysis_dag()