"""
네이버 검색 결과에서 뉴스 기사를 찾아 본문까지 크롤링하는 GUI 앱
(requests + BeautifulSoup4 + PyQt6, 엑셀 저장은 openpyxl)

사용법:
    pip install requests beautifulsoup4 PyQt6 openpyxl
    python naver_news_crawler.py
"""
import csv
import html
import os
import re
import sys
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# 요청하신 URL (뉴스 탭 전체, query=아름다운가게)
SEARCH_URL = (
    "https://search.naver.com/search.naver?ssc=tab.news.all&where=news"
    "&sm=tab_jum&query={query}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.naver.com/",
}

# 네이버뉴스 기사 링크 형식: https://n.news.naver.com/mnews/article/{언론사}/{기사번호}
ARTICLE_RE = re.compile(r"https?://n\.news\.naver\.com/(?:mnews/)?article/\d+/\d+")

FIELDS = ["title", "press", "date", "url", "content"]

# 꼬마 탐정 컨셉 스타일 (남색 재킷 + 빨간 나비넥타이 + 크림색 수첩)
NAVY = "#1F3B73"
RED = "#E5383B"
CREAM = "#FFF8E7"
STYLE = f"""
QMainWindow, QWidget#central {{ background: {CREAM}; }}
QWidget {{ font-family: "Malgun Gothic"; font-size: 10pt; color: #2B2B2B; }}
QLabel#banner {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {NAVY}, stop:1 #3D5FA8);
    color: white; font-size: 17pt; font-weight: bold;
    border-radius: 18px; padding: 14px 20px;
}}
QLabel#subtitle {{ color: {NAVY}; font-size: 9pt; padding-left: 6px; }}
QLabel#status {{ color: {NAVY}; font-weight: bold; padding: 2px 6px; }}
QLineEdit {{
    background: white; border: 3px solid {NAVY}; border-radius: 16px;
    padding: 6px 14px; font-size: 11pt;
}}
QLineEdit:focus {{ border-color: {RED}; }}
QPushButton {{
    background: {NAVY}; color: white; border: none; border-radius: 16px;
    padding: 8px 16px; font-weight: bold;
}}
QPushButton:hover {{ background: #2E5299; }}
QPushButton:disabled {{ background: #C9CED9; color: #F2F2F2; }}
QPushButton#search {{ background: {RED}; }}
QPushButton#search:hover {{ background: #F25C5F; }}
QTableWidget {{
    background: white; alternate-background-color: #FFF1F1;
    border: 3px solid {NAVY}; border-radius: 14px; gridline-color: transparent;
    selection-background-color: #FFD6D7; selection-color: #2B2B2B;
}}
QHeaderView::section {{
    background: {NAVY}; color: white; font-weight: bold; border: none; padding: 6px;
}}
QTextBrowser {{
    background: white; border: 3px dashed {RED}; border-radius: 14px; padding: 8px;
}}
QProgressBar {{
    background: white; border: 2px solid {NAVY}; border-radius: 9px;
    height: 18px; text-align: center; color: {NAVY}; font-weight: bold;
}}
QProgressBar::chunk {{ background: {RED}; border-radius: 7px; }}
QSplitter::handle {{ background: transparent; height: 8px; }}
"""


