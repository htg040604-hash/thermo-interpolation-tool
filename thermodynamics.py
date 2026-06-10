"""
thermodynamics.py
수증기 열역학 상태량 계산 엔진

- 포화 테이블 (온도/압력 기준) 선형 보간
- 상(Phase) 판정: 압축액 / 포화 혼합물 / 과열증기
- 건도(x) 계산
- 과열증기 이중 선형 보간
"""

import pandas as pd
import numpy as np
import os

# ─────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

_sat_temp  = pd.read_csv(os.path.join(_DATA_DIR, "sat_temp.csv")).sort_values("T_C").reset_index(drop=True)
_sat_press = pd.read_csv(os.path.join(_DATA_DIR, "sat_press.csv")).sort_values("P_kPa").reset_index(drop=True)
_sup_raw   = pd.read_csv(os.path.join(_DATA_DIR, "superheated.csv"))

# 과열증기: Sat. 행 분리 및 T_C가 있는 행만 사용
_sup_data = _sup_raw.dropna(subset=["T_C"]).copy()
_sup_sat  = _sup_raw[_sup_raw["T_label"] == "Sat."].copy()

SAT_PROPS = ["vf", "vg", "uf", "ufg", "ug", "hf", "hfg", "hg", "sf", "sfg", "sg"]
PROP_NAMES = ["v", "u", "h", "s"]

# ─────────────────────────────────────────────
# 범위 정보
# ─────────────────────────────────────────────
T_MIN = float(_sat_temp["T_C"].min())
T_MAX = float(_sat_temp["T_C"].max())
P_MIN_kPa = float(_sat_press["P_kPa"].min())
P_MAX_kPa = float(_sat_press["P_kPa"].max())
SUP_P_MIN_MPa = float(_sup_data["P_MPa"].min())
SUP_P_MAX_MPa = float(_sup_data["P_MPa"].max())


# ─────────────────────────────────────────────
# 유틸: 1D 선형 보간
# ─────────────────────────────────────────────
def _interp1d(x_arr, y_arr, x_val):
    """x_arr이 정렬된 배열, x_val에 대해 선형 보간."""
    x_arr = np.asarray(x_arr, dtype=float)
    y_arr = np.asarray(y_arr, dtype=float)
    if x_val <= x_arr[0]:
        return float(y_arr[0])
    if x_val >= x_arr[-1]:
        return float(y_arr[-1])
    idx = np.searchsorted(x_arr, x_val) - 1
    x0, x1 = x_arr[idx], x_arr[idx + 1]
    y0, y1 = y_arr[idx], y_arr[idx + 1]
    return float(y0 + (y1 - y0) * (x_val - x0) / (x1 - x0))


# ─────────────────────────────────────────────
# 포화 상태량 조회 (온도 또는 압력 기준)
# ─────────────────────────────────────────────
def get_sat_props_by_T(T_C: float) -> dict:
    """온도(°C)로 포화 상태량(f, fg, g) 반환."""
    if T_C < T_MIN or T_C > T_MAX:
        raise ValueError(f"온도 범위 초과: {T_C}°C (허용: {T_MIN}~{T_MAX}°C)")
    df = _sat_temp
    result = {"T_C": T_C}
    result["P_kPa"] = _interp1d(df["T_C"], df["P_kPa"], T_C)
    for col in SAT_PROPS:
        result[col] = _interp1d(df["T_C"], df[col], T_C)
    return result


def get_sat_props_by_P(P_kPa: float) -> dict:
    """압력(kPa)으로 포화 상태량(f, fg, g) 반환."""
    if P_kPa < P_MIN_kPa or P_kPa > P_MAX_kPa:
        raise ValueError(f"압력 범위 초과: {P_kPa} kPa (허용: {P_MIN_kPa}~{P_MAX_kPa} kPa)")
    df = _sat_press
    result = {"P_kPa": P_kPa}
    result["T_C"] = _interp1d(df["P_kPa"], df["T_C"], P_kPa)
    for col in SAT_PROPS:
        result[col] = _interp1d(df["P_kPa"], df[col], P_kPa)
    return result


# ─────────────────────────────────────────────
# 상(Phase) 판정 및 건도 계산
# ─────────────────────────────────────────────
PHASE_SUBCOOLED  = "압축액 (Subcooled Liquid)"
PHASE_MIXTURE    = "포화 혼합물 (Saturated Mixture)"
PHASE_SUPERHEATED = "과열증기 (Superheated Vapor)"
PHASE_SAT_LIQ    = "포화액 (Saturated Liquid)"
PHASE_SAT_VAP    = "포화증기 (Saturated Vapor)"


