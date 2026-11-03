"""
대한민국 출생아수·합계출산율·자연증가 데이터 (KOSIS, 1970~2025)
1) 데이터 클렌징  2) pandas 다각도 분석  3) 출생아수 라인 그래프

사용법: python birth_analysis.py [엑셀파일경로]
"""
import sys
import warnings
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

BASE_DIR = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "births.xlsx"
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

# 원본 항목명 → 분석용 컬럼명 (단위는 주석으로 관리)
COLUMN_MAP = {
    "출생아수(명)": "births",              # 명
    "자연증가건수(명)": "natural_increase",  # 명 (출생 - 사망)
    "조출생률(천명당)": "crude_birth_rate",  # 인구 천명당
    "자연증가율(천명당)": "natural_increase_rate",  # 인구 천명당
    "합계출산율(명)": "tfr",                # 여성 1명당 평생 출생아수
    "출생성비(명)": "sex_ratio",            # 여아 100명당 남아
}
KOR_LABEL = {v: k for k, v in COLUMN_MAP.items()}


def section(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


# ----------------------------------------------------------------------
# 1. 데이터 클렌징
# ----------------------------------------------------------------------
def load_and_clean(path: Path) -> pd.DataFrame:
    section("1. 데이터 클렌징")
    raw = pd.read_excel(path, sheet_name=0, header=None)
    print(f"원본 shape: {raw.shape}  (행=지표, 열=연도인 wide 형태)")

    # (1) 첫 행은 연도 헤더, 첫 열은 지표명 → 전치하여 '연도 x 지표' tidy 형태로 변환
    raw.iloc[:, 0] = raw.iloc[:, 0].astype(str).str.strip()
    raw = raw.set_index(0)
    df = raw.T
    df.columns.name = None

    # (2) 연도 컬럼 정리: float(1970.0) → int
    df = df.rename(columns={df.columns[0]: "year"})  # 첫 행(기본항목) = 연도
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    # (3) 컬럼명 영문 snake_case 로 변경, 예상치 못한 지표가 있으면 알림
    unknown = set(df.columns) - set(COLUMN_MAP) - {"year"}
    if unknown:
        print(f"[경고] 매핑되지 않은 항목: {unknown}")
    df = df.rename(columns=COLUMN_MAP)

    # (4) 숫자형 변환 (쉼표·공백·'-' 등 문자열이 섞여 있어도 안전하게 처리)
    value_cols = [c for c in df.columns if c != "year"]
    for c in value_cols:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(",", "").str.strip().replace({"-": None, "": None}),
            errors="coerce",
        )
    df[["births", "natural_increase"]] = df[["births", "natural_increase"]].round().astype("Int64")

    # (5) 중복 연도 제거 및 정렬
    dup = df["year"].duplicated().sum()
    df = df.drop_duplicates("year", keep="last").sort_values("year").set_index("year")
    print(f"중복 연도 제거: {dup}건")

    # (6) 결측치 확인 / 연도 연속성 확인
    na = df.isna().sum()
    print("결측치 개수:\n" + na.to_string())
    missing_years = sorted(set(range(df.index.min(), df.index.max() + 1)) - set(df.index))
    print(f"누락 연도: {missing_years or '없음'}")
    if na.any():
        df = df.interpolate(method="linear", limit_direction="both")
        print("→ 결측치는 선형 보간으로 처리")

    # (7) 값 범위(도메인) 검증
    checks = {
        "출생아수 > 0": (df["births"] > 0).all(),
        "합계출산율 0~10": df["tfr"].between(0, 10).all(),
        "출생성비 90~130": df["sex_ratio"].between(90, 130).all(),
        "조출생률 0~60": df["crude_birth_rate"].between(0, 60).all(),
    }
    for k, ok in checks.items():
        print(f"검증 [{k}]: {'통과' if ok else '실패'}")

    # (8) 파생 변수: 사망자수 = 출생아수 - 자연증가건수
    df["deaths"] = df["births"] - df["natural_increase"]

    print(f"\n클렌징 후 shape: {df.shape}, 기간: {df.index.min()}~{df.index.max()}")
    print(df.dtypes.to_string())
    df.to_csv(OUT_DIR / "births_clean.csv", encoding="utf-8-sig")
    print(f"→ 저장: {OUT_DIR / 'births_clean.csv'}")
    return df