# ---------------------------------------------------------------- 크롤링 로직
def get_soup(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def collect_article_links(query):
    """검색 결과 페이지에서 네이버뉴스 기사 링크를 중복 없이 수집"""
    links = []
    soup = get_soup(SEARCH_URL.format(query=quote(query)))
    for a in soup.find_all("a", href=True):
        m = ARTICLE_RE.match(a["href"])
        if m and m.group(0) not in links:
            links.append(m.group(0))
    return links


def parse_article(url):
    """네이버뉴스 기사 페이지에서 제목/언론사/날짜/본문 추출"""
    soup = get_soup(url)

    title = soup.select_one("#title_area, h2.media_end_head_headline")
    press = soup.select_one("a.media_end_head_top_logo img")
    date = soup.select_one("span.media_end_head_info_datestamp_time")
    body = soup.select_one("#dic_area, #newsct_article")

    if body:
        # 사진 설명, 스크립트 등 본문이 아닌 요소 제거
        for tag in body.select("script, style, em.img_desc, span.end_photo_org, div.ab_photo"):
            tag.decompose()
        content = re.sub(r"\n\s*\n+", "\n", body.get_text("\n", strip=True))
    else:
        content = ""

    return {
        "title": title.get_text(strip=True) if title else "",
        "press": press.get("alt", "") if press else "",
        "date": date.get("data-date-time", date.get_text(strip=True)) if date else "",
        "url": url,
        "content": content,
    }


def export_excel(articles, path):
    """수집한 기사를 서식이 적용된 엑셀(.xlsx) 파일로 저장"""
    wb = Workbook()
    ws = wb.active
    ws.title = "뉴스"

    headers = ["번호", "제목", "언론사", "날짜", "URL", "본문"]
    widths = [6, 50, 14, 20, 45, 100]
    ws.append(headers)
    for col, width in enumerate(widths, 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY.lstrip("#"))
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = width

    for i, a in enumerate(articles, 1):
        ws.append([i, a["title"], a["press"], a["date"], a["url"], a["content"]])
        row = i + 1
        url_cell = ws.cell(row=row, column=5)
        url_cell.hyperlink = a["url"]
        url_cell.style = "Hyperlink"
        for col in range(1, 7):
            # 본문은 줄바꿈 유지, 나머지는 위쪽 정렬
            ws.cell(row=row, column=col).alignment = Alignment(
                vertical="top", wrap_text=(col in (2, 6))
            )
        ws.row_dimensions[row].height = 90

    ws.freeze_panes = "A2"  # 머리글 고정
    ws.auto_filter.ref = ws.dimensions
    wb.save(path)


# ---------------------------------------------------------------- 작업 스레드
class CrawlWorker(QThread):
    """크롤링 중에도 화면이 멈추지 않도록 별도 스레드에서 실행"""

    found = pyqtSignal(int)              # 발견한 기사 수
    article = pyqtSignal(dict)           # 기사 1건 수집 완료
    progress = pyqtSignal(int, str)      # 진행 번호, 상태 메시지
    failed = pyqtSignal(str)             # 치명적 오류

    def __init__(self, query):
        super().__init__()
        self.query = query
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            links = collect_article_links(self.query)
        except requests.RequestException as e:
            self.failed.emit(f"검색 페이지를 가져오지 못했습니다.\n{e}")
            return

        self.found.emit(len(links))
        for i, url in enumerate(links, 1):
            if self._stop:
                break
            try:
                self.article.emit(parse_article(url))
                self.progress.emit(i, f"[{i}/{len(links)}] 수집 완료")
            except requests.RequestException as e:
                self.progress.emit(i, f"[{i}/{len(links)}] 실패: {e}")
            time.sleep(0.5)  # 서버 부담을 줄이기 위한 요청 간격


# ---------------------------------------------------------------- 메인 화면
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 꼬마 탐정 뉴스 수사대")
        self.resize(1100, 760)
        self.setStyleSheet(STYLE)
        self.articles = []
        self.worker = None

        # 타이틀 배너
        banner = QLabel("🕵️ 꼬마 탐정 뉴스 수사대 🎀")
        banner.setObjectName("banner")
        subtitle = QLabel("🔎 수사할 키워드를 알려주면 네이버 뉴스에서 단서를 모아올게요!")
        subtitle.setObjectName("subtitle")

        # 검색 영역
        self.query_edit = QLineEdit("아름다운가게")
        self.query_edit.setPlaceholderText("🔎 수사할 키워드를 입력하세요")
        self.query_edit.returnPressed.connect(self.start_crawl)
        self.search_btn = QPushButton("🔍 수사 시작")
        self.search_btn.setObjectName("search")
        self.search_btn.clicked.connect(self.start_crawl)
        self.stop_btn = QPushButton("✋ 잠깐!")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_crawl)
        self.save_btn = QPushButton("📄 CSV")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_csv)
        self.excel_btn = QPushButton("📊 엑셀")
        self.excel_btn.setEnabled(False)
        self.excel_btn.clicked.connect(self.save_excel)
        for btn in (self.search_btn, self.stop_btn, self.save_btn, self.excel_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(self.query_edit, 1)
        top.addWidget(self.search_btn)
        top.addWidget(self.stop_btn)
        top.addWidget(self.save_btn)
        top.addWidget(self.excel_btn)

        # 기사 목록 표
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["📰 사건 파일", "🏢 제보처", "🕰️ 발생 시각"])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_article)
        self.table.cellDoubleClicked.connect(self.open_in_browser)

        # 본문 보기
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setPlaceholderText("📝 사건 파일을 선택하면 수사 기록(본문)이 여기에 나타나요.")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.viewer)
        splitter.setSizes([350, 370])

        # 진행 상태
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.status_label = QLabel("🎀 준비 완료! [수사 시작]을 눌러주세요. (사건 파일 더블클릭 → 원문 보기)")
        self.status_label.setObjectName("status")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(banner)
        layout.addWidget(subtitle)
        layout.addLayout(top)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        central = QWidget()
        central.setObjectName("central")
        central.setLayout(layout)
        self.setCentralWidget(central)

    # ---- 크롤링 제어
    def start_crawl(self):
        query = self.query_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "🕵️ 앗!", "수사할 키워드를 먼저 알려주세요!")
            return
        if self.worker and self.worker.isRunning():
            return

        self.articles.clear()
        self.table.setRowCount(0)
        self.viewer.clear()
        self.progress.setRange(0, 0)  # 링크 수집 중에는 진행 표시만
        self.status_label.setText(f"🔍 '{query}' 사건 현장 조사 중...")
        self.set_running(True)

        self.worker = CrawlWorker(query)
        self.worker.found.connect(self.on_found)
        self.worker.article.connect(self.add_article)
        self.worker.progress.connect(self.on_progress)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop_crawl(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("✋ 수사를 멈추는 중...")

    def set_running(self, running):
        self.search_btn.setEnabled(not running)
        self.query_edit.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.save_btn.setEnabled(not running and bool(self.articles))
        self.excel_btn.setEnabled(not running and bool(self.articles))

    # ---- 작업 스레드 시그널 처리
    def on_found(self, count):
        self.progress.setRange(0, max(count, 1))
        self.progress.setValue(0)
        self.status_label.setText(f"💡 단서 {count}건 발견! 하나씩 살펴보는 중...")

    def add_article(self, article):
        self.articles.append(article)
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, key in enumerate(["title", "press", "date"]):
            self.table.setItem(row, col, QTableWidgetItem(article[key]))
        if row == 0:
            self.table.selectRow(0)

    def on_progress(self, value, message):
        self.progress.setValue(value)
        self.status_label.setText(message)

    def on_failed(self, message):
        QMessageBox.critical(self, "오류", message)

    def on_finished(self):
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 1)
        self.set_running(False)
        self.status_label.setText(f"🎉 사건 해결! 단서 {len(self.articles)}건 확보 완료")

    # ---- 기사 보기 / 저장
    def show_article(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        a = {k: html.escape(v) for k, v in self.articles[rows[0].row()].items()}
        body = a["content"].replace("\n", "<br>") or "(수사 기록을 찾지 못했어요 😢)"
        self.viewer.setHtml(
            f"<h2 style='color:{NAVY}'>🔎 {a['title']}</h2>"
            f"<p style='color:{RED}'><b>🏢 {a['press']}</b> &nbsp;·&nbsp; 🕰️ {a['date']}<br>"
            f"🔗 <a href='{a['url']}' style='color:{NAVY}'>{a['url']}</a></p><hr>"
            f"<p style='line-height:170%'>{body}</p>"
        )

    def open_in_browser(self, row, _col):
        QDesktopServices.openUrl(QUrl(self.articles[row]["url"]))

    def save_csv(self):
        default = f"naver_news_{self.query_edit.text().strip()}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "CSV 저장", default, "CSV 파일 (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.articles)
        QMessageBox.information(self, "저장 완료", f"{len(self.articles)}건 저장 완료\n{path}")

    def save_excel(self):
        default = f"naver_news_{self.query_edit.text().strip()}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "엑셀 저장", default, "엑셀 파일 (*.xlsx)")
        if not path:
            return
        try:
            export_excel(self.articles, path)
        except PermissionError:
            QMessageBox.critical(self, "오류", f"파일이 다른 프로그램에서 열려 있어 저장할 수 없습니다.\n{path}")
            return
        QMessageBox.information(self, "저장 완료", f"{len(self.articles)}건 저장 완료\n{path}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()


def resource_path(name):
    """PyInstaller로 묶인 exe에서는 임시 폴더(_MEIPASS)에서 리소스를 찾음"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("detective.ico")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