def determine_phase(prop: str, val: float, sat: dict):
    """
    prop: 'v', 'u', 'h', 's'
    val: 사용자 입력값
    sat: get_sat_props_by_T 또는 get_sat_props_by_P 반환값
    반환: (phase_str, x)
    """
    f_val = sat[f"{prop}f"]
    g_val = sat[f"{prop}g"]

    if val < f_val:
        return PHASE_SUBCOOLED, None
    elif val > g_val:
        return PHASE_SUPERHEATED, None
    else:
        # 포화 혼합물
        if abs(g_val - f_val) < 1e-12:
            x = 0.0
        else:
            x = (val - f_val) / (g_val - f_val)
        x = max(0.0, min(1.0, x))
        if x == 0.0:
            return PHASE_SAT_LIQ, 0.0
        elif x == 1.0:
            return PHASE_SAT_VAP, 1.0
        return PHASE_MIXTURE, x


# ─────────────────────────────────────────────
# 포화 혼합물 상태량 계산
# ─────────────────────────────────────────────
def calc_sat_mixture_props(x: float, sat: dict) -> dict:
    """
    건도 x와 포화 상태량 딕셔너리로 전체 상태량 계산.
    M = Mf + x * (Mg - Mf)
    """
    return {
        "T_C": sat["T_C"],
        "P_kPa": sat["P_kPa"],
        "v": sat["vf"] + x * (sat["vg"] - sat["vf"]),
        "u": sat["uf"] + x * (sat["ug"] - sat["uf"]),
        "h": sat["hf"] + x * (sat["hg"] - sat["hf"]),
        "s": sat["sf"] + x * (sat["sg"] - sat["sf"]),
    }


# ─────────────────────────────────────────────
# 압축액 상태량 (포화액 근사 적용)
# 압축액 별도 테이블 없음 → 같은 온도의 포화액 값 사용 (표준 근사)
# ─────────────────────────────────────────────
def calc_subcooled_props(T_C: float, P_kPa: float) -> dict:
    """
    압축액 상태량 = 같은 온도의 포화액 값 (표준 근사)
    단, 엔탈피는 h ≈ hf(T) + vf(T) * (P - Psat(T)) 보정 적용
    """
    sat = get_sat_props_by_T(T_C)
    P_sat = sat["P_kPa"]
    vf = sat["vf"]
    # 엔탈피 보정 (단위: kJ/kg, 압력차 kPa → kPa*m³/kg = kJ/kg)
    h_corr = sat["hf"] + vf * (P_kPa - P_sat)
    return {
        "T_C": T_C,
        "P_kPa": P_kPa,
        "v": sat["vf"],
        "u": sat["uf"],
        "h": h_corr,
        "s": sat["sf"],
    }


# ─────────────────────────────────────────────
# 과열증기 이중 선형 보간
# ─────────────────────────────────────────────
def _get_nearest_pressures(P_MPa: float):
    """사용 가능한 과열증기 테이블 압력 중 보간에 쓸 두 값."""
    avail = sorted(_sup_data["P_MPa"].unique())
    if P_MPa <= avail[0]:
        return avail[0], avail[0]
    if P_MPa >= avail[-1]:
        return avail[-1], avail[-1]
    idx = next(i for i, p in enumerate(avail) if p >= P_MPa)
    if avail[idx] == P_MPa:
        return P_MPa, P_MPa
    return avail[idx - 1], avail[idx]


def _interp_at_pressure(P_MPa: float, T_C: float) -> dict:
    """단일 압력 레벨에서 T_C 기준으로 v, u, h, s 선형 보간."""
    df = _sup_data[_sup_data["P_MPa"] == P_MPa].sort_values("T_C")
    if df.empty:
        raise ValueError(f"과열증기 테이블에 P={P_MPa} MPa 없음")
    result = {}
    for prop in PROP_NAMES:
        result[prop] = _interp1d(df["T_C"].values, df[prop].values, T_C)
    return result


