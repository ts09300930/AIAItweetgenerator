import streamlit as st
from openai import OpenAI
import gspread
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="裏垢女子ツール（B版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（B版・スプシ保存）")

# =====================
# Google Sheets 接続（ここをあなたの情報に変えてください）
# =====================
SHEET_URL = "https://docs.google.com/spreadsheets/d/ここにあなたのスプレッドシートIDを入れてください"
SHEET_NAME = "History"

@st.cache_resource
def get_sheet():
    gc = gspread.service_account_from_dict(st.secrets["gspread"])
    return gc.open_by_url(SHEET_URL).worksheet(SHEET_NAME)

# APIキー
with st.sidebar:
    st.header("設定")
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("APIキー", type="password")
        if not api_key: st.stop()

if api_key.startswith("xai-"):
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    MODEL = "grok-4.20"
else:
    client = OpenAI(api_key=api_key)
    MODEL = "gpt-4o-mini"

# =====================
# 過去データ読み込み
# =====================
try:
    sheet = get_sheet()
    df = pd.DataFrame(sheet.get_all_records())
except:
    df = pd.DataFrame()

# =====================
# サイドバー：過去ペルソナ
# =====================
with st.sidebar:
    st.markdown("### 📜 過去のペルソナ")
    if not df.empty:
        personas = df["persona"].unique().tolist()
        selected_persona = st.selectbox("選択", ["-- 新規 --"] + personas)
        if selected_persona != "-- 新規 --":
            st.session_state.persona = selected_persona
    else:
        st.info("まだ保存されたペルソナがありません")

# =====================
# メインUI
# =====================
st.header("ステップ1: ペルソナ")

persona = st.text_area("ペルソナ詳細", 
                       value=st.session_state.get("persona", ""), 
                       height=140)

if st.button("💾 このペルソナ＋生成結果をスプシに保存"):
    if "last_tweets" in st.session_state:
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "persona": persona,
            "topic": st.session_state.get("last_topic", ""),
            "tweet1": st.session_state.last_tweets[0] if len(st.session_state.last_tweets) > 0 else "",
            "tweet2": st.session_state.last_tweets[1] if len(st.session_state.last_tweets) > 1 else "",
            "tweet3": st.session_state.last_tweets[2] if len(st.session_state.last_tweets) > 2 else ""
        }
        sheet.append_row(list(row.values()))
        st.success("スプシに保存しました！")
    else:
        st.warning("先にツイートを生成してください")

# 以下は省略（生成部分は前回と同じ）
st.divider()
st.header("ステップ2: トピック入力 → 生成")

# （ここに生成ロジックを入れる。必要なら前回のコードをコピペして使ってください）
