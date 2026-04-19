import streamlit as st
from openai import OpenAI
import gspread
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="裏垢女子ツール（最終版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（最終版）")
st.caption("私 → AI①（プロンプト設計） → AI②（生成） の完全チェーン + スプシ保存")

# =====================
# Google Sheets接続
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
# 過去データ
# =====================
try:
    sheet = get_sheet()
    df = pd.DataFrame(sheet.get_all_records())
except:
    df = pd.DataFrame()

# =====================
# ステップ1: ペルソナ + AI①がプロンプト設計
# =====================
st.header("ステップ1: ペルソナ → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細", height=140)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①がXの成功パターンを分析しながらプロンプトを設計中..."):
            meta_instruction = f"""あなたはXで成功している裏垢女子のツイートを徹底分析したプロンプトエンジニアです。

【最重要】
生成するツイートは「普通の裏垢女子がサラッと書いた自然な感じ」にしてください。
- 口語体・短め・カジュアル
- 難しい言葉は避ける
- 絵文字を適度に使う

ペルソナ:
{persona}

このペルソナに最適な「自然なXツイート生成用システムプロンプト」を作ってください。
出力はプロンプト本文のみ。"""

            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": meta_instruction}],
                    temperature=0.65
                )
                st.session_state.meta_prompt = response.choices[0].message.content.strip()
                st.success("✅ AI①がプロンプトを設計しました！")
            except Exception as e:
                st.error(f"エラー: {e}")

if "meta_prompt" in st.session_state:
    with st.expander("AI①が設計したプロンプトを確認"):
        st.code(st.session_state.meta_prompt)

# =====================
# ステップ2: トピック → AI②が生成
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → AI②がツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")

if st.button("✨ AI②で自然なツイート3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen_prompt = f"""以下のトピックで、普通の裏垢女子が書きそうな自然なXツイートを3パターン作ってください。

トピック: {topic}

【重要】小説っぽくせず、普通のツイートらしい口語で短めにしてください。

出力形式:
ツイート1:
（本文）

ツイート2:
（本文）

ツイート3:
（本文）"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": st.session_state.meta_prompt},
                    {"role": "user", "content": gen_prompt}
                ],
                temperature=0.85
            )
            result = response.choices[0].message.content.strip()
            tweets = [line.strip() for line in result.split("\n") if line.strip() and not line.startswith("ツイート")]
            st.session_state.last_tweets = tweets[:3]
            st.session_state.last_topic = topic
            st.success("✅ AI②がツイートを生成しました！")
        except Exception as e:
            st.error(f"エラー: {e}")

# ツイート表示
if "last_tweets" in st.session_state:
    st.subheader("AI②が生成したツイート")
    for i, tweet in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=tweet, height=100, key=f"t_{i}")

# =====================
# 保存
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

st.caption("最終版 | 私 → AI① → AI② の完全チェーン | スプシ保存対応")
