#!/bin/bash
pip install -r requirements.txt
pyinstaller --onefile --noconsole --add-data "materials:materials" --add-data "kips.json:." main.py