"""
대한민국 출생아수 분석기 (PyQt6 GUI)
- 엑셀 불러오기 → 데이터 클렌징 → 다각도 분석 → 그래프
- 분석 로직은 birth_analysis.py 를 그대로 재사용

사용법: python birth_gui.py
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QSpinBox, QTableWidget,
    QTableWidgetItem, QTabWidget, QToolBar, QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.ticker as mticker

import birth_analysis as ba

DEFAULT_FILE = Path(__file__).resolve().parent / "births.xlsx"

# 화면 표시용 한글 컬럼명
DISPLAY_NAME = {**ba.KOR_LABEL, "deaths": "사망자수(명)"}
INT_COLS = {"births", "natural_increase", "deaths"}


class NumericItem(QTableWidgetItem):
    """표시는 포맷 문자열, 정렬은 UserRole 에 저장한 숫자 기준"""

    def __lt__(self, other):
        return self.data(Qt.ItemDataRole.UserRole) < other.data(Qt.ItemDataRole.UserRole)


class StatCard(QFrame):
    """요약 수치를 보여주는 카드"""

    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.value = QLabel("-")
        self.value.setObjectName("cardValue")
        self.sub = QLabel("")
        self.sub.setObjectName("cardSub")
        for w in (self.title, self.value, self.sub):
            layout.addWidget(w)

    def set(self, value: str, sub: str = ""):
        self.value.setText(value)
        self.sub.setText(sub)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("대한민국 출생아수 분석기")
        self.resize(1200, 780)
        self.df: pd.DataFrame | None = None
        self.source: Path | None = None

        ba.setup_korean_font()
        self._build_toolbar()
        self._build_ui()
        self.statusBar().showMessage("엑셀 파일을 열어주세요 (KOSIS 출생아수·합계출산율 통계표)")

        if DEFAULT_FILE.exists():
            self.load_file(DEFAULT_FILE)

    # ------------------------------------------------------------------ UI
    def _build_toolbar(self):
        tb = QToolBar("메인")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_open = QAction("📂 엑셀 열기", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.open_file)
        tb.addAction(act_open)

        self.act_csv = QAction("💾 정제 데이터 CSV 저장", self)
        self.act_csv.triggered.connect(self.save_csv)
        tb.addAction(self.act_csv)

        self.act_png = QAction("📊 그래프 PNG 저장", self)
        self.act_png.triggered.connect(self.save_png)
        tb.addAction(self.act_png)

        for a in (self.act_csv, self.act_png):
            a.setEnabled(False)

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        # 상단 요약 카드
        cards = QGridLayout()
        self.card_max = StatCard("최고 출생아수")
        self.card_min = StatCard("최저 출생아수")
        self.card_last = StatCard("최근 출생아수")
        self.card_tfr = StatCard("최근 합계출산율")
        for i, c in enumerate((self.card_max, self.card_min, self.card_last, self.card_tfr)):
            cards.addWidget(c, 0, i)
        root.addLayout(cards)

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_chart_tab(), "📈 그래프")
        self.tabs.addTab(self._build_table_tab(), "📋 정제 데이터")
        self.tabs.addTab(self._build_report_tab(), "🔍 분석 결과")
        root.addWidget(self.tabs)
        self.setCentralWidget(central)

    def _build_chart_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("지표"))
        self.cmb_metric = QComboBox()
        for key, label in DISPLAY_NAME.items():
            self.cmb_metric.addItem(label, key)
        ctrl.addWidget(self.cmb_metric)

        ctrl.addSpacing(16)
        ctrl.addWidget(QLabel("시작 연도"))
        self.spn_start = QSpinBox()
        ctrl.addWidget(self.spn_start)
        ctrl.addWidget(QLabel("~ 종료 연도"))
        self.spn_end = QSpinBox()
        ctrl.addWidget(self.spn_end)
        for s in (self.spn_start, self.spn_end):
            s.setRange(1970, 2025)
            s.setValue(1970)
        self.spn_end.setValue(2025)

        ctrl.addSpacing(16)
        self.chk_ma = QCheckBox("5년 이동평균")
        self.chk_ma.setChecked(True)
        ctrl.addWidget(self.chk_ma)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.figure = Figure(figsize=(12, 5.5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(NavigationToolbar2QT(self.canvas, w))
        layout.addWidget(self.canvas)

        self.cmb_metric.currentIndexChanged.connect(self.update_chart)
        self.spn_start.valueChanged.connect(self.update_chart)
        self.spn_end.valueChanged.connect(self.update_chart)
        self.chk_ma.toggled.connect(self.update_chart)
        return w

    def _build_table_tab(self):
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        return self.table

    def _build_report_tab(self):
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        mono = QFont()
        mono.setFamilies(["D2Coding", "Consolas", "Malgun Gothic"])
        mono.setPointSize(10)
        self.report.setFont(mono)
        return self.report

    # ------------------------------------------------------------- Actions
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 열기", str(DEFAULT_FILE.parent), "Excel (*.xlsx *.xls)")
        if path:
            self.load_file(Path(path))

    def load_file(self, path: Path):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):          # 클렌징·분석 로그를 그대로 리포트로 사용
                df = ba.load_and_clean(path)
                ba.analyze(df)
        except Exception as e:
            QMessageBox.critical(self, "불러오기 실패", f"{path.name}\n\n{type(e).__name__}: {e}")
            return

        self.df, self.source = df, path
        self.report.setPlainText(buf.getvalue())
        self._fill_table()
        self._fill_cards()

        lo, hi = int(df.index.min()), int(df.index.max())
        for s in (self.spn_start, self.spn_end):
            s.blockSignals(True)
            s.setRange(lo, hi)
        self.spn_start.setValue(lo)
        self.spn_end.setValue(hi)
        for s in (self.spn_start, self.spn_end):
            s.blockSignals(False)

        self.update_chart()
        for a in (self.act_csv, self.act_png):
            a.setEnabled(True)
        self.statusBar().showMessage(f"{path.name} — {len(df)}개 연도 ({lo}~{hi}) 불러옴")

    def _fill_cards(self):
        df = self.df
        b = df["births"].astype(float)
        last = int(df.index.max())
        yoy = b.pct_change()[last] * 100
        self.card_max.set(f"{b.max():,.0f}명", f"{b.idxmax()}년")
        self.card_min.set(f"{b.min():,.0f}명", f"{b.idxmin()}년")
        self.card_last.set(f"{b[last]:,.0f}명", f"{last}년 · 전년 대비 {yoy:+.1f}%")
        self.card_tfr.set(f"{df['tfr'][last]:.3f}명", f"{last}년 · 최저 {df['tfr'].min():.3f} ({df['tfr'].idxmin()}년)")

    def _fill_table(self):
        df = self.df
        cols = ["year"] + list(df.columns)
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(["연도"] + [DISPLAY_NAME.get(c, c) for c in df.columns])

        for r, (year, row) in enumerate(df.iterrows()):
            values = [year] + list(row.values)
            for c, (col, v) in enumerate(zip(cols, values)):
                num = float(v)
                if col == "year":
                    text = str(int(num))
                elif col in INT_COLS:
                    text = f"{num:,.0f}"
                else:
                    text = f"{num:,.3f}".rstrip("0").rstrip(".")
                item = NumericItem(text)
                item.setData(Qt.ItemDataRole.UserRole, num)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if col == "natural_increase" and num < 0:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(r, c, item)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)

    def update_chart(self):
        if self.df is None:
            return
        start, end = self.spn_start.value(), self.spn_end.value()
        if start >= end:
            self.statusBar().showMessage("시작 연도는 종료 연도보다 작아야 합니다")
            return

        metric = self.cmb_metric.currentData()
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if metric == "births":
            ba.draw_births(ax, self.df, start, end, show_ma=self.chk_ma.isChecked())
        else:
            self._draw_metric(ax, metric, start, end)
        self.canvas.draw_idle()

    def _draw_metric(self, ax, metric: str, start: int, end: int):
        s = self.df.loc[start:end, metric].astype(float)
        label = DISPLAY_NAME[metric]
        ax.plot(s.index, s.values, color="#2F6FD6", linewidth=2.2, marker="o", markersize=3.5,
                label=label)
        if self.chk_ma.isChecked():
            ax.plot(s.index, s.rolling(5, center=True).mean(), color="#9AA4B2",
                    linewidth=1.2, linestyle="--", label="5년 이동평균")
        # 지표별 기준선
        refs = {"tfr": (2.1, "대체출산율 2.1"), "sex_ratio": (107, "정상범위 상한 107"),
                "natural_increase": (0, "0 (자연감소 경계)"),
                "natural_increase_rate": (0, "0 (자연감소 경계)")}
        if metric in refs:
            y, txt = refs[metric]
            ax.axhline(y, color="#D64545", linewidth=1, linestyle=":", label=txt)
        if metric in INT_COLS:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 10_000:,.0f}만"))

        ax.set_title(f"대한민국 연도별 {label} ({start}~{end})", fontsize=15, pad=12)
        ax.set_xlabel("연도")
        ax.set_ylabel(label)
        ax.set_xticks(range(start, end + 1, 5 if end - start > 20 else 1))
        ax.set_xlim(start - 1, end + 1)
        ax.grid(axis="y", alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False)

    def save_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "정제 데이터 저장", str(ba.OUT_DIR / "births_clean.csv"), "CSV (*.csv)")
        if path:
            self.df.rename(columns=DISPLAY_NAME).rename_axis("연도").to_csv(path, encoding="utf-8-sig")
            self.statusBar().showMessage(f"저장 완료: {path}")

    def save_png(self):
        metric = self.cmb_metric.currentData()
        default = ba.OUT_DIR / f"{metric}_{self.spn_start.value()}_{self.spn_end.value()}.png"
        path, _ = QFileDialog.getSaveFileName(self, "그래프 저장", str(default), "PNG (*.png)")
        if path:
            self.figure.savefig(path, dpi=150)
            self.statusBar().showMessage(f"저장 완료: {path}")


STYLE = """
QMainWindow { background: #F6F7F9; }
#card { background: white; border: 1px solid #E3E6EA; border-radius: 8px; }
#cardTitle { color: #6B7280; font-size: 12px; }
#cardValue { color: #111827; font-size: 22px; font-weight: 600; }
#cardSub { color: #9CA3AF; font-size: 11px; }
QTabWidget::pane { border: 1px solid #E3E6EA; background: white; border-radius: 6px; }
QTabBar::tab { padding: 8px 18px; }
QTabBar::tab:selected { font-weight: 600; }
"""


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic", 10))
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