# ----------------------------------------------------------------------
# 2. 다각도 분석
# ----------------------------------------------------------------------
def analyze(df: pd.DataFrame) -> None:
    b = df["births"].astype(float)

    section("2-1. 기술통계")
    print(df.describe().T[["mean", "std", "min", "50%", "max"]])

    section("2-2. 출생아수 최고/최저 및 장기 변화")
    print(f"최고: {b.idxmax()}년 {b.max():,.0f}명")
    print(f"최저: {b.idxmin()}년 {b.min():,.0f}명")
    first, last = df.index.min(), df.index.max()
    n = last - first
    cagr = (b[last] / b[first]) ** (1 / n) - 1
    print(f"{first}→{last}: {b[first]:,.0f}명 → {b[last]:,.0f}명 "
          f"({b[last] / b[first] - 1:+.1%}, 연평균 {cagr:+.2%})")

    section("2-3. 전년 대비 증감 (상위/하위 5개 연도)")
    yoy = pd.DataFrame({
        "births": b,
        "diff": b.diff(),
        "pct": b.pct_change() * 100,
    }).dropna()
    print("▼ 감소폭 큰 해\n", yoy.nsmallest(5, "pct").to_string())
    print("▲ 증가폭 큰 해\n", yoy.nlargest(5, "pct").to_string())
    streak, best, end = 0, 0, None
    for y, p in yoy["pct"].items():
        streak = streak + 1 if p < 0 else 0
        if streak > best:
            best, end = streak, y
    print(f"최장 연속 감소: {end - best + 1}~{end}년 ({best}년 연속)")

    section("2-4. 10년 단위(연대별) 평균")
    decade = df.groupby((df.index // 10) * 10).agg(
        births_mean=("births", "mean"),
        tfr_mean=("tfr", "mean"),
        sex_ratio_mean=("sex_ratio", "mean"),
        years=("births", "size"),
    )
    decade.index = [f"{d}년대" for d in decade.index]
    print(decade)

    section("2-5. 합계출산율 구간 분석")
    bins = [0, 1.0, 1.3, 2.1, 10]
    labels = ["1.0 미만(초초저출산)", "1.0~1.3(초저출산)", "1.3~2.1(저출산)", "2.1 이상(대체수준 이상)"]
    df_tfr = pd.cut(df["tfr"], bins=bins, labels=labels, right=False)
    print(df_tfr.value_counts().reindex(labels).to_string())
    print(f"대체출산율(2.1) 처음 미달: {df[df['tfr'] < 2.1].index.min()}년")
    print(f"1.3 미만 진입: {df[df['tfr'] < 1.3].index.min()}년")
    print(f"1.0 미만 진입: {df[df['tfr'] < 1.0].index.min()}년")
    print(f"TFR 최저: {df['tfr'].idxmin()}년 {df['tfr'].min():.3f}")

    section("2-6. 자연증가 (출생 - 사망) — 인구 데드크로스")
    neg = df[df["natural_increase"] < 0]
    print(f"자연감소 첫 해: {neg.index.min()}년 (자연감소 연속 {len(neg)}년)")
    print(df.loc[df.index >= 2015, ["births", "deaths", "natural_increase", "natural_increase_rate"]])

    section("2-7. 출생성비 추이 (정상범위 103~107)")
    abnormal = df[df["sex_ratio"] > 107]
    print(f"정상범위 초과 연도 수: {len(abnormal)}  "
          f"(최고 {df['sex_ratio'].idxmax()}년 {df['sex_ratio'].max():.1f})")
    print(f"정상범위 회복 이후 첫 해: "
          f"{df[(df.index > df['sex_ratio'].idxmax()) & (df['sex_ratio'] <= 107)].index.min()}년")

    section("2-8. 지표 간 상관관계 (Pearson)")
    print(df[["births", "deaths", "crude_birth_rate", "tfr", "sex_ratio"]].astype(float).corr())

    section("2-9. 최근 반등 여부 (최근 5년)")
    recent = df.loc[df.index >= last - 4, ["births", "tfr"]].copy()
    recent["births_yoy_%"] = b.pct_change().loc[recent.index] * 100
    recent["tfr_diff"] = df["tfr"].diff().loc[recent.index]
    print(recent)

    df.assign(births_ma5=b.rolling(5, center=True).mean()).to_csv(
        OUT_DIR / "births_with_ma.csv", encoding="utf-8-sig")


# ----------------------------------------------------------------------
# 3. 출생아수 라인 그래프 (1970~2025)
# ----------------------------------------------------------------------
def setup_korean_font() -> None:
    plt.rcParams["font.family"] = "Malgun Gothic"   # Windows 한글 폰트 (macOS: AppleGothic)
    plt.rcParams["axes.unicode_minus"] = False


def draw_births(ax, df: pd.DataFrame, start: int = 1970, end: int = 2025,
                show_ma: bool = True) -> None:
    """주어진 Axes 에 출생아수 라인 그래프를 그린다 (CLI·GUI 공용)."""
    s = df.loc[start:end, "births"].astype(float)
    start, end = int(s.index.min()), int(s.index.max())
    ax.plot(s.index, s.values, color="#2F6FD6", linewidth=2.2, marker="o", markersize=3.5,
            label="출생아수")
    if show_ma:
        ax.plot(s.index, s.rolling(5, center=True).mean(), color="#9AA4B2", linewidth=1.2,
                linestyle="--", label="5년 이동평균")

    # 주요 시점 주석
    for y, text, dy in [
        (s.idxmax(), "최고", 40_000),
        (s.idxmin(), "최저", -60_000),
        (end, "", 40_000),
    ]:
        ax.annotate(f"{text} {y}년\n{s[y]:,.0f}명".strip(), xy=(y, s[y]), xytext=(y, s[y] + dy),
                    ha="center", fontsize=9, color="#333",
                    arrowprops=dict(arrowstyle="-", color="#999", lw=0.8))

    ax.set_title(f"대한민국 연도별 출생아수 ({start}~{end})", fontsize=15, pad=12)
    ax.set_xlabel("연도")
    ax.set_ylabel("출생아수 (명)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 10_000:,.0f}만"))
    ax.set_xticks(range(start, end + 1, 5 if end - start > 20 else 1))
    ax.set_xlim(start - 1, end + 1)
    ax.set_ylim(0, s.max() * 1.12)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    ax.text(1, -0.1, "자료: 통계청 「인구동향조사」 (KOSIS)", transform=ax.transAxes,
            ha="right", fontsize=8, color="#777")


def plot_births(df: pd.DataFrame, start: int = 1970, end: int = 2025) -> None:
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(13, 6))
    draw_births(ax, df, start, end)
    fig.tight_layout()
    out = OUT_DIR / "births_1970_2025.png"
    fig.savefig(out, dpi=150)
    print(f"\n→ 그래프 저장: {out}")
    plt.show()


if __name__ == "__main__":
    data = load_and_clean(SRC)
    analyze(data)
    plot_births(data, 1970, 2025)
