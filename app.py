import streamlit as st
from openai import OpenAI
import random
import time

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（修正版安定版）")

# =====================
# API設定
# =====================
with st.sidebar:
    api_key = st.text_input("APIキー", type="password")

    if api_key:
        if api_key.startswith("xai-"):
            client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            MODEL = "grok-4.20"
        else:
            client = OpenAI(api_key=api_key)
            MODEL = "gpt-4o-mini"
    else:
        st.warning("APIキーを入力してください")
        st.stop()

    num_tweets = st.slider("生成数", 1, 20, 5)
    tweet_length = st.slider("文字数", 20, 120, 40)

    levels = ["0%", "25%", "50%", "75%", "100%"]
    kawaii = st.select_slider("かわいさ", levels, value="50%")
    ero = st.select_slider("エロさ", levels, value="0%")
    hazu = st.select_slider("恥ずかしさ", levels, value="50%")

# =====================
# メタプロンプト生成関数
# =====================
def build_meta_prompt(persona):
    if ero == "0%":
        ero_part = "身体描写禁止・欲求禁止・日常のみ"
    elif ero == "25%":
        ero_part = "雰囲気のみ"
    elif ero == "50%":
        ero_part = "軽い身体意識OK（欲求禁止）"
    elif ero == "75%":
        ero_part = "欲求OK・行為禁止"
    else:
        ero_part = "制限なし"

    return f"""
あなたはツイート生成AI。

【ペルソナ】
{persona}

【エロ制御】
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
・毎回違う内容

出力はツイートのみ
"""

# =====================
# ステップ1
# =====================
st.header("ステップ1：プロンプト生成")
persona = st.text_area("ペルソナ", height=150)

meta_prompt = build_meta_prompt(persona)

st.text_area("生成プロンプト（リアルタイム）", meta_prompt, height=250)

# =====================
# ステップ2
# =====================
st.header("ステップ2：生成")

if st.button("✨ 生成"):

    seed = random.randint(0, 9999999)
    noise = time.time()

    user_prompt = f"""
乱数:{seed}
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
            {"role": "system", "content": meta_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.9
    )

    raw = res.choices[0].message.content

    results = [t.strip() for t in raw.split("###") if t.strip()]

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
