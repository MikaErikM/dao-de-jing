#run.py

import os
import subprocess

def run_scripts_in_folder(folder_path, script_names):
    """
    Navigate to the specified folder and run several scripts.

    Parameters:
    - folder_path: The path to the folder containing the scripts.
    - script_names: A list of script names (with extensions) to be executed.
    """
    try:
        # Change the current working directory to the specified folder
        os.chdir(folder_path)
        print(f"Changed directory to {folder_path}")

        # Run each script in the list
        for script in script_names:
            if os.path.exists(script):
                print(f"Running script: {script}")
                result = subprocess.run(["python", script], capture_output=True, text=True)

                # Print the output and errors, if any
                if result.stdout:
                    print(f"Output of {script}:\n{result.stdout}")
                if result.stderr:
                    print(f"Errors from {script}:\n{result.stderr}")
            else:
                print(f"Script {script} does not exist in the folder.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
folder_path = "src"
script_names = [
    "0_link_scraper.py", 
    "1_chapter_scraper.py", 
    "2_merge_manual_additions.py",
    "3_cleaner.py"
    ]
run_scripts_in_folder(folder_path, script_names)
