import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（自然・高速版）")

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

    num_tweets = st.slider("生成数", 1, 30, 5)
    tweet_length = st.slider("文字数", 20, 120, 50)

    levels = ["0%", "25%", "50%", "75%", "100%"]
    kawaii = st.select_slider("かわいさ", options=levels, value="50%")
    ero = st.select_slider("エロさ", options=levels, value="0%")
    hazu = st.select_slider("恥ずかしさ", options=levels, value="50%")

# =====================
# ステップ1：プロンプト生成
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたはツイート生成AIのプロンプト設計者。

以下条件を満たすプロンプトを作れ。

【ペルソナ】
{persona}

【基本】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言のみ（説明禁止）

【内容】
・1つの瞬間だけを書く
・行動 / 感覚 / 気持ち のどれか1つを軽く含める
・自然さ最優先

【禁止】
・説明文
・同じ語尾の繰り返し
・テンプレ化

【トーン】
かわいさ:{kawaii}
エロさ:{ero}
恥ずかしさ:{hazu}

出力はプロンプトのみ
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":meta}],
        temperature=0.7
    )

    st.session_state.meta_prompt = res.choices[0].message.content

# 編集
if "meta_prompt" in st.session_state:
    st.session_state.edited = st.text_area(
        "プロンプト編集",
        st.session_state.meta_prompt,
        height=220
    )

# =====================
# ステップ2：生成（高速・自然）
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    results = []
    base_prompt = st.session_state.get("edited", st.session_state.meta_prompt)

    for i in range(num_tweets):

        seed = random.randint(0,999999)

        system_prompt = f"""
{base_prompt}

【最終条件】
・{tweet_length}文字前後
・独り言
・自然な一言
・同じ表現を避ける

乱数:{seed}
"""

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":system_prompt}],
            temperature=1.2
        )

        text = res.choices[0].message.content.strip()
        results.append(text)

    st.session_state.results = results

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
