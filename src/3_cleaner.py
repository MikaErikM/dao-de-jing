import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime
import logging
import os
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    print(f"Warning: NLTK download failed: {e}")

# Configuration constants
LOG_DIR = "../logs/cleaning"
CONFIG = {
    'log_level': logging.WARNING,
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

def setup_logging():
    """Sets up error-focused logging configuration."""
    expanded_log_dir = os.path.expandvars(os.path.expanduser(LOG_DIR))
    os.makedirs(expanded_log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(expanded_log_dir, f'cleaning_log_{timestamp}.log')

    logging.basicConfig(
        level=CONFIG['log_level'],
        format=CONFIG['log_format'],
        datefmt=CONFIG['date_format'],
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_file

def clean_text(row):
    """Clean translation text using extended rules."""
    try:
        text = row['text']
        chapter_num = row['chapter']
        
        # Original cleaning steps
        excerpt_text = "Here are some tantalizing excerpts from the newest computer-assisted translation of Lao Tzu's famous"
        excerpt_pos = text.find(excerpt_text)
        if excerpt_pos != -1:
            text = text[:excerpt_pos]
            logging.debug(f"Removed excerpt text in chapter {chapter_num}")
        
        text = re.sub(r'-{10,}.*$', '', text)
        
        next_chapter = str(chapter_num + 1)
        next_chapter_pos = text.find(next_chapter)
        if next_chapter_pos != -1:
            text = text[:next_chapter_pos]
            logging.debug(f"Removed next chapter content in chapter {chapter_num}")
        
        # Basic cleaning
        text = re.sub(r'[\u4e00-\u9fff]+', '', text)  # Chinese characters
        text = re.sub(r'[¶†‡§]+', '', text)  # Sentence markers
        text = re.sub(r'\s*\[MODULE:FOOTER\].*$', '', text)
        text = text.encode('ascii', 'ignore').decode()
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove 'up' from end
        last_ten = text[-10:] if len(text) >= 10 else text
        up_pos = last_ten.lower().find('up')
        if up_pos != -1:
            text = text[:-(10-up_pos)]
            logging.debug(f"Removed trailing 'up' in chapter {chapter_num}")
        
        # Additional NLTK cleaning
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # General cleanup
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
        text = re.sub(r'[""'']', '', text)  # Remove smart quotes
        text = re.sub(r'[–—]', '-', text)  # Normalize dashes
        
        return text.strip()
    except Exception as e:
        logging.error(f"Error cleaning text for chapter {row.get('chapter', 'unknown')}: {str(e)}")
        return row['text']

def process_translations(input_path):
    """Process and clean translation data."""
    try:
        logging.info(f"Loading data from {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rows = []
        for translation in data['translations']:
            translator = translation['translation_name']
            url = translation['url']
            scrape_time = translation['timestamp']
            
            for chapter_num, text in translation['chapters'].items():
                # Create a dictionary with both original and cleaned text
                row_data = {
                    'translator': translator,
                    'url': url,
                    'scrape_time': scrape_time,
                    'chapter': int(chapter_num),
                    'original_text': text,  # Keep original text
                    'text': text  # This will be cleaned
                }
                rows.append(row_data)

        df = pd.DataFrame(rows)
        logging.info(f"Loaded {len(data['translations'])} translations with shape {df.shape}")
        
        # Clean the text column while preserving original_text
        df['cleaned_text'] = df.apply(clean_text, axis=1)
        
        # Add length columns
        df['original_length'] = df['original_text'].str.len()
        df['cleaned_length'] = df['cleaned_text'].str.len()
        
        return df

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error processing translations: {str(e)}", exc_info=True)
        return None

def print_statistics(df):
    """Print statistical analysis of the data."""
    if df is None:
        logging.error("Cannot print statistics: DataFrame is None")
        return

    print("\nText Length Statistics:")
    print("-" * 50)
    print("Original Text:")
    print(df['original_length'].describe())
    print("\nCleaned Text:")
    print(df['cleaned_length'].describe())

def print_outliers(df, title):
    """Print outlier analysis."""
    if df is None:
        logging.error(f"Cannot print outliers for {title}: DataFrame is None")
        return

    for text_type in ['original', 'cleaned']:
        length_col = f'{text_type}_length'
        text_col = f'{text_type}_text'
        
        mean_len = df[length_col].mean()
        std_len = df[length_col].std()
        outliers = df[abs(df[length_col] - mean_len) > 2 * std_len]
        
        print(f"\n{title} Outliers for {text_type.title()} Text (>2 standard deviations from mean):")
        print("-" * 80)
        print("\nShortest outliers:")
        print(outliers.nsmallest(5, length_col)[['translator', 'chapter', length_col, text_col]])
        print("\nLongest outliers:")
        print(outliers.nlargest(5, length_col)[['translator', 'chapter', length_col, text_col]])

def calculate_text_stats(df):
    """Calculate statistics about the text cleaning."""
    try:
        stats = {
            'total_translations': len(df['translator'].unique()),
            'total_chapters': len(df['chapter'].unique()),
            'avg_length_original': df['original_length'].mean(),
            'avg_length_cleaned': df['cleaned_length'].mean(),
            'reduction_percentage': ((df['original_length'].sum() - df['cleaned_length'].sum()) / 
                                   df['original_length'].sum() * 100),
            'min_length_original': df['original_length'].min(),
            'min_length_cleaned': df['cleaned_length'].min(),
            'max_length_original': df['original_length'].max(),
            'max_length_cleaned': df['cleaned_length'].max()
        }
        return stats
    except Exception as e:
        logging.error(f"Error calculating text statistics: {str(e)}")
        return None

if __name__ == "__main__":
    log_file = setup_logging()
    
    input_path = '../data/raw/merged/merged.json'
    output_path = '../data/processed'
    
    if not os.path.exists(input_path):
        logging.error(f"Input file not found: {input_path}")
        exit(1)
    
    os.makedirs(output_path, exist_ok=True)
    
    df = process_translations(input_path)
    
    if df is not None:
        # Print analysis
        print_statistics(df)
        print_outliers(df, "Text Data")
        
        # Calculate and print text cleaning stats
        stats = calculate_text_stats(df)
        if stats:
            print("\nText Cleaning Statistics:")
            print("-" * 50)
            for key, value in stats.items():
                if 'percentage' in key:
                    print(f"{key}: {value:.2f}%")
                else:
                    print(f"{key}: {value:.2f}")
        
        # Export cleaned data
        output_file = os.path.join(output_path, f'cleaned_data.xlsx')
        
        try:
            df.sort_values(['translator', 'chapter']).to_excel(
                output_file,
                columns=['translator', 'chapter', 'original_text', 'cleaned_text', 
                        'original_length', 'cleaned_length', 'url', 'scrape_time']
            )
            print(f"\nData saved to: {output_file}")
            logging.info(f"Successfully exported data to {output_file}")
        except Exception as e:
            logging.error(f"Error saving output file: {str(e)}")
    else:
        logging.error("Failed to process translations")
        exit(1)
