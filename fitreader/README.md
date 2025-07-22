# Python Webapp for Garmin FIT File Parsing and Map Visualization

This project is a Python-based web application that uses the garmin-fit-sdk to parse FIT files and provides map visualization features.

## Features
- Upload and parse Garmin FIT files
- Visualize activity data on interactive maps

## Setup
1. Create a virtual environment:
   ```zsh
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```zsh
   pip install -r requirements.txt
   ```

## Run the App
```zsh
python app.py
```

## Dependencies
- Flask (web framework)
- garmin-fit-sdk (FIT file parsing)
- folium (map visualization)

## Notes
- Make sure to activate your virtual environment before running the app.
