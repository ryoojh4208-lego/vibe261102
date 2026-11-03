"""
네이버페이 증권(https://stock.naver.com/market/stock/kr)의 코스피200 데이터를
수집해서 보여주는 GUI 앱 (requests + PyQt6, 엑셀 저장은 openpyxl)

새 네이버 증권 페이지는 Next.js SPA라서 HTML에는 빈 표(0, '-')만 들어 있고,
실제 시세는 브라우저가 아래 JSON API를 호출해 채운다.
(예전 finance.naver.com/sise/... HTML 페이지는 410 Gone으로 폐지됨)
그래서 BeautifulSoup으로 HTML을 파싱해서는 값을 얻을 수 없고,
페이지가 쓰는 API를 requests로 직접 호출한다.

  - 지수 요약 : https://m.stock.naver.com/api/index/KPI200/basic
  - 일별 시세 : https://m.stock.naver.com/api/index/KPI200/price
  - 구성 종목 : https://m.stock.naver.com/api/index/KPI200/enrollStocks

사용법:
    pip install requests PyQt6 openpyxl
    python kospi200_crawler.py
"""
import csv
import sys
import time
from datetime import datetime

import requests
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices
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
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

API = "https://m.stock.naver.com/api/index/KPI200"
STOCK_URL = "https://stock.naver.com/domestic/stock/{code}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Referer": "https://stock.naver.com/market/stock/kr",
}
PAGE_SIZE = 60  # 서버 허용 최대값 (100은 400 에러)
DAILY_DAYS = 60

STOCK_FIELDS = ["순위", "종목코드", "종목명", "현재가", "전일대비", "등락률(%)",
                "거래량", "거래대금(백만)", "시가총액(억)"]
DAILY_FIELDS = ["날짜", "종가", "전일대비", "등락률(%)", "시가", "고가", "저가"]

# 국내 증시 관례: 상승 빨강, 하락 파랑
UP = "#D62C2C"
DOWN = "#1F5FD6"
NAVY = "#1B2B48"
BG = "#F5F7FB"
STYLE = f"""
QMainWindow, QWidget#central {{ background: {BG}; }}
QWidget {{ font-family: "Malgun Gothic"; font-size: 10pt; color: #222; }}
QLabel#title {{ font-size: 16pt; font-weight: bold; color: {NAVY}; }}
QLabel#price {{ font-size: 26pt; font-weight: bold; }}
QLabel#change {{ font-size: 13pt; font-weight: bold; }}
QLabel#meta, QLabel#status {{ color: #666; }}
QWidget#card {{ background: white; border: 1px solid #DDE3EE; border-radius: 10px; }}
QPushButton {{
    background: white; border: 1px solid #C9D2E3; border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{ background: #EEF2FA; }}
QPushButton:disabled {{ color: #AAA; }}
QPushButton#primary {{ background: {NAVY}; color: white; border: none; font-weight: bold; }}
QPushButton#primary:hover {{ background: #2A3F66; }}
QPushButton#primary:disabled {{ background: #8892A6; }}
QLineEdit {{ background: white; border: 1px solid #C9D2E3; border-radius: 6px; padding: 5px 8px; }}
QTableWidget {{
    background: white; alternate-background-color: #F7F9FD;
    border: 1px solid #DDE3EE; gridline-color: #EEE;
}}
QHeaderView::section {{
    background: {NAVY}; color: white; font-weight: bold; padding: 5px; border: none;
}}
QTabWidget::pane {{ border: none; }}
QProgressBar {{ border: 1px solid #C9D2E3; border-radius: 5px; background: white; height: 14px;
               text-align: center; }}
QProgressBar::chunk {{ background: {NAVY}; border-radius: 4px; }}
"""


# ---------------------------------------------------------------- 수집 함수
def get_json(url, params=None):
    resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_index_summary():
    """코스피200 지수 현재가/등락"""
    d = get_json(f"{API}/basic")
    return {
        "지수명": d["stockName"],
        "현재가": d["closePrice"],
        "전일대비": d["compareToPreviousClosePrice"],
        "등락률(%)": d["fluctuationsRatio"],
        "상태": d["marketStatus"],
        "기준시각": d["localTradedAt"],
    }


