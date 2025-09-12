import html
import praw
import re
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
DB_URL = os.getenv("DB_URL")

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=SECRET_KEY,
    user_agent='data pipeline by u/user'
)

subreddit = reddit.subreddit("kenya+nairobi")
limit = 100
data = []

'''
1. Extract data from the reddit.Subreddit instance with a limit of 100 messages/day
2. Return the extracted data in a list
3. Transform the data. Change the post_date from a string into a pd.Datetime object
4. Load the data into a PostgreSQL database. This database holds semi-structured data for sentiment analysis
5. These functions will later be exported to Airflow DAG for orchestration

'''

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F" 
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF" 
        "\U0001F1E0-\U0001F1FF"  
        "\U00002700-\U000027BF" 
        "\U000024C2-\U0001F251"  
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def clean_text(text):
    text = html.unescape(text)
    text = text.replace('\r', '').replace('\n', ' ').replace('\t', ' ')
    text = text.replace('\u00a0', ' ').replace('\u2019', ' ').replace('\u2023', ' ').replace('\u2013', ' ')
    text = remove_emojis(text) 
    text = ' '.join(text.split())
    return text.strip()

def extract_data(subreddit, limit):
    for s in subreddit.top(time_filter='day', limit=limit):
        data.append({
            'id': s.id,
            'title': clean_text(s.title) if s.title else 'N/A',
            'text': clean_text(s.selftext) if s.selftext else 'N/A',
            'url': s.url,
            'score': s.score,
            'author': s.author.name if s.author else None,
            'author_karma': s.author.link_karma if s.author else None,
            'time_created': s.created_utc
        })

        return data
    
def transform_data(data):
    df = pd.DataFrame(data)
    df["time_created"] = pd.to_datetime(df["time_created"].astype(float), unit='s', origin='unix')
    engine = create_engine(DB_URL)

    try:
        df.to_sql(name='reddit_posts', con=engine, schema='reddit', if_exists='replace', index=False) # change if_exists to 'append'
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data to db: {e}")

