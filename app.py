"""
app.py - 수증기 상태량 계산기 (Streamlit 웹 앱)
건도(Quality, x) 계산 및 열역학 상태량 보간 프로그램
"""

import streamlit as st
import pandas as pd
import numpy as np

# ── 페이지 설정 ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="수증기 상태량 계산기",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 커스텀 CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── 전체 배경 ── */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    font-family: 'Inter', sans-serif;
}

/* ── 헤더 ── */
.hero-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem 0;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.4rem;
    letter-spacing: -0.02em;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    font-weight: 400;
}

/* ── 카드 ── */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── 상태 뱃지 ── */
.phase-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.6rem 1.4rem;
    border-radius: 50px;
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0.5rem 0 1rem 0;
}
.badge-subcooled {
    background: linear-gradient(135deg, #1e40af22, #3b82f633);
    border: 1.5px solid #3b82f6;
    color: #93c5fd;
}
.badge-mixture {
    background: linear-gradient(135deg, #92400e22, #f59e0b33);
    border: 1.5px solid #f59e0b;
    color: #fcd34d;
}
.badge-superheated {
    background: linear-gradient(135deg, #7f1d1d22, #ef444433);
    border: 1.5px solid #ef4444;
    color: #fca5a5;
}
.badge-sat-liq {
    background: linear-gradient(135deg, #1e3a5f22, #0ea5e933);
    border: 1.5px solid #0ea5e9;
    color: #7dd3fc;
}
.badge-sat-vap {
    background: linear-gradient(135deg, #4a1d4a22, #a855f733);
    border: 1.5px solid #a855f7;
    color: #d8b4fe;
}

/* ── 건도 표시 ── */
.quality-display {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.2rem;
}
.quality-label {
    color: #94a3b8;
    font-size: 0.82rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}
.quality-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #f8fafc;
}

/* ── 상태량 표 ── */
.state-table {
    width: 100%;
    border-collapse: collapse;
    border-radius: 12px;
    overflow: hidden;
    font-size: 0.9rem;
}
.state-table thead tr {
    background: rgba(167, 139, 250, 0.15);
}
.state-table thead th {
    padding: 0.7rem 1rem;
    text-align: left;
    color: #c4b5fd;
    font-weight: 600;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.state-table tbody tr {
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: background 0.15s;
}
.state-table tbody tr:hover {
    background: rgba(255,255,255,0.05);
}
.state-table tbody td {
    padding: 0.65rem 1rem;
    color: #e2e8f0;
}
.state-table tbody td:first-child {
    color: #94a3b8;
    font-weight: 500;
}
.state-table tbody td:nth-child(3) {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    color: #f8fafc;
    font-weight: 500;
}
.state-table tbody td:last-child {
    color: #64748b;
    font-size: 0.82rem;
}
.highlighted-row {
    background: rgba(167, 139, 250, 0.1) !important;
}
.highlighted-row td:nth-child(3) {
    color: #a78bfa !important;
}

/* ── 구분선 ── */
.divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1rem 0;
}

/* ── 도움말 ── */
.help-text {
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}

/* ── 버튼 ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 25px rgba(124, 58, 237, 0.5) !important;
}

/* ── Streamlit 기본 요소 스타일 오버라이드 ── */
.stSelectbox label, .stNumberInput label, .stRadio label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
.stSelectbox > div > div, .stNumberInput > div > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}
div[data-testid="stRadio"] > div {
    gap: 0.5rem;
}
.stRadio > div > label {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.8rem !important;
    color: #cbd5e1 !important;
}

/* ── 정보 박스 ── */
.info-box {
    background: rgba(96, 165, 250, 0.08);
    border: 1px solid rgba(96, 165, 250, 0.25);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    color: #93c5fd;
    font-size: 0.85rem;
    margin: 0.5rem 0;
}
.warning-box {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    color: #fcd34d;
    font-size: 0.85rem;
}
.error-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    color: #fca5a5;
    font-size: 0.88rem;
}
</style>
""", unsafe_allow_html=True)


# ── 열역학 엔진 임포트 ──────────────────────────────────────────────
try:
    from thermodynamics import (
        calculate_state,
        T_MIN, T_MAX, P_MIN_kPa, P_MAX_kPa,
        PHASE_SUBCOOLED, PHASE_MIXTURE, PHASE_SUPERHEATED,
        PHASE_SAT_LIQ, PHASE_SAT_VAP,
        get_sat_props_by_T, get_sat_props_by_P
    )
    ENGINE_OK = True
except Exception as e:
    ENGINE_OK = False
    ENGINE_ERROR = str(e)


# ── 헤더 ────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🌡️ 수증기 상태량 계산기</div>
    <div class="hero-subtitle">
        건도(Quality, x) 계산 및 열역학 상태량 보간 프로그램 &nbsp;·&nbsp;
        IAPWS-IF97 기반 스팀 테이블 (SI 단위)
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

if not ENGINE_OK:
    st.error(f"열역학 엔진 로드 실패: {ENGINE_ERROR}")
    st.stop()


# ── 레이아웃: 좌측 입력 / 우측 결과 ─────────────────────────────────
col_in, col_out = st.columns([1, 1.4], gap="large")

with col_in:
    st.markdown("""
    <div class="glass-card">
        <div class="card-title">⚙️ 입력 조건 설정</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 독립변수 선택 ──
    st.markdown('<p style="color:#94a3b8;font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">📌 독립변수 선택</p>', unsafe_allow_html=True)
    indep_choice = st.radio(
        "독립변수",
        options=["온도 T (°C)", "압력 P (kPa)"],
        horizontal=True,
        label_visibility="collapsed",
        key="indep_choice"
    )
    indep_var = "T" if "T" in indep_choice else "P"

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── 독립변수 값 입력 ──
    if indep_var == "T":
        indep_val = st.number_input(
            f"온도 T [°C]  (범위: {T_MIN} ~ {T_MAX}°C)",
            min_value=T_MIN,
            max_value=T_MAX,
            value=150.0,
            step=1.0,
            format="%.2f",
            key="T_input"
        )
        st.markdown(f'<p class="help-text">포화 테이블 범위: {T_MIN} ~ {T_MAX} °C</p>', unsafe_allow_html=True)
    else:
        indep_val = st.number_input(
            f"압력 P [kPa]  (범위: {P_MIN_kPa:.1f} ~ {P_MAX_kPa:.0f} kPa)",
            min_value=P_MIN_kPa,
            max_value=P_MAX_kPa,
            value=476.16,
            step=1.0,
            format="%.2f",
            key="P_input"
        )
        st.markdown(f'<p class="help-p style="color:#64748b;font-size:0.8rem;">포화 테이블 범위: {P_MIN_kPa:.1f} ~ {P_MAX_kPa:.0f} kPa</p>', unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 두 번째 상태량 선택 ──
    st.markdown('<p style="color:#94a3b8;font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">📊 두 번째 상태량 선택</p>', unsafe_allow_html=True)
    prop_options = {
        "비체적 v [m³/kg]":     "v",
        "내부에너지 u [kJ/kg]": "u",
        "엔탈피 h [kJ/kg]":     "h",
        "엔트로피 s [kJ/kg·K]": "s",
    }
    prop_label = st.selectbox(
        "상태량",
        options=list(prop_options.keys()),
        index=2,  # 기본: 엔탈피
        label_visibility="collapsed",
        key="prop_select"
    )
    second_prop = prop_options[prop_label]

    # ── 두 번째 상태량 값 입력 ──
    PROP_DEFAULTS = {"v": 0.3924, "u": 1927.4, "h": 2746.0, "s": 6.837}
    PROP_FORMATS  = {"v": "%.5f", "u": "%.3f", "h": "%.3f", "s": "%.4f"}
    PROP_STEPS    = {"v": 0.001,  "u": 0.1,    "h": 0.1,    "s": 0.001}
    PROP_UNITS    = {"v": "m³/kg", "u": "kJ/kg", "h": "kJ/kg", "s": "kJ/kg·K"}

    second_val = st.number_input(
        f"{prop_label}의 값",
        value=PROP_DEFAULTS[second_prop],
        step=PROP_STEPS[second_prop],
        format=PROP_FORMATS[second_prop],
        key="second_val"
    )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # ── 포화 상태량 미리 보기 ──
    with st.expander("📋 포화 상태량 참고값 보기", expanded=False):
        try:
            if indep_var == "T":
                sat_ref = get_sat_props_by_T(indep_val)
            else:
                sat_ref = get_sat_props_by_P(indep_val)

            ref_data = {
                "상태량": ["vf", "vg", "hf", "hg", "sf", "sg"],
                "값": [
                    f"{sat_ref['vf']:.6f}",
                    f"{sat_ref['vg']:.5f}",
                    f"{sat_ref['hf']:.3f}",
                    f"{sat_ref['hg']:.3f}",
                    f"{sat_ref['sf']:.4f}",
                    f"{sat_ref['sg']:.4f}",
                ],
                "단위": ["m³/kg","m³/kg","kJ/kg","kJ/kg","kJ/kg·K","kJ/kg·K"],
            }
            ref_df = pd.DataFrame(ref_data)
            st.dataframe(
                ref_df, use_container_width=True, hide_index=True,
                column_config={
                    "상태량": st.column_config.TextColumn(width="small"),
                    "값": st.column_config.TextColumn(width="medium"),
                    "단위": st.column_config.TextColumn(width="medium"),
                }
            )
            sat_T = sat_ref['T_C']
            sat_P = sat_ref['P_kPa']
            st.markdown(f'<p class="help-text">포화 온도: {sat_T:.2f} °C | 포화 압력: {sat_P:.3f} kPa</p>', unsafe_allow_html=True)
        except ValueError as e:
            st.warning(str(e))

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── 계산 버튼 ──
    calc_btn = st.button("🔬 계산하기", key="calc_btn", use_container_width=True)


# ── 결과 패널 ─────────────────────────────────────────────────────────
with col_out:
    st.markdown("""
    <div class="glass-card">
        <div class="card-title">📊 계산 결과</div>
    </div>
    """, unsafe_allow_html=True)

    if not calc_btn:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 4rem 2rem;
            color: #475569;
        ">
            <div style="font-size: 3.5rem; margin-bottom: 1rem;">⚗️</div>
            <div style="font-size: 1.1rem; font-weight: 500; color: #64748b;">
                좌측에서 조건을 입력하고<br>
                <span style="color:#7c3aed;">'계산하기'</span> 버튼을 눌러 주세요
            </div>
            <div style="margin-top: 1rem; font-size: 0.85rem; color: #334155;">
                독립변수 + 두 번째 상태량으로 상(Phase) 판정 및<br>
                전체 상태량을 자동으로 계산합니다
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # ── 계산 실행 ──
        try:
            result = calculate_state(indep_var, indep_val, second_prop, second_val)
            phase   = result["phase"]
            x       = result["x"]
            x_disp  = result["x_display"]

            # ── 상태 뱃지 ──
            PHASE_ICONS = {
                PHASE_SUBCOOLED:   ("💧", "badge-subcooled"),
                PHASE_MIXTURE:     ("⚡", "badge-mixture"),
                PHASE_SUPERHEATED: ("🔥", "badge-superheated"),
                PHASE_SAT_LIQ:     ("🔵", "badge-sat-liq"),
                PHASE_SAT_VAP:     ("🟣", "badge-sat-vap"),
            }
            icon, badge_cls = PHASE_ICONS.get(phase, ("❓", "badge-mixture"))

            st.markdown(f"""
            <div style="margin-bottom: 0.5rem;">
                <p style="color:#94a3b8;font-size:0.82rem;font-weight:600;
                          text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">
                    현재 상태 (Phase)
                </p>
                <div class="phase-badge {badge_cls}">
                    {icon} {phase}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── 건도 표시 ──
            if x is not None:
                # 건도 게이지 바
                pct = int(x * 100)
                bar_color = "#f59e0b"
                st.markdown(f"""
                <div class="quality-display">
                    <div class="quality-label">건도 (Quality, x)</div>
                    <div class="quality-value">{x_disp}</div>
                    <div style="margin-top:0.7rem;">
                        <div style="background:rgba(255,255,255,0.08);border-radius:6px;height:8px;overflow:hidden;">
                            <div style="
                                width:{pct}%;
                                height:100%;
                                background: linear-gradient(90deg, #3b82f6, {bar_color}, #ef4444);
                                border-radius:6px;
                                transition: width 0.4s ease;
                            "></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;
                                    color:#475569;font-size:0.75rem;margin-top:0.3rem;">
                            <span>0 (포화액)</span>
                            <span>1 (포화증기)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                x_color = "#64748b"
                st.markdown(f"""
                <div class="quality-display">
                    <div class="quality-label">건도 (Quality, x)</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;
                                color:#64748b;font-weight:400;">{x_disp}</div>
                </div>
                """, unsafe_allow_html=True)

            # ── 상태량 표 ──
            PROP_ROWS = [
                ("온도", "T", f"{result['T_C']:.3f}", "°C"),
                ("압력", "P", f"{result['P_kPa']:.4f}", "kPa"),
                ("비체적", "v", f"{result['v']:.6f}", "m³/kg"),
                ("내부에너지", "u", f"{result['u']:.3f}", "kJ/kg"),
                ("엔탈피", "h", f"{result['h']:.3f}", "kJ/kg"),
                ("엔트로피", "s", f"{result['s']:.5f}", "kJ/kg·K"),
            ]

            # 입력한 두 번째 상태량에 하이라이트
            PROP_TO_NAME = {"v": "비체적", "u": "내부에너지", "h": "엔탈피", "s": "엔트로피"}
            highlight_name = PROP_TO_NAME[second_prop]
            if indep_var == "T":
                highlight_indep = "온도"
            else:
                highlight_indep = "압력"

            rows_html = ""
            for name, sym, val_str, unit in PROP_ROWS:
                is_input = (name == highlight_name or name == highlight_indep)
                row_cls = "highlighted-row" if is_input else ""
                input_marker = " ⬅ 입력값" if is_input else ""
                rows_html += f"""
                <tr class="{row_cls}">
                    <td>{name}</td>
                    <td style="color:#7c3aed;font-family:'JetBrains Mono',monospace;">{sym}</td>
                    <td>{val_str}{input_marker}</td>
                    <td>{unit}</td>
                </tr>"""

            st.markdown(f"""
            <p style="color:#94a3b8;font-size:0.82rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">
                최종 상태량
            </p>
            <table class="state-table">
                <thead>
                    <tr>
                        <th>상태량</th>
                        <th>기호</th>
                        <th>값</th>
                        <th>단위</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """, unsafe_allow_html=True)

            # ── 계산 방법 요약 ──
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            if phase in (PHASE_MIXTURE, PHASE_SAT_LIQ, PHASE_SAT_VAP):
                method_txt = f"포화 혼합물 공식: M = M_f + x·(M_g - M_f), x = {x:.4f}" if x is not None else ""
            elif phase == PHASE_SUPERHEATED:
                method_txt = "과열증기 테이블 이중 선형 보간 (P, T 기준)"
            else:
                method_txt = "압축액 근사: 동일 온도의 포화액(f) 값 사용 + 엔탈피 압력 보정"

            st.markdown(f"""
            <div class="info-box">
                <strong>계산 방법:</strong> {method_txt}
            </div>
            """, unsafe_allow_html=True)

        except ValueError as e:
            err_msg = str(e)
            if "범위" in err_msg or "range" in err_msg.lower():
                st.markdown(f"""
                <div class="error-box">
                    ⚠️ <strong>테이블 범위를 벗어난 입력값입니다.</strong><br>
                    <small>{err_msg}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="warning-box">
                    ⚠️ 계산 중 오류가 발생했습니다: {err_msg}
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                ❌ 예상치 못한 오류: {str(e)}
            </div>
            """, unsafe_allow_html=True)
            st.exception(e)


# ── 하단 정보 ────────────────────────────────────────────────────────
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
st.markdown("""
<hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:0 0 0.8rem 0;">
<div style="text-align:center;color:#334155;font-size:0.78rem;">
    데이터 출처: IAPWS-IF97 기반 스팀 테이블 (Cengel & Boles, Thermodynamics, Appendix) &nbsp;·&nbsp;
    SI 단위계 (kJ, kPa, kg, °C) &nbsp;·&nbsp; 포화 테이블: 0.01 ~ 373.95 °C
</div>
""", unsafe_allow_html=True)


# ── 사이드바: 사용법 안내 ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📖 사용 방법")
    st.markdown("""
    1. **독립변수 선택**: 온도 T(°C) 또는 압력 P(kPa)
    2. **두 번째 상태량** 선택 및 값 입력  
       (v, u, h, s 중 하나)
    3. **계산하기** 버튼 클릭

    ---
    **상태 판정 기준**

    | 비교 결과 | 상태 |
    |-----------|------|
    | 입력 < f값 | 압축액 |
    | f값 ≤ 입력 ≤ g값 | 포화 혼합물 |
    | 입력 > g값 | 과열증기 |

    **건도 계산 공식**
    ```
    x = (입력값 - f값) / (g값 - f값)
    M = Mf + x · (Mg - Mf)
    ```
    ---
    **단위 참고**
    - T: °C, P: kPa (또는 MPa)
    - v: m³/kg
    - u, h: kJ/kg
    - s: kJ/(kg·K)
    """)

    st.markdown("---")
    st.markdown("### 📊 테이블 데이터 범위")

    try:
        st.markdown(f"""
        | 테이블 | 범위 |
        |--------|------|
        | 포화(온도) | {T_MIN} ~ {T_MAX} °C |
        | 포화(압력) | {P_MIN_kPa:.1f} ~ {P_MAX_kPa:.0f} kPa |
        | 과열증기 | 0.01 ~ 60 MPa |
        """)
    except Exception:
        pass
