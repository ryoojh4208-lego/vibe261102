"""
정해진 5개 키워드(아름다운가게/사회적기업/NGO/비영리단체/기후위기)의
네이버 뉴스 탭 검색 결과에서 기사를 찾아 본문까지 크롤링하는 GUI 앱
(requests + BeautifulSoup4 + PyQt6, 엑셀 저장은 openpyxl)

사용법:
    pip install requests beautifulsoup4 PyQt6 openpyxl
    python naver_keyword_news_crawler.py
"""
import csv
import html
import os
import re
import sys
import time

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.naver.com/",
}

# 네이버뉴스 기사 링크 형식: https://n.news.naver.com/mnews/article/{언론사}/{기사번호}
ARTICLE_RE = re.compile(r"https?://n\.news\.naver\.com/(?:mnews/)?article/\d+/\d+")

FIELDS = ["keyword", "title", "press", "date", "url", "content"]

# 따뜻하고 귀여운 컨셉 스타일 (베이지 바탕 + 초록 잎사귀 + 갈색 글씨)
GREEN = "#5A9E3A"       # 메인 초록
LEAF = "#8CC26B"        # 밝은 연두
SOFT_GREEN = "#E6F2DA"  # 아주 연한 초록
BEIGE = "#F7EFDF"       # 바탕 베이지
SAND = "#E8D9BC"        # 진한 베이지 (테두리)
BROWN = "#6B4F35"       # 글씨 갈색
STYLE = f"""
QMainWindow, QWidget#central {{ background: {BEIGE}; }}
QWidget {{ font-family: "Malgun Gothic"; font-size: 10pt; color: {BROWN}; }}
QLabel#banner {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {GREEN}, stop:1 {LEAF});
    color: white; font-size: 18pt; font-weight: bold;
    border-radius: 24px; padding: 14px 22px;
}}
QLabel#subtitle {{ color: {BROWN}; font-size: 9pt; padding-left: 8px; }}
QLabel#status {{ color: {GREEN}; font-weight: bold; padding: 2px 8px; }}
QPushButton {{
    background: {GREEN}; color: white; border: none; border-radius: 18px;
    padding: 8px 16px; font-weight: bold;
}}
QPushButton:hover {{ background: {LEAF}; }}
QPushButton:disabled {{ background: {SAND}; color: #FFFDF8; }}
QTableWidget {{
    background: #FFFDF8; alternate-background-color: {SOFT_GREEN};
    border: 3px solid {SAND}; border-radius: 18px; gridline-color: transparent;
    selection-background-color: {LEAF}; selection-color: white;
}}
QHeaderView::section {{
    background: {SAND}; color: {BROWN}; font-weight: bold; border: none; padding: 7px;
}}
QTextBrowser {{
    background: #FFFDF8; border: 3px dashed {LEAF}; border-radius: 18px; padding: 10px;
}}
QProgressBar {{
    background: #FFFDF8; border: 2px solid {SAND}; border-radius: 10px;
    height: 20px; text-align: center; color: {BROWN}; font-weight: bold;
}}
QProgressBar::chunk {{ background: {LEAF}; border-radius: 8px; }}
QSplitter::handle {{ background: transparent; height: 8px; }}
"""

# 요청하신 5개 뉴스 탭 검색 URL (query 값만 키워드별로 다름)
KEYWORD_URLS = {
    "아름다운가게": "https://search.naver.com/search.naver?ssc=tab.news.all&where=news&sm=tab_jum&query=%EC%95%84%EB%A6%84%EB%8B%A4%EC%9A%B4%EA%B0%80%EA%B2%8C",
    "사회적기업": "https://search.naver.com/search.naver?sm=tab_hty.top&where=news&ssc=tab.news.all&query=%EC%82%AC%ED%9A%8C%EC%A0%81%EA%B8%B0%EC%97%85",
    "NGO": "https://search.naver.com/search.naver?sm=tab_hty.top&where=news&ssc=tab.news.all&query=NGO",
    "비영리단체": "https://search.naver.com/search.naver?sm=tab_hty.top&where=news&ssc=tab.news.all&query=%EB%B9%84%EC%98%81%EB%A6%AC%EB%8B%A8%EC%B2%B4",
    "기후위기": "https://search.naver.com/search.naver?sm=tab_hty.top&where=news&ssc=tab.news.all&query=%EA%B8%B0%ED%9B%84%EC%9C%84%EA%B8%B0",
}

# 선택된 키워드 버튼 강조 스타일
STYLE += f"""
QPushButton#keyword {{ background: #FFFDF8; color: {GREEN}; border: 3px solid {LEAF}; }}
QPushButton#keyword:hover {{ background: {SOFT_GREEN}; }}
QPushButton#keyword:checked {{ background: {GREEN}; color: white; border-color: {GREEN}; }}
QPushButton#keyword:disabled {{ color: {SAND}; border-color: {SAND}; }}
QPushButton#keyword:checked:disabled {{ background: {LEAF}; color: white; border-color: {LEAF}; }}
QPushButton#all {{ background: #D98E4A; }}
QPushButton#all:hover {{ background: #E8A464; }}
"""