def calc_superheated_props(P_kPa: float, T_C: float) -> dict:
    """
    과열증기 상태량: 압력(kPa)과 온도(°C)로 이중 선형 보간.
    """
    P_MPa = P_kPa / 1000.0
    avail = sorted(_sup_data["P_MPa"].unique())

    if P_MPa < avail[0] or P_MPa > avail[-1]:
        raise ValueError(
            f"과열증기 압력 범위 초과: {P_MPa} MPa "
            f"(허용: {avail[0]}~{avail[-1]} MPa)"
        )

    # 온도 범위 검사 (해당 압력에서)
    P_lo, P_hi = _get_nearest_pressures(P_MPa)
    df_lo = _sup_data[_sup_data["P_MPa"] == P_lo]
    T_min = float(df_lo["T_C"].min())

    if T_C < T_min:
        raise ValueError(
            f"P={P_MPa} MPa에서 온도가 낮습니다 (최소 과열 온도 ≈ {T_min}°C). "
            f"입력 T={T_C}°C는 포화 또는 압축액 영역입니다."
        )

    if P_lo == P_hi:
        props = _interp_at_pressure(P_lo, T_C)
    else:
        props_lo = _interp_at_pressure(P_lo, T_C)
        props_hi = _interp_at_pressure(P_hi, T_C)
        # P에 대해 선형 보간
        alpha = (P_MPa - P_lo) / (P_hi - P_lo)
        props = {
            prop: props_lo[prop] + alpha * (props_hi[prop] - props_lo[prop])
            for prop in PROP_NAMES
        }

    return {
        "T_C": T_C,
        "P_kPa": P_kPa,
        **props
    }


# ─────────────────────────────────────────────
# 메인 계산 함수 (외부 호출용)
# ─────────────────────────────────────────────
def calculate_state(indep_var: str, indep_val: float,
                    second_prop: str, second_val: float) -> dict:
    """
    Parameters
    ----------
    indep_var : 'T' 또는 'P'
    indep_val : 온도(°C) 또는 압력(kPa) 값
    second_prop : 'v', 'u', 'h', 's' 중 하나
    second_val : 두 번째 상태량 값

    Returns
    -------
    {
        'phase': str,
        'x': float or None,
        'x_display': str,
        'T_C': float,
        'P_kPa': float,
        'v': float,
        'u': float,
        'h': float,
        's': float,
    }
    """
    # 1) 포화 상태량 취득
    if indep_var == "T":
        T_C = indep_val
        sat = get_sat_props_by_T(T_C)
        P_kPa = sat["P_kPa"]
    else:  # 'P'
        P_kPa = indep_val
        sat = get_sat_props_by_P(P_kPa)
        T_C = sat["T_C"]

    # 2) 상 판정
    phase, x = determine_phase(second_prop, second_val, sat)

    # 3) 상별 상태량 계산
    if phase in (PHASE_MIXTURE, PHASE_SAT_LIQ, PHASE_SAT_VAP):
        props = calc_sat_mixture_props(x, sat)
        if x == 0.0:
            x_display = "x = 0 (포화액)"
        elif x == 1.0:
            x_display = "x = 1 (포화증기)"
        else:
            x_display = f"x = {x:.4f}"

    elif phase == PHASE_SUPERHEATED:
        # 과열증기: 두 번째 상태량과 독립변수로 T, P 결정
        if indep_var == "T":
            # T 알고 있음, P는 포화압보다 낮아야 과열 → 상태량으로 P 추정 불가
            # 대신 T로 포화 Tsat을 이용: 입력T에서 과열이므로 P_sat은 알 수 없음
            # → 근사: 포화압에서 T로 구하면 됨. 과열증기는 P를 독립변수로만 정확히 보간 가능
            # 여기선 보수적으로 포화압(해당 T에서)을 사용하고 second_prop으로 보완
            # 실제로는 two-property 문제 → 반복법 필요
            # 간단화: sat.P_kPa에서 T로 과열증기 구함 (T,P 둘 다 알아야 하는데 T만 앎)
            # second_prop == 'h': T=const에서 h로 P를 추정 → 실용적으로 포화압 사용
            try:
                props = calc_superheated_props(P_kPa, T_C)
            except ValueError:
                # 포화압에서는 과열 안 됨 → 실제 P는 Psat보다 낮음
                # 이중 보간으로 처리
                props = _estimate_superheated_from_T_and_prop(T_C, second_prop, second_val, sat)
        else:  # P 알고 있음
            # P 알고 second_prop 알고 있으면 T를 추정해야 함
            # T를 이분법으로 추정
            T_est = _estimate_T_from_P_and_prop(P_kPa, second_prop, second_val)
            props = calc_superheated_props(P_kPa, T_est)

        x_display = "x = 해당 없음 (> 1, 과열증기)"
        x = None

    else:  # PHASE_SUBCOOLED
        if indep_var == "T":
            props = calc_subcooled_props(T_C, P_kPa)
        else:
            props = calc_subcooled_props(T_C, P_kPa)
        x_display = "x = 해당 없음 (< 0, 압축액)"
        x = None

    return {
        "phase": phase,
        "x": x,
        "x_display": x_display,
        "T_C":   props["T_C"],
        "P_kPa": props["P_kPa"],
        "v":     props["v"],
        "u":     props["u"],
        "h":     props["h"],
        "s":     props["s"],
    }


