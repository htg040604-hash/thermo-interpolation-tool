"""
extract_tables.py
열역학테이블.pdf에서 포화수 테이블(온도/압력 기준)과
과열증기 테이블을 파싱하여 CSV로 저장합니다.
"""

import pdfplumber
import pandas as pd
import re
import os

PDF_PATH = "열역학테이블.pdf"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# 유틸: 숫자 문자열 정리
# ─────────────────────────────────────────────
def clean_num(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    # 쉼표 천단위 구분자 제거
    try:
        return float(s)
    except ValueError:
        return None


# ─────────────────────────────────────────────
# 포화 테이블 파싱 (온도 기준 & 압력 기준)
# 컬럼: T_C, P_kPa, vf, vg, uf, ufg, ug, hf, hfg, hg, sf, sfg, sg
# ─────────────────────────────────────────────
SAT_HEADER = ["T_C", "P_kPa", "vf", "vg", "uf", "ufg", "ug", "hf", "hfg", "hg", "sf", "sfg", "sg"]

# 포화 테이블 행 패턴: 숫자로 시작하는 13개 값
SAT_ROW_RE = re.compile(
    r"^(-?\d[\d.,]*)\s+"   # col1 (T or P)
    r"(-?\d[\d.,]*)\s+"   # col2
    r"([\d.]+)\s+"         # vf
    r"([\d.]+)\s+"         # vg
    r"([\d.]+)\s+"         # uf
    r"([\d.]+)\s+"         # ufg
    r"([\d.]+)\s+"         # ug
    r"([\d.]+)\s+"         # hf
    r"([\d.]+)\s+"         # hfg
    r"([\d.]+)\s+"         # hg
    r"([\d.]+)\s+"         # sf
    r"([\d.]+)\s+"         # sfg
    r"([\d.]+)"            # sg
)

def parse_sat_table(pages, temp_first=True):
    """
    temp_first=True: 첫 컬럼이 온도(°C), 두 번째가 압력(kPa)
    temp_first=False: 첫 컬럼이 압력(kPa), 두 번째가 온도(°C)
    """
    rows = []
    for page in pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            m = SAT_ROW_RE.match(line)
            if m:
                vals = [clean_num(v) for v in m.groups()]
                if None in vals:
                    continue
                if temp_first:
                    row = {"T_C": vals[0], "P_kPa": vals[1]}
                else:
                    row = {"P_kPa": vals[0], "T_C": vals[1]}
                row.update({
                    "vf": vals[2], "vg": vals[3],
                    "uf": vals[4], "ufg": vals[5], "ug": vals[6],
                    "hf": vals[7], "hfg": vals[8], "hg": vals[9],
                    "sf": vals[10], "sfg": vals[11], "sg": vals[12]
                })
                rows.append(row)
    df = pd.DataFrame(rows, columns=SAT_HEADER)
    df = df.dropna().drop_duplicates()
    return df


# ─────────────────────────────────────────────
# 과열증기 테이블 파싱
# 멀티 블록: 각 블록이 "P = X MPa (Tsat°C)" 로 시작
# 각 행: T(°C)  v  u  h  s
# ─────────────────────────────────────────────
BLOCK_HEADER_RE = re.compile(
    r"P\s*=\s*([\d.]+)\s*MPa"
)
# 숫자 행: 온도(정수 또는 "Sat.") + 4개 실수
DATA_ROW_RE = re.compile(
    r"^(Sat\.|[\d]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
)

def parse_superheated_pages(pages):
    """
    각 페이지에서 과열증기 테이블 블록 추출.
    반환: DataFrame[P_MPa, T_C, v, u, h, s]
    """
    rows = []
    current_pressures = []  # 한 줄에 최대 3개 P값 동시 존재

    for page in pages:
        text = page.extract_text()
        if not text:
            continue

        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 새 블록 헤더 탐지 (P = X MPa ... P = Y MPa ... )
            found_ps = BLOCK_HEADER_RE.findall(line)
            if found_ps:
                current_pressures = [float(p) for p in found_ps]
                i += 1
                continue

            # 데이터 행: 한 줄에 여러 블록 데이터가 나란히 있을 수 있음
            # 예: "350  0.05461  2668.9  2887.3  6.2312  0.04733  ..."
            # 숫자들을 공백으로 분리
            parts = line.split()
            if not parts:
                i += 1
                continue

            # 첫 토큰이 "Sat." 또는 정수 온도
            if parts[0] in ("Sat.", "Sat") or (parts[0].lstrip("-").isdigit()):
                # T값 결정
                if parts[0] in ("Sat.", "Sat"):
                    T_val = None  # Sat. 포화온도는 압력 헤더에서 괄호로 나옴
                    T_str = "Sat."
                    num_parts = parts[1:]
                else:
                    T_val = float(parts[0])
                    T_str = parts[0]
                    num_parts = parts[1:]

                # num_parts를 4개씩 묶어서 각 P블록에 배정
                # 각 블록: v, u, h, s
                vals = []
                for p in num_parts:
                    try:
                        vals.append(float(p))
                    except ValueError:
                        break

                n_blocks = len(current_pressures)
                for b in range(n_blocks):
                    start = b * 4
                    if start + 3 < len(vals):
                        v_, u_, h_, s_ = vals[start], vals[start+1], vals[start+2], vals[start+3]
                        rows.append({
                            "P_MPa": current_pressures[b],
                            "T_label": T_str,
                            "T_C": T_val,
                            "v": v_,
                            "u": u_,
                            "h": h_,
                            "s": s_
                        })
            i += 1

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.dropna(subset=["v", "u", "h", "s"])
    df = df.reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    pdf = pdfplumber.open(PDF_PATH)
    pages = pdf.pages
    n = len(pages)
    print(f"총 페이지: {n}")

    # 포화 테이블 - 온도 기준 (페이지 1 ~ 2)
    print("포화 테이블(온도 기준) 파싱 중...")
    df_sat_temp = parse_sat_table(pages[0:2], temp_first=True)
    print(f"  → {len(df_sat_temp)} 행 추출")
    df_sat_temp.to_csv(f"{DATA_DIR}/sat_temp.csv", index=False)

    # 포화 테이블 - 압력 기준 (페이지 3 ~ 4)
    print("포화 테이블(압력 기준) 파싱 중...")
    df_sat_press = parse_sat_table(pages[2:4], temp_first=False)
    print(f"  → {len(df_sat_press)} 행 추출")
    df_sat_press.to_csv(f"{DATA_DIR}/sat_press.csv", index=False)

    # 과열증기 테이블 (페이지 5 ~ 끝)
    print("과열증기 테이블 파싱 중...")
    df_sup = parse_superheated_pages(pages[4:])
    print(f"  → {len(df_sup)} 행 추출")
    df_sup.to_csv(f"{DATA_DIR}/superheated.csv", index=False)

    print("\n✅ 모든 CSV 파일 저장 완료!")
    print(f"\n[포화 테이블 - 온도 기준 샘플]")
    print(df_sat_temp.head(5).to_string(index=False))
    print(f"\n[포화 테이블 - 압력 기준 샘플]")
    print(df_sat_press.head(5).to_string(index=False))
    print(f"\n[과열증기 테이블 샘플]")
    if not df_sup.empty:
        print(df_sup.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
