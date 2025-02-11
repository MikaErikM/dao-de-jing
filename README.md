# Comparative Analysis of English Language Translations of the Daodejing/Tao Te King (道德经)

This project analyzes English language translations of the Daodejing using data from terebess.hu/english/tao/_index.html

## Setup and Usage
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix/macOS
.\venv\Scripts\activate   # Windows

pip install -r requirements.txt
python3 run.py
```

The script downloads translation links, extracts content by chapter, and cleans the data for analysis in Jupyter Notebook.

After creating the file - move to the Notebook for further analysis.

## Project Context
The Daodejing is a significant but concise text (~5,000 characters) with numerous English translations. This project currently includes about 60 translations, creating a foundation for analyzing:
- Differences between translations
- Areas of translator disagreement
- Changes in translation approaches over time

## Next Steps
- Add metadata (year and translator name)
- Include additional translations
- Expand the analysis