def fetch_daily_prices(days=DAILY_DAYS):
    """코스피200 일별 시세 (최근 days일)"""
    rows = get_json(f"{API}/price", {"page": 1, "pageSize": days})
    return [
        {
            "날짜": r["localTradedAt"],
            "종가": float(r["closePrice"].replace(",", "")),
            "전일대비": float(r["compareToPreviousClosePrice"].replace(",", "")),
            "등락률(%)": float(r["fluctuationsRatio"]),
            "시가": float(r["openPrice"].replace(",", "")),
            "고가": float(r["highPrice"].replace(",", "")),
            "저가": float(r["lowPrice"].replace(",", "")),
        }
        for r in rows
    ]


def parse_stock(rank, r):
    return {
        "순위": rank,
        "종목코드": r["itemCode"],
        "종목명": r["stockName"],
        "현재가": int(r["closePriceRaw"]),
        "전일대비": int(r["compareToPreviousClosePriceRaw"]),
        "등락률(%)": float(r["fluctuationsRatio"]),
        "거래량": int(r["accumulatedTradingVolumeRaw"]),
        "거래대금(백만)": int(r["accumulatedTradingValueRaw"]) // 1_000_000,
        "시가총액(억)": int(r["marketValueRaw"]) // 100_000_000,
    }


def save_csv(rows, fields, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # 엑셀 한글 깨짐 방지
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export_excel(stocks, daily, path):
    """구성 종목 / 일별 시세를 시트 2개짜리 엑셀(.xlsx)로 저장"""
    wb = Workbook()
    sheets = [(wb.active, "구성종목", STOCK_FIELDS, stocks),
              (wb.create_sheet(), "일별시세", DAILY_FIELDS, daily)]
    for ws, title, fields, rows in sheets:
        ws.title = title
        ws.append(fields)
        for col in range(1, len(fields) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor=NAVY.lstrip("#"))
            cell.alignment = Alignment(horizontal="center")
            ws.column_dimensions[get_column_letter(col)].width = 16
        for r in rows:
            ws.append([r[f] for f in fields])
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value, int):
                    cell.number_format = "#,##0"
                elif isinstance(cell.value, float):
                    cell.number_format = "#,##0.00"
        ws.freeze_panes = "A2"  # 머리글 고정
        ws.auto_filter.ref = ws.dimensions
    wb.save(path)


# ---------------------------------------------------------------- 작업 스레드
class CrawlWorker(QThread):
    """수집 중에도 화면이 멈추지 않도록 별도 스레드에서 실행"""

    summary = pyqtSignal(dict)           # 지수 요약
    daily = pyqtSignal(list)             # 일별 시세
    stocks = pyqtSignal(list)            # 구성 종목 한 페이지분
    progress = pyqtSignal(int, str)      # 수집한 종목 수, 상태 메시지
    failed = pyqtSignal(str)             # 오류

    def __init__(self, max_pages=20):
        super().__init__()
        self.max_pages = max_pages
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            self.summary.emit(fetch_index_summary())
            self.daily.emit(fetch_daily_prices())

            # 페이지 단위로 받아오며, 빈 페이지나 PAGE_SIZE 미만 페이지가 나오면 마지막으로 본다.
            # 페이지 경계에서 순위가 바뀌어 같은 종목이 두 번 나올 수 있어 종목코드로 중복 제거.
            seen = set()
            for page in range(1, self.max_pages + 1):
                if self._stop:
                    break
                rows = get_json(f"{API}/enrollStocks", {"page": page, "pageSize": PAGE_SIZE})
                batch = []
                for r in rows:
                    if r["itemCode"] in seen:
                        continue
                    seen.add(r["itemCode"])
                    batch.append(parse_stock(len(seen), r))
                self.stocks.emit(batch)
                self.progress.emit(len(seen), f"{page}페이지: {len(rows)}개 수집 (누적 {len(seen)}개)")
                if len(rows) < PAGE_SIZE:
                    break
                time.sleep(0.3)  # 서버 부담 줄이기
        except (requests.RequestException, KeyError, ValueError) as e:
            self.failed.emit(f"데이터를 가져오지 못했습니다.\n{e}")


# ---------------------------------------------------------------- 표 헬퍼
class NumItem(QTableWidgetItem):
    """천 단위 콤마로 보여주되 숫자 크기로 정렬되는 셀"""

    def __init__(self, value, fmt="{:,}"):
        super().__init__(fmt.format(value))
        self.value = value
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, other):
        if isinstance(other, NumItem):
            return self.value < other.value
        return super().__lt__(other)


