import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版FINAL）")

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
# 型バリエーション（強制）
# =====================
TWEET_STYLES = [
    "感覚スタート",
    "行動スタート",
    "途中独り言",
    "短文余韻",
    "否定スタート",
    "身体部位スタート",
    "動作→反応"
]

# =====================
# ステップ1
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたはツイート生成AIのプロンプト設計者。

以下条件を満たすプロンプトを作れ：

【ペルソナ】
{persona}

【基本】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言のみ

【内容】
・1つの瞬間だけ
・具体的な行動 or 身体感覚を1つだけ入れる
・抽象表現は禁止

【禁止】
・説明文
・同じ構文の繰り返し

出力はプロンプトのみ
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":meta}],
        temperature=0.7
    )

    st.session_state.meta_prompt = res.choices[0].message.content

if "meta_prompt" in st.session_state:
    st.session_state.edited = st.text_area(
        "プロンプト編集",
        st.session_state.meta_prompt,
        height=220
    )

# =====================
# ステップ2（完全改善）
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    results = []

    base_prompt = st.session_state.get("edited", st.session_state.meta_prompt)

    for i in range(num_tweets):

        style = random.choice(TWEET_STYLES)
        seed = random.randint(0,999999)

        system_prompt = f"""
{base_prompt}

【重要】
今回は「{style}」の型で書け

【絶対条件】
・{tweet_length}±5文字
・独り言
・1状況のみ
・具体描写のみ

【禁止】
・同じ語尾
・同じ構文
・テンプレ化

乱数:{seed}
"""

        # 🔥 文字数制御リトライ
        for _ in range(3):

            res = client.chat.completions.create(
                model=MODEL,
                messages=[{"role":"system","content":system_prompt}],
                temperature=1.3
            )

            text = res.choices[0].message.content.strip()
            length = len(text)

            if tweet_length - 5 <= length <= tweet_length + 5:
                break

        results.append(text)

    st.session_state.results = results

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
