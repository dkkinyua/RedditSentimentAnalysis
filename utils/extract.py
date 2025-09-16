import html
import re
'''
These functions are utility functions
1. remove_emojis removes emojis from texts for analysis, some emojis might be misleading
2. clean_text removes unicode chars from text
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

def get_sentiment(x):
    if x >= 0.05:
        return "Positive"
    elif x <= -0.05:
        return "Negative"
    else:
        return "Neutral"