# ---------------------------------------------------------------- 크롤링 로직
def get_soup(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def collect_article_links(url):
    """뉴스 탭 검색 결과에서 네이버뉴스 기사 링크를 중복 없이 수집"""
    links = []
    for a in get_soup(url).find_all("a", href=True):
        m = ARTICLE_RE.match(a["href"])
        if m and m.group(0) not in links:
            links.append(m.group(0))
    return links


def parse_article(url, keyword):
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
        "keyword": keyword,
        "title": title.get_text(strip=True) if title else "",
        "press": press.get("alt", "") if press else "",
        "date": date.get("data-date-time", date.get_text(strip=True)) if date else "",
        "url": url,
        "content": content,
    }


def export_excel(articles, path):
    """수집한 기사를 키워드별 시트로 나눠 엑셀(.xlsx) 파일로 저장
    (키워드가 2개 이상이면 맨 앞에 모든 기사를 모은 '전체' 시트 추가)"""
    by_keyword = {}
    for a in articles:
        by_keyword.setdefault(a["keyword"], []).append(a)

    sheets = list(by_keyword.items())
    if len(sheets) > 1:
        sheets.insert(0, ("전체", articles))

    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in sheets:
        write_sheet(wb.create_sheet(name), rows)
    wb.save(path)


def write_sheet(ws, articles):
    """시트 하나에 머리글 서식과 기사 목록을 기록"""
    headers = ["번호", "키워드", "제목", "언론사", "날짜", "URL", "본문"]
    widths = [6, 12, 50, 14, 20, 45, 100]
    ws.append(headers)
    for col, width in enumerate(widths, 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=GREEN.lstrip("#"))
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = width

    for i, a in enumerate(articles, 1):
        ws.append([i] + [a[k] for k in FIELDS])
        row = i + 1
        url_cell = ws.cell(row=row, column=6)
        url_cell.hyperlink = a["url"]
        url_cell.style = "Hyperlink"
        for col in range(1, 8):
            # 제목/본문은 줄바꿈 유지, 나머지는 위쪽 정렬
            ws.cell(row=row, column=col).alignment = Alignment(
                vertical="top", wrap_text=(col in (3, 7))
            )
        ws.row_dimensions[row].height = 90

    ws.freeze_panes = "A2"  # 머리글 고정
    ws.auto_filter.ref = ws.dimensions


# ---------------------------------------------------------------- 작업 스레드
class CrawlWorker(QThread):
    """크롤링 중에도 화면이 멈추지 않도록 별도 스레드에서 실행"""

    found = pyqtSignal(int)              # 발견한 기사 수
    article = pyqtSignal(dict)           # 기사 1건 수집 완료
    progress = pyqtSignal(int, str)      # 진행 번호, 상태 메시지
    failed = pyqtSignal(str)             # 치명적 오류

    def __init__(self, keywords):
        super().__init__()
        self.keywords = keywords
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        # 모든 키워드의 기사 링크를 먼저 모아 전체 진행률을 계산
        jobs = []
        for kw in self.keywords:
            if self._stop:
                return
            try:
                jobs += [(kw, url) for url in collect_article_links(KEYWORD_URLS[kw])]
            except requests.RequestException as e:
                self.failed.emit(f"'{kw}' 검색 페이지를 가져오지 못했습니다.\n{e}")
                return

        self.found.emit(len(jobs))
        for i, (kw, url) in enumerate(jobs, 1):
            if self._stop:
                break
            try:
                self.article.emit(parse_article(url, kw))
                self.progress.emit(i, f"[{i}/{len(jobs)}] {kw} 수집 완료")
            except requests.RequestException as e:
                self.progress.emit(i, f"[{i}/{len(jobs)}] {kw} 실패: {e}")
            time.sleep(0.5)  # 서버 부담을 줄이기 위한 요청 간격


