@echo off
REM 
pip install -r requirements.txt

REM 
pyinstaller --onefile --noconsole ^
 --add-data "materials;materials" ^
 --add-data "kips.json;." ^
 --add-data "back1.png;."

pause