def sign_color(value):
    if value > 0:
        return QColor(UP)
    if value < 0:
        return QColor(DOWN)
    return QColor("#222")


def make_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    return table


# ---------------------------------------------------------------- 메인 화면
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("코스피200 시세 수집기")
        self.resize(1150, 780)
        self.setStyleSheet(STYLE)
        self.stock_rows = []
        self.daily_rows = []
        self.worker = None

        # 지수 요약 카드
        title = QLabel("📈 코스피 200")
        title.setObjectName("title")
        self.price_label = QLabel("-")
        self.price_label.setObjectName("price")
        self.change_label = QLabel("")
        self.change_label.setObjectName("change")
        self.meta_label = QLabel("[수집 시작]을 눌러 데이터를 불러오세요.")
        self.meta_label.setObjectName("meta")

        price_row = QHBoxLayout()
        price_row.addWidget(self.price_label)
        price_row.addSpacing(12)
        price_row.addWidget(self.change_label, 0, Qt.AlignmentFlag.AlignBottom)
        price_row.addStretch(1)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.addWidget(title)
        card_layout.addLayout(price_row)
        card_layout.addWidget(self.meta_label)
        card = QWidget()
        card.setObjectName("card")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setLayout(card_layout)

        # 버튼 / 검색
        self.start_btn = QPushButton("🔄 수집 시작")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start_crawl)
        self.stop_btn = QPushButton("⏹ 중지")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_crawl)
        self.csv_btn = QPushButton("📄 CSV")
        self.csv_btn.setEnabled(False)
        self.csv_btn.clicked.connect(self.save_csv_files)
        self.excel_btn = QPushButton("📊 엑셀")
        self.excel_btn.setEnabled(False)
        self.excel_btn.clicked.connect(self.save_excel)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("🔎 종목명 또는 종목코드로 거르기")
        self.filter_edit.textChanged.connect(self.apply_filter)
        for btn in (self.start_btn, self.stop_btn, self.csv_btn, self.excel_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.start_btn)
        toolbar.addWidget(self.stop_btn)
        toolbar.addWidget(self.filter_edit, 1)
        toolbar.addWidget(self.csv_btn)
        toolbar.addWidget(self.excel_btn)

        # 표 (탭 2개)
        self.stock_table = make_table(STOCK_FIELDS)
        self.stock_table.cellDoubleClicked.connect(self.open_stock_page)
        self.daily_table = make_table(DAILY_FIELDS)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.stock_table, "구성 종목")
        self.tabs.addTab(self.daily_table, "일별 시세")

        # 진행 상태
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)  # 진행 상황은 아래 상태 문구로 표시
        self.status_label = QLabel("준비 완료 (종목 더블클릭 → 네이버 증권에서 보기, 머리글 클릭 → 정렬)")
        self.status_label.setObjectName("status")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(card)
        layout.addLayout(toolbar)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        central = QWidget()
        central.setObjectName("central")
        central.setLayout(layout)
        self.setCentralWidget(central)

    # ---- 수집 제어
    def start_crawl(self):
        if self.worker and self.worker.isRunning():
            return
        self.stock_rows.clear()
        self.daily_rows.clear()
        self.stock_table.setSortingEnabled(False)
        self.stock_table.setRowCount(0)
        self.daily_table.setRowCount(0)
        self.progress.setRange(0, 0)  # 종목 수를 알기 전에는 진행 표시만
        self.status_label.setText("지수 정보를 불러오는 중...")
        self.set_running(True)

        self.worker = CrawlWorker()
        self.worker.summary.connect(self.show_summary)
        self.worker.daily.connect(self.fill_daily)
        self.worker.stocks.connect(self.add_stocks)
        self.worker.progress.connect(self.on_progress)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop_crawl(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("중지하는 중...")

    def set_running(self, running):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        has_data = not running and bool(self.stock_rows)
        self.csv_btn.setEnabled(has_data)
        self.excel_btn.setEnabled(has_data)

    # ---- 작업 스레드 시그널 처리
    def show_summary(self, s):
        change = float(s["전일대비"].replace(",", ""))
        arrow = "▲" if change > 0 else "▼" if change < 0 else ""
        color = sign_color(change).name()
        self.price_label.setText(s["현재가"])
        self.price_label.setStyleSheet(f"color: {color};")
        self.change_label.setText(f"{arrow} {s['전일대비'].lstrip('-')}  ({s['등락률(%)']}%)")
        self.change_label.setStyleSheet(f"color: {color};")
        status = "장중" if s["상태"] == "OPEN" else "장마감"
        traded = s["기준시각"][:16].replace("T", " ")
        self.meta_label.setText(f"{status} · 기준 {traded}")

    def fill_daily(self, rows):
        self.daily_rows = rows
        self.daily_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.daily_table.setItem(i, 0, QTableWidgetItem(r["날짜"]))
            for col, key in enumerate(DAILY_FIELDS[1:], 1):
                item = NumItem(r[key], "{:,.2f}")
                if key in ("전일대비", "등락률(%)"):
                    item.setForeground(sign_color(r[key]))
                self.daily_table.setItem(i, col, item)

    def add_stocks(self, batch):
        self.stock_rows.extend(batch)
        for r in batch:
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            for col, key in enumerate(STOCK_FIELDS):
                value = r[key]
                if key in ("종목코드", "종목명"):
                    item = QTableWidgetItem(value)
                elif key == "등락률(%)":
                    item = NumItem(value, "{:+.2f}")
                elif key == "전일대비":
                    item = NumItem(value, "{:+,}")
                else:
                    item = NumItem(value)
                if key in ("전일대비", "등락률(%)"):
                    item.setForeground(sign_color(value))
                self.stock_table.setItem(row, col, item)
        self.apply_filter()

    def on_progress(self, count, message):
        # KOSPI200은 보통 200종목이지만 정기변경 등으로 늘 수 있어 최대값을 맞춰 늘림
        self.progress.setRange(0, max(200, count))
        self.progress.setValue(count)
        self.status_label.setText(message)

    def on_failed(self, message):
        QMessageBox.critical(self, "오류", message)

    def on_finished(self):
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 1)
        else:
            self.progress.setRange(0, len(self.stock_rows) or 1)
            self.progress.setValue(len(self.stock_rows))
        self.stock_table.setSortingEnabled(True)
        self.set_running(False)
        self.status_label.setText(
            f"수집 완료: 구성 종목 {len(self.stock_rows)}개, 일별 시세 {len(self.daily_rows)}일 "
            f"({datetime.now():%H:%M:%S})"
        )

    # ---- 표 조작
    def apply_filter(self):
        keyword = self.filter_edit.text().strip().lower()
        for row in range(self.stock_table.rowCount()):
            code = self.stock_table.item(row, 1).text()
            name = self.stock_table.item(row, 2).text().lower()
            hidden = bool(keyword) and keyword not in name and keyword not in code
            self.stock_table.setRowHidden(row, hidden)

    def open_stock_page(self, row, _col):
        code = self.stock_table.item(row, 1).text()
        QDesktopServices.openUrl(QUrl(STOCK_URL.format(code=code)))

    # ---- 저장
    def save_csv_files(self):
        default = f"kospi200_stocks_{datetime.now():%Y%m%d}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "CSV 저장", default, "CSV 파일 (*.csv)")
        if not path:
            return
        daily_path = path.replace("_stocks_", "_daily_") if "_stocks_" in path \
            else path[:-4] + "_daily.csv"
        try:
            save_csv(self.stock_rows, STOCK_FIELDS, path)
            save_csv(self.daily_rows, DAILY_FIELDS, daily_path)
        except PermissionError:
            QMessageBox.critical(self, "오류", "파일이 다른 프로그램에서 열려 있어 저장할 수 없습니다.")
            return
        QMessageBox.information(
            self, "저장 완료",
            f"구성 종목 {len(self.stock_rows)}개\n{path}\n\n일별 시세 {len(self.daily_rows)}일\n{daily_path}",
        )

    def save_excel(self):
        default = f"kospi200_{datetime.now():%Y%m%d}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "엑셀 저장", default, "엑셀 파일 (*.xlsx)")
        if not path:
            return
        try:
            export_excel(self.stock_rows, self.daily_rows, path)
        except PermissionError:
            QMessageBox.critical(self, "오류", f"파일이 다른 프로그램에서 열려 있어 저장할 수 없습니다.\n{path}")
            return
        QMessageBox.information(self, "저장 완료", f"구성 종목 {len(self.stock_rows)}개 저장 완료\n{path}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.start_crawl()  # 실행하면 바로 수집 시작
    sys.exit(app.exec())
