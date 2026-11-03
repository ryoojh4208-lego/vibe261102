@echo off
REM Build NewsDetective.exe (runs on PCs without Python)
REM Output: dist\NewsDetective.exe

cd /d "%~dp0"

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name NewsDetective ^
  --icon detective.ico ^
  --add-data "detective.ico;." ^
  --exclude-module PySide6 ^
  --exclude-module matplotlib ^
  --exclude-module pandas ^
  --exclude-module numpy ^
  --exclude-module scipy ^
  --exclude-module IPython ^
  --exclude-module tkinter ^
  naver_news_crawler.py

echo.
echo Build done: dist\NewsDetective.exe
