import requests
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

# Set output directory
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# List of languages
languages = os.getenv("LANGUAGES").split(',')

# Base URL template
base_url_template = "https://{language}pod101.com/api/word-day/{date}"

# Function to fetch data for a given language and date
def fetch_data(language, date):
    url = base_url_template.format(language=language, date=date)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for {language} on {date}")
        return None

# Main function
def main():
    current_date = datetime.today()
    start_date = datetime(2013, 9, 2)
    
    # Loop through languages
    for language in languages:
        word_data = []
        examples_data = []
        
        # Loop through dates from start_date to current_date
        date = start_date
        while date <= current_date:
            formatted_date = date.strftime("%Y-%m-%d")
            data = fetch_data(language, formatted_date)
            
            if data and data.get("status") == "success":
                word_day = data["payload"]["word_day"]
                
                # Append word of the day data with missing field handling
                word_entry = {
                    "Date": formatted_date,
                    "Dictionary ID": word_day.get("dictionary_id", ""),
                    "Flashcard ID": word_day.get("flashcard_id", ""),
                    "Text": word_day.get("text", ""),
                    "Audio Target": word_day.get("audio_target", ""),
                    "Audio English": word_day.get("audio_english", ""),
                    "Image URL": word_day.get("image_url", ""),
                    "English": word_day.get("english", ""),
                    "Meaning": word_day.get("meaning", ""),
                    "Class": word_day.get("class", ""),
                    "Gender": word_day.get("gender", ""),  # Default to empty string if missing
                    "Romanization": word_day.get("romanization", ""),
                    "Vowelled": word_day.get("vowelled", "")
                }
                word_data.append(word_entry)
                
                # Append examples with missing field handling
                for example in word_day.get("samples", []):
                    example_entry = {
                        "Date": formatted_date,
                        "Dictionary ID": word_day.get("dictionary_id", ""),
                        "Text": example.get("text", ""),
                        "Audio Target": example.get("audio_target", ""),
                        "Audio English": example.get("audio_english", ""),
                        "English": example.get("english", ""),
                        "Romanization": example.get("romanization", ""),  # Set a default value
                        "Vowelled": example.get("vowelled", "")
                    }
                    examples_data.append(example_entry)
                    
            date += timedelta(days=1)
        
        # Save to CSV
        word_df = pd.DataFrame(word_data)
        examples_df = pd.DataFrame(examples_data)
        
        word_csv_path = os.path.join(output_dir, f"{language.lower()}.csv")
        examples_csv_path = os.path.join(output_dir, f"{language.lower()}-examples.csv")
        word_df.to_csv(word_csv_path, index=False)
        examples_df.to_csv(examples_csv_path, index=False)
        
        # Save to SQLite
        sqlite_path = os.path.join(output_dir, f"{language.lower()}.sqlite")
        with sqlite3.connect(sqlite_path) as conn:
            word_df.to_sql(f"{language.lower()}", conn, if_exists="replace", index=False)
            examples_df.to_sql(f"{language.lower()}_examples", conn, if_exists="replace", index=False)

    # Combine all languages into one SQLite file
    combined_sqlite_path = os.path.join(output_dir, "all_languages.sqlite")
    with sqlite3.connect(combined_sqlite_path) as combined_conn:
        for language in languages:
            language_name = language.lower()
            word_df = pd.read_csv(os.path.join(output_dir, f"{language_name}.csv"))
            examples_df = pd.read_csv(os.path.join(output_dir, f"{language_name}-examples.csv"))
            
            word_df.to_sql(f"{language_name}", combined_conn, if_exists="replace", index=False)
            examples_df.to_sql(f"{language_name}_examples", combined_conn, if_exists="replace", index=False)

if __name__ == "__main__":
    main()
