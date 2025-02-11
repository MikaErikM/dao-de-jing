import json
import os
from datetime import datetime

def merge_translation_files(main_file, additional_folder, output_file):
    """
    Merge translations from a main JSON file and additional JSON files in a folder.
    
    Args:
        main_file (str): Path to the main translations JSON file
        additional_folder (str): Path to folder containing additional JSON files
    """
    try:
        # Initialize merged data structure
        merged_data = {
            "scrape_timestamp": datetime.now().isoformat(),
            "translations": []
        }
        
        # Load main file
        with open(main_file, 'r', encoding='utf-8') as f:
            main_data = json.load(f)
            if "translations" in main_data:
                merged_data["translations"].extend(main_data["translations"])
                print(f"Added translations from main file: {main_file}")
        
        # Process additional files from folder
        if os.path.isdir(additional_folder):
            for filename in os.listdir(additional_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(additional_folder, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict) and "chapters" in data:
                                # Single translation file
                                merged_data["translations"].append(data)
                                print(f"Added translation from {filename}")
                            elif "translations" in data:
                                # Multiple translations file
                                merged_data["translations"].extend(data["translations"])
                                print(f"Added translations from {filename}")
                    except json.JSONDecodeError:
                        print(f"Skipping {filename}: Invalid JSON format")
                    except Exception as e:
                        print(f"Error processing {filename}: {str(e)}")
        
        # Save merged data
        if merged_data["translations"]:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully merged {len(merged_data['translations'])} translations to {output_file}")
            return output_file
        else:
            print("No translations were found to merge")
            return None
            
    except Exception as e:
        print(f"Unexpected error during merge: {str(e)}")
        return None

if __name__ == "__main__":
    main_file = "../data/raw/scraped/chapters.json"
    additional_folder = "../data/raw/manual"
    output_file = "../data/raw/merged/merged.json"
    
    if not os.path.exists(main_file):
        print(f"Main file not found: {main_file}")
        exit(1)
        
    if not os.path.exists(additional_folder):
        print(f"Additional translations folder not found: {additional_folder}")
        exit(1)
        
    merge_translation_files(main_file, additional_folder, output_file)