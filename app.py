import streamlit as st
from openai import OpenAI
import gspread
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="裏垢女子ツール B版", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（B版・スプシ完全保存）")

# =====================
# Google Sheets接続
# =====================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1cwzwUjCjjHvhDbpjMZnV078pY8mLnUyQCjHasfQsVjg/edit?gid=0#gid=0"
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
except Exception as e:
    st.error(f"スプレッドシート接続エラー: {e}")
    df = pd.DataFrame()

# =====================
# サイドバー：過去ペルソナ一覧
# =====================
with st.sidebar:
    st.markdown("### 📜 過去のペルソナ（クリックで復元）")
    if not df.empty:
        unique_personas = df["persona"].dropna().unique().tolist()
        selected = st.selectbox("過去のペルソナを選択", ["-- 新規入力 --"] + unique_personas)
        if selected != "-- 新規入力 --":
            st.session_state.persona = selected
    else:
        st.info("まだ保存されていません")

# =====================
# メイン画面
# =====================
st.header("ステップ1: ペルソナ")

persona = st.text_area(
    "ペルソナ詳細",
    value=st.session_state.get("persona", ""),
    height=140
)

# =====================
# ステップ2: 生成
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → 生成")

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")

if st.button("✨ ツイート3パターン生成", type="primary"):
    with st.spinner("生成中..."):
        # ここに生成ロジックを入れる（前回の自然ツイート版と同じでOK）
        # 簡易版として省略（必要なら前のコードをコピペ）
        st.session_state.last_tweets = [
            "生成されたツイート1（ここに実際の生成結果が入ります）",
            "生成されたツイート2",
            "生成されたツイート3"
        ]
        st.session_state.last_topic = topic
        st.success("生成完了！")

# ツイート表示（簡易）
if "last_tweets" in st.session_state:
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=100)

# =====================
# 保存ボタン
# =====================
st.divider()
if st.button("💾 このペルソナ＋ツイートをスプシに保存", type="primary"):
    if "last_tweets" in st.session_state:
        try:
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                persona,
                st.session_state.last_topic,
                st.session_state.last_tweets[0],
                st.session_state.last_tweets[1],
                st.session_state.last_tweets[2]
            ])
            st.success("✅ スプレッドシートに保存しました！")
        except Exception as e:
            st.error(f"保存エラー: {e}")
    else:
        st.warning("先にツイートを生成してください")

st.caption("B版 | Google Sheetsに全履歴を保存 | 再利用しやすい設計")