# ─────────────────────────────────────────────
# 보조: 과열증기에서 T 추정 (이분법)
# ─────────────────────────────────────────────
def _estimate_T_from_P_and_prop(P_kPa: float, prop: str, val: float,
                                  T_lo: float = None, T_hi: float = 1300.0,
                                  tol: float = 1e-4, max_iter: int = 100) -> float:
    """
    주어진 P와 두 번째 상태량(prop=val)으로 과열증기 온도 T를 이분법으로 추정.
    """
    P_MPa = P_kPa / 1000.0
    avail = sorted(_sup_data["P_MPa"].unique())
    P_lo_avail, P_hi_avail = _get_nearest_pressures(P_MPa)
    df_lo = _sup_data[_sup_data["P_MPa"] == P_lo_avail]

    if T_lo is None:
        T_lo = float(df_lo["T_C"].min())

    def f(T):
        try:
            props = calc_superheated_props(P_kPa, T)
            return props[prop] - val
        except Exception:
            return None

    f_lo = f(T_lo)
    f_hi = f(T_hi)

    if f_lo is None or f_hi is None:
        raise ValueError("과열증기 보간 실패")

    # prop이 단조 증가/감소인지 확인
    if f_lo * f_hi > 0:
        # 같은 부호: 범위를 넓혀봄
        T_hi = 1300.0
        f_hi = f(T_hi)
        if f_lo is None or (f_lo * f_hi > 0):
            raise ValueError(f"과열증기 테이블에서 {prop}={val} 찾기 실패")

    for _ in range(max_iter):
        T_mid = (T_lo + T_hi) / 2.0
        f_mid = f(T_mid)
        if f_mid is None:
            break
        if abs(f_mid) < tol or (T_hi - T_lo) < 0.001:
            return T_mid
        if f_lo * f_mid <= 0:
            T_hi = T_mid
            f_hi = f_mid
        else:
            T_lo = T_mid
            f_lo = f_mid
    return (T_lo + T_hi) / 2.0


def _estimate_superheated_from_T_and_prop(T_C: float, prop: str, val: float,
                                            sat: dict) -> dict:
    """
    T와 두 번째 상태량으로 과열증기 P를 추정 (이분법).
    T가 고정이고, P가 Psat보다 낮은 경우.
    """
    P_sat_MPa = sat["P_kPa"] / 1000.0
    avail = sorted(_sup_data["P_MPa"].unique())
    P_lo_MPa = avail[0]

    def f(P_MPa):
        try:
            props = _interp_at_pressure_bilinear(P_MPa, T_C)
            return props[prop] - val
        except Exception:
            return None

    f_lo = f(P_lo_MPa)
    f_hi = f(P_sat_MPa * 0.9999)

    if f_lo is None or f_hi is None or f_lo * f_hi > 0:
        # 이분법 실패 시 P_lo에서의 값 반환
        props = _interp_at_pressure_bilinear(P_lo_MPa, T_C)
        props["T_C"] = T_C
        props["P_kPa"] = P_lo_MPa * 1000
        return props

    for _ in range(100):
        P_mid = (P_lo_MPa + P_sat_MPa * 0.9999) / 2.0
        f_mid = f(P_mid)
        if f_mid is None:
            break
        if abs(f_mid) < 1e-4 or abs(P_sat_MPa - P_lo_MPa) < 1e-6:
            P_MPa = P_mid
            break
        if f_lo * f_mid <= 0:
            P_sat_MPa = P_mid
            f_hi = f_mid
        else:
            P_lo_MPa = P_mid
            f_lo = f_mid
    else:
        P_MPa = (P_lo_MPa + P_sat_MPa) / 2.0

    props = _interp_at_pressure_bilinear(P_MPa, T_C)
    props["T_C"] = T_C
    props["P_kPa"] = P_MPa * 1000
    return props


def _interp_at_pressure_bilinear(P_MPa: float, T_C: float) -> dict:
    """P_MPa에서 T_C의 상태량 (P 보간 포함)."""
    P_lo, P_hi = _get_nearest_pressures(P_MPa)
    if P_lo == P_hi:
        return _interp_at_pressure(P_lo, T_C)
    props_lo = _interp_at_pressure(P_lo, T_C)
    props_hi = _interp_at_pressure(P_hi, T_C)
    alpha = (P_MPa - P_lo) / (P_hi - P_lo)
    return {
        prop: props_lo[prop] + alpha * (props_hi[prop] - props_lo[prop])
        for prop in PROP_NAMES
    }
