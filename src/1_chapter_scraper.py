import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import os
import re
from urllib.parse import urlparse

# Configuration constants
LOG_DIR = "../logs/scraping/chapter_scraper"
CONFIG = {
    'log_level': logging.WARNING,
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

def setup_logging():
    """
    Sets up error-focused logging configuration.
    Creates log directory if it doesn't exist.
    """
    expanded_log_dir = os.path.expandvars(os.path.expanduser(LOG_DIR))
    os.makedirs(expanded_log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(expanded_log_dir, f'scraper_errors_{timestamp}.log')

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

def is_valid_url(url):
    """Check if URL is a non-PDF terebess.hu link"""
    try:
        parsed = urlparse(url)
        return (
            "terebess.hu" in parsed.netloc.lower() and
            not url.lower().endswith('.pdf')
        )
    except:
        return False

def scrape_chapters_by_links_to_json(url, translation_name):
    """
    Scrape chapters from a single translation URL.
    Returns a dictionary with the scraped data or None if scraping fails.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        chapters = {}
        chapter_links = soup.select('a[href^="#Kap"]')
        
        if not chapter_links:
            logging.error(f"No chapter links found for translation: {translation_name}")
            return None
        
        # Create chapter boundaries
        chapter_boundaries = []
        for link in chapter_links:
            chapter_id = link['href'].lstrip('#')
            anchor = soup.find('a', {'name': chapter_id})
            if anchor:
                parent_text = anchor.parent.get_text()
                number_match = re.search(r'\b(\d+)\b', parent_text)
                if number_match:
                    chapter_boundaries.append({
                        'number': number_match.group(1),
                        'anchor': anchor,
                        'id': chapter_id
                    })
        
        # Sort boundaries by position
        chapter_boundaries.sort(key=lambda x: str(x['anchor']))
        
        # Extract content between boundaries
        for i in range(len(chapter_boundaries)):
            current = chapter_boundaries[i]
            chapter_num = current['number']
            start_anchor = current['anchor']
            end_anchor = chapter_boundaries[i + 1]['anchor'] if i + 1 < len(chapter_boundaries) else None
            
            content_parts = []
            current_element = start_anchor
            
            while current_element and current_element != end_anchor:
                if isinstance(current_element, str) and current_element.strip():
                    content_parts.append(current_element.strip())
                
                next_element = current_element.next_element
                if not next_element or (end_anchor and next_element == end_anchor):
                    break
                current_element = next_element
            
            chapter_text = ' '.join(content_parts)
            chapter_text = re.sub(f'^{chapter_num}\\s*', '', chapter_text)
            chapter_text = re.sub(r'\s+', ' ', chapter_text).strip()
            
            if chapter_text:
                chapters[chapter_num] = chapter_text
        
        sorted_chapters = dict(sorted(chapters.items(), key=lambda x: int(x[0])))
        
        if not sorted_chapters:
            logging.error(f"No chapter content extracted for translation: {translation_name}")
            return None
            
        return {
            "translation_name": translation_name,
            "url": url,
            "chapters": sorted_chapters,
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error scraping {translation_name} from {url}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error scraping {translation_name}: {str(e)}", exc_info=True)
        return None

def process_translations(input_file, output_file):
    """
    Process multiple translations from a JSON input file.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        valid_translations = [
            t for t in data["translations"]
            if not t["is_pdf"] and is_valid_url(t["link"])
        ]
        
        if not valid_translations:
            logging.error("No valid translations found to process")
            return None
        
        results = []
        for translation in valid_translations:
            result = scrape_chapters_by_links_to_json(
                translation["link"],
                translation["name"]
            )
            if result:
                results.append(result)
        
        if not results:
            logging.error("No translations were successfully scraped")
            return None
        
        output_data = {
            "scrape_timestamp": datetime.now().isoformat(),
            "translations": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully scraped {len(results)} translations")
        return output_file
        
    except json.JSONDecodeError as e:
        logging.error(f"Error reading input file {input_file}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing translations: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    # Set up logging
    log_file = setup_logging()

    # Define input/output paths 
    input_file = "../data/raw/scraped/links.json"
    output_file = "../data/raw/scraped/chapters.json"
    
    # Process translations
    result_file = process_translations(input_file, output_file)
    
    if result_file:
        print(f"Scraping complete. Results saved to: {output_file}")
        print(f"Error log created at: {log_file}")
    else:
        print("Error during scraping. Check the log file for details.")