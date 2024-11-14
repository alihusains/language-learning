import os
import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Setup output directory
os.makedirs("output", exist_ok=True)

# Environment Config
languages = os.getenv("LANGUAGES").split(",")
base_date = datetime(2013, 9, 2)
today = datetime.now()

def fetch_word_of_the_day(language, date):
    url = f'https://{language.lower()}pod101.com/api/word-day/{date}'
    headers = {
        'accept': '*/*',
        'accept-language': 'en',
        'user-agent': 'Mozilla/5.0',
        'x-requested-with': 'XMLHttpRequest'
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def save_to_csv(data, examples, language):
    # Save word data
    word_df = pd.DataFrame(data)
    word_df.to_csv(f"output/{language.lower()}.csv", index=False)

    # Save examples data
    example_df = pd.DataFrame(examples)
    example_df.to_csv(f"output/{language.lower()}-examples.csv", index=False)

def save_to_sqlite(data, examples, language):
    db_path = f"output/{language.lower()}.sqlite"
    conn = sqlite3.connect(db_path)

    # Save words
    word_df = pd.DataFrame(data)
    word_df.to_sql("words", conn, if_exists="replace", index=False)

    # Save examples
    example_df = pd.DataFrame(examples)
    example_df.to_sql("examples", conn, if_exists="replace", index=False)

    conn.close()

def main():
    all_words = []
    all_examples = []

    for language in languages:
        word_data = []
        example_data = []
        date = base_date

        while date <= today:
            date_str = date.strftime('%Y-%m-%d')
            response = fetch_word_of_the_day(language, date_str)

            if response and response['status'] == 'success':
                word_day = response['payload']['word_day']
                word_data.append({
                    "Date": date_str,
                    "Dictionary ID": word_day['dictionary_id'],
                    "Flashcard ID": word_day['flashcard_id'],
                    "Word": word_day['text'],
                    "English": word_day['english'],
                    "Meaning": word_day['meaning'],
                    "Class": word_day['class'],
                    "Gender": word_day['gender'],
                    "Romanization": word_day['romanization'],
                    "Vowelled": word_day['vowelled'],
                    "Audio Target": word_day['audio_target'],
                    "Audio English": word_day['audio_english'],
                    "Image URL": word_day['image_url']
                })

                # Add examples
                for sample in word_day.get('samples', []):
                    example_data.append({
                        "Date": date_str,
                        "Dictionary ID": word_day['dictionary_id'],
                        "Example Text": sample['text'],
                        "Example English": sample['english'],
                        "Example Romanization": sample['romanization'],
                        "Example Vowelled": sample['vowelled'],
                        "Audio Target": sample['audio_target'],
                        "Audio English": sample['audio_english']
                    })

            date += timedelta(days=1)

        # Save to CSV and SQLite for the current language
        save_to_csv(word_data, example_data, language)
        save_to_sqlite(word_data, example_data, language)

        # Append to combined data
        all_words.extend(word_data)
        all_examples.extend(example_data)

    # Save combined data to a single SQLite
    conn = sqlite3.connect("output/all_languages.sqlite")
    pd.DataFrame(all_words).to_sql("words", conn, if_exists="replace", index=False)
    pd.DataFrame(all_examples).to_sql("examples", conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    main()
