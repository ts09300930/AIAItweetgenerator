import streamlit as st
from openai import OpenAI
import random
import time

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（最終安定版）")

# =====================
# API設定
# =====================
with st.sidebar:
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("APIキー", type="password")

    if not api_key:
        st.stop()

    if api_key.startswith("xai-"):
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        MODEL = "grok-4.20"
    else:
        client = OpenAI(api_key=api_key)
        MODEL = "gpt-4o-mini"

    num_tweets = st.slider("生成数", 1, 20, 5)
    tweet_length = st.slider("文字数", 20, 120, 40)

    levels = ["0%", "25%", "50%", "75%", "100%"]
    kawaii = st.select_slider("かわいさ", levels, value="50%")
    ero = st.select_slider("エロさ", levels, value="0%")
    hazu = st.select_slider("恥ずかしさ", levels, value="50%")

# =====================
# エロ分岐（最重要）
# =====================
def build_meta_prompt(persona, ero):
    if ero == "0%":
        ero_part = """
【エロ制御】
・身体描写完全禁止
・欲求完全禁止
・ドキドキや距離感も禁止
・完全に日常のみ
"""
    elif ero == "25%":
        ero_part = """
【エロ制御】
・雰囲気のみ
・身体直接描写は禁止
"""
    elif ero == "50%":
        ero_part = """
【エロ制御】
・軽い身体意識OK（赤面・体温）
・欲求は禁止
"""
    elif ero == "75%":
        ero_part = """
【エロ制御】
・欲求・身体感覚OK
・行為描写は禁止
"""
    else:
        ero_part = """
【エロ制御】
・制限なし（最大表現）
"""

    return f"""
あなたはツイート生成AI。

【ペルソナ】
{persona}

{ero_part}

【トーン】
かわいさ:{kawaii}
恥ずかしさ:{hazu}

【絶対ルール】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言
・説明禁止
・1ツイート1状況
・具体的な内容
・毎回違う内容

出力はツイートのみ
"""

# =====================
# ステップ1
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta_prompt = build_meta_prompt(persona, ero)
    st.session_state.meta = meta_prompt

# 編集
if "meta" in st.session_state:
    st.session_state.meta = st.text_area("プロンプト編集", st.session_state.meta, height=250)

# =====================
# ステップ2
# =====================
st.header("ステップ2：生成")

if "meta" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0, 9999999)
    noise = time.time()

    user_prompt = f"""
乱数:{seed}
ノイズ:{noise}

必ず{num_tweets}個生成

形式:
###1
本文
###2
本文
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":st.session_state.meta},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.9
    )

    raw = res.choices[0].message.content

    results = []
    for b in raw.split("###"):
        t = b.strip()
        if t:
            results.append(t)

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
