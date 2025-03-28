
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="눈 건강 대시보드", layout="wide")
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            background-color: #f9fbfd;
            color: #1a1a1a;
        }
        h1, h2, h3 {
            color: #0056ff;
            font-weight: 700;
        }
        .stMetric {
            background-color: #ffffff;
            border: 1px solid #dce3ec;
            border-radius: 12px;
            padding: 16px;
            color: #0056ff !important;
            text-align: center;
        }
        .css-1v3fvcr, .css-1d391kg p {
            color: #0056ff !important;
        }
        .stDataFrame {
            background-color: white;
            border-radius: 12px;
            border: 1px solid #dce3ec;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    conn = sqlite3.connect("eye_data.db")
    df = pd.read_sql_query("SELECT * FROM eye_health ORDER BY timestamp ASC", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

RESAMPLE_RULES = {
    "1분": "1min", "5분": "5min", "30분": "30min",
    "1시간": "1H", "12시간": "12H", "1일": "1D"
}

def plot_bar(data, y_col, title, color):
    fig = px.bar(data, x="timestamp", y=y_col, title=title, color_discrete_sequence=[color])
    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#0056ff",
        xaxis_tickangle=-45,
        height=400,
        margin=dict(t=40, b=80, l=40, r=40),
        bargap=0.3
    )
    return fig

st.title("🟦 실시간 눈 건강 대시보드")
st.markdown("눈 깜빡임, 피로도, 색상 및 밝기 비율을 직관적으로 확인할 수 있습니다.")

st.sidebar.header("⏱ 데이터 간격 설정")
interval_label = st.sidebar.radio("시간 간격", list(RESAMPLE_RULES.keys()))
interval = RESAMPLE_RULES[interval_label]

df = load_data()
if df.empty:
    st.error("❗ 데이터가 없습니다. eye_data.db 파일을 확인하세요.")
    st.stop()

df_resampled = df.set_index("timestamp").resample(interval).mean().dropna().reset_index()
df_resampled["timestamp"] = df_resampled["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

# 기준 정의
NORMAL_BLINK_MIN = 10
NORMAL_BLINK_MAX = 30
FATIGUE_THRESHOLD = 0.6

# 진단 함수
def blink_diagnosis(rate):
    if rate < NORMAL_BLINK_MIN:
        return "👁️ 깜빡임 부족 (건조 주의)"
    elif rate > NORMAL_BLINK_MAX:
        return "⚠️ 과다 깜빡임 (피로 or 이상 감지)"
    else:
        return "✅ 적정 깜빡임"

def fatigue_diagnosis(score):
    return "🔥 피로 누적" if score >= FATIGUE_THRESHOLD else "🧊 안정 상태"

# 진단 결과 추가
df_resampled["깜빡임 진단"] = df_resampled["blink_rate"].apply(blink_diagnosis)
df_resampled["피로도 진단"] = df_resampled["fatigue"].apply(fatigue_diagnosis)

# 평균 요약
st.subheader("📌 평균 요약")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("👁️ 평균 깜빡임 수", f"{df_resampled['blink_rate'].mean():.2f}")
with col2:
    st.metric("😵 평균 피로도", f"{df_resampled['fatigue'].mean():.2f}")
with col3:
    st.metric("💡 평균 밝기 비율", f"{df_resampled['brightness_ratio'].mean():.2f}")

# 진단 표
st.subheader("🧠 눈 건강 진단 결과")
st.dataframe(df_resampled[["timestamp", "blink_rate", "fatigue", "깜빡임 진단", "피로도 진단"]], use_container_width=True)

# 주요 지표 그래프
st.subheader("📊 지표별 변화")
col4, col5 = st.columns(2)
with col4:
    st.plotly_chart(plot_bar(df_resampled, "blink_rate", "깜빡임 수", "#007bff"), use_container_width=True)
    st.plotly_chart(plot_bar(df_resampled, "brightness_ratio", "밝기 비율", "#4dabf7"), use_container_width=True)
with col5:
    st.plotly_chart(plot_bar(df_resampled, "fatigue", "피로도", "#1e90ff"), use_container_width=True)

# 색상 비율
st.subheader("🎨 화면 색상 비율")
col6, col7, col8 = st.columns(3)
with col6:
    st.metric("🔴 Red 평균", f"{df_resampled['red_ratio'].mean():.2f}")
    st.plotly_chart(plot_bar(df_resampled, "red_ratio", "Red 비율", "#ff6b6b"), use_container_width=True)
with col7:
    st.metric("🟡 Yellow 평균", f"{df_resampled['yellow_ratio'].mean():.2f}")
    st.plotly_chart(plot_bar(df_resampled, "yellow_ratio", "Yellow 비율", "#ffd43b"), use_container_width=True)
with col8:
    st.metric("🔵 Blue 평균", f"{df_resampled['blue_ratio'].mean():.2f}")
    st.plotly_chart(plot_bar(df_resampled, "blue_ratio", "Blue 비율", "#228be6"), use_container_width=True)

with st.expander("📋 전체 데이터 보기"):
    st.dataframe(df_resampled)
