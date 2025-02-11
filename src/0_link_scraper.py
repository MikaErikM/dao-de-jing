import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import logging
import os
from datetime import datetime

# Configuration constants
LOG_DIR = "../logs/scraping/link_scraper"
CONFIG = {
    'log_level': logging.WARNING,  # Changed to WARNING level
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

    # Configure logging
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

def scrape_table_data(url):
    """
    Scrapes data from a specific table on a given URL, processes links and content.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        dict: Dictionary containing scraped data with translations
        None: If scraping fails or table is not found
    """
    try:
        # Fetch and parse webpage
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find target table
        target_table = soup.find('table', attrs={
            'border': '0',
            'cellspacing': '0',
            'cellpadding': '0',
            'width': '100%'
        })

        if not target_table:
            logging.error('Target table not found in HTML content')
            return None

        # Extract data
        base_url = urljoin(url, '.')
        table_data = {"translations": []}
        rows = target_table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                for p_tag in cell.find_all('p'):
                    link_tag = p_tag.find('a')
                    
                    if link_tag:
                        translation_name = link_tag.text.strip()
                        relative_link = link_tag.get('href')
                        absolute_link = urljoin(base_url, relative_link)
                        is_pdf = absolute_link.lower().endswith(".pdf")
                        
                        table_data["translations"].append({
                            "name": translation_name,
                            "link": absolute_link,
                            "is_pdf": is_pdf
                        })
                    else:
                        text_content = p_tag.text.strip()
                        if text_content:
                            table_data["translations"].append({
                                "name": text_content,
                                "link": None,
                                "is_pdf": False
                            })

        return table_data

    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to fetch URL {url}: {str(e)}')
        return None
    except Exception as e:
        logging.error(f'Unexpected error during scraping: {str(e)}', exc_info=True)
        return None

if __name__ == "__main__":
    # Initialize logging
    log_file = setup_logging()
    target_url = "https://terebess.hu/english/tao/_index.html"
    
    scraped_data = scrape_table_data(target_url)

    if scraped_data:
        # Save results to JSON file
        output_file = "../data/raw/scraped/links.json"
        try:
            json_output = json.dumps(scraped_data, indent=4, ensure_ascii=False)
            with open(output_file, "w", encoding="utf-8") as outfile:
                outfile.write(json_output)
            print(f"Data saved to {output_file}")
        except Exception as e:
            logging.error(f'Failed to save output file: {str(e)}')
    else:
        logging.error('Scraping operation failed')