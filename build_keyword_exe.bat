@echo off
REM Build KeywordNewsCrawler.exe (runs on PCs without Python)
REM Requires: pip install pyinstaller requests beautifulsoup4 PyQt6 openpyxl
REM Output: dist\KeywordNewsCrawler.exe

cd /d "%~dp0"

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name KeywordNewsCrawler ^
  --icon detective.ico ^
  --add-data "detective.ico;." ^
  --exclude-module PySide6 ^
  --exclude-module matplotlib ^
  --exclude-module pandas ^
  --exclude-module numpy ^
  --exclude-module scipy ^
  --exclude-module IPython ^
  --exclude-module tkinter ^
  naver_keyword_news_crawler.py

echo.
echo Build done: dist\KeywordNewsCrawler.exe
