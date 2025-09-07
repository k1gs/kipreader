#!/bin/bash
pip install -r requirements.txt
pyinstaller -i icon.ico --onefile --noconsole --add-data "materials:materials" --add-data "kips.json:." main.py
