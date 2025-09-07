#!/bin/bash
pip install -r requirements.txt
pyinstaller --noconsole \
 --add-data "materials:materials" \
 --add-data "kips.json:." \
 --add-data "back1.png:." \
 main.py