# ---------------------------------------------------------------- 메인 화면
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌱 키워드 뉴스 크롤러")
        self.resize(1100, 760)
        self.setStyleSheet(STYLE)
        self.articles = []
        self.worker = None
        self.keyword = None

        # 타이틀 배너
        banner = QLabel("🌱 따뜻한 뉴스 바구니 🧺")
        banner.setObjectName("banner")
        subtitle = QLabel(
            "🍀 키워드 버튼을 누르면 네이버 뉴스에서 기사 본문을 모아옵니다."
            " [전체 수집] → 5개 키워드를 모두 모아 엑셀에 키워드별 시트로 저장"
        )
        subtitle.setObjectName("subtitle")

        # 키워드 버튼 5개 (누르면 바로 크롤링 시작)
        self.keyword_btns = []
        keywords = QHBoxLayout()
        keywords.setSpacing(8)
        for kw in KEYWORD_URLS:
            btn = QPushButton(kw)
            btn.setObjectName("keyword")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, k=kw: self.start_crawl([k]))
            keywords.addWidget(btn, 1)
            self.keyword_btns.append(btn)

        # 제어 버튼
        self.all_btn = QPushButton("🧺 전체 수집")
        self.all_btn.setObjectName("all")
        self.all_btn.clicked.connect(lambda: self.start_crawl(list(KEYWORD_URLS)))
        keywords.addWidget(self.all_btn)
        self.stop_btn = QPushButton("✋ 중지")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_crawl)
        self.save_btn = QPushButton("📄 CSV")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_csv)
        self.excel_btn = QPushButton("📊 엑셀")
        self.excel_btn.setEnabled(False)
        self.excel_btn.clicked.connect(self.save_excel)
        for btn in (self.all_btn, self.stop_btn, self.save_btn, self.excel_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        for btn in (self.stop_btn, self.save_btn, self.excel_btn):
            keywords.addWidget(btn)

        # 기사 목록 표
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["🏷️ 키워드", "📰 제목", "🏢 언론사", "🕰️ 날짜"])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_article)
        self.table.cellDoubleClicked.connect(self.open_in_browser)

        # 본문 보기
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setPlaceholderText("🌼 기사를 선택하면 본문이 여기에 나타나요.")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.viewer)
        splitter.setSizes([350, 370])

        # 진행 상태
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.status_label = QLabel("키워드 버튼을 눌러주세요. (기사 더블클릭 → 원문 보기)")
        self.status_label.setObjectName("status")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(banner)
        layout.addWidget(subtitle)
        layout.addLayout(keywords)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        central = QWidget()
        central.setObjectName("central")
        central.setLayout(layout)
        self.setCentralWidget(central)

    # ---- 크롤링 제어
    def start_crawl(self, keywords):
        if self.worker and self.worker.isRunning():
            return
        # 상태 메시지와 저장 파일 이름에 쓰는 이름 (전체 수집이면 '전체')
        self.keyword = keywords[0] if len(keywords) == 1 else "전체"
        for btn in self.keyword_btns:
            btn.setChecked(btn.text() in keywords)

        self.articles.clear()
        self.table.setRowCount(0)
        self.viewer.clear()
        self.progress.setRange(0, 0)  # 링크 수집 중에는 진행 표시만
        self.status_label.setText(f"🌿 '{self.keyword}' 뉴스를 찾는 중이에요...")
        self.set_running(True)

        self.worker = CrawlWorker(keywords)
        self.worker.found.connect(self.on_found)
        self.worker.article.connect(self.add_article)
        self.worker.progress.connect(self.on_progress)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop_crawl(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("✋ 중지하는 중...")

    def set_running(self, running):
        for btn in self.keyword_btns + [self.all_btn]:
            btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.save_btn.setEnabled(not running and bool(self.articles))
        self.excel_btn.setEnabled(not running and bool(self.articles))

    # ---- 작업 스레드 시그널 처리
    def on_found(self, count):
        self.progress.setRange(0, max(count, 1))
        self.progress.setValue(0)
        self.status_label.setText(f"🍃 기사 {count}건 발견! 하나씩 담는 중이에요...")

    def add_article(self, article):
        self.articles.append(article)
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, key in enumerate(["keyword", "title", "press", "date"]):
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
        self.status_label.setText(f"🌻 '{self.keyword}' 기사 {len(self.articles)}건을 바구니에 담았어요!")

    # ---- 기사 보기 / 저장
    def show_article(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        a = {k: html.escape(v) for k, v in self.articles[rows[0].row()].items()}
        body = a["content"].replace("\n", "<br>") or "(본문을 찾지 못했습니다)"
        self.viewer.setHtml(
            f"<h2 style='color:{GREEN}'>{a['title']}</h2>"
            f"<p style='color:{BROWN}'><b>🏢 {a['press']}</b> &nbsp;·&nbsp; 🕰️ {a['date']}"
            f" &nbsp;·&nbsp; 🏷️ {a['keyword']}<br>"
            f"🔗 <a href='{a['url']}' style='color:{GREEN}'>{a['url']}</a></p><hr>"
            f"<p style='line-height:170%'>{body}</p>"
        )

    def open_in_browser(self, row, _col):
        QDesktopServices.openUrl(QUrl(self.articles[row]["url"]))

    def save_csv(self):
        default = f"naver_news_{self.keyword}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "CSV 저장", default, "CSV 파일 (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.articles)
        QMessageBox.information(self, "저장 완료", f"{len(self.articles)}건 저장 완료\n{path}")

    def save_excel(self):
        default = f"naver_news_{self.keyword}.xlsx"
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
