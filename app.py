import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版）")

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
# トーン
# =====================
def tone_block():
    return f"""
かわいさ:{kawaii}
恥ずかしさ:{hazu}
"""

# =====================
# エロ制御（完全分岐）
# =====================
def ero_rules():
    if ero == "0%":
        return """
【エロ制御】
・日常内容のみ
・身体描写禁止
・欲求禁止
・距離感表現禁止
・ドキドキ禁止
"""
    else:
        return f"""
【エロ制御】
25%: 雰囲気のみ
50%: 軽い身体意識
75%: 欲求あり（行為NG）
100%: 制限なし

現在:{ero}
"""

# =====================
# ステップ1
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたはツイート生成AIのプロンプト設計者。

【ペルソナ】
{persona}

【ルール】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言
・説明禁止

【構造】
・1ツイート1状況
・行動 または 日常の気持ち
・具体的でシンプルな内容

出力はプロンプトのみ
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":meta}],
        temperature=0.7
    )

    st.session_state.meta = res.choices[0].message.content

# 編集
if "meta" in st.session_state:
    st.session_state.meta = st.text_area("プロンプト編集", st.session_state.meta, height=200)

# =====================
# ステップ2
# =====================
st.header("ステップ2：生成")

if "meta" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0,999999)

    system_prompt = f"""
{st.session_state.meta}

{tone_block()}

{ero_rules()}

【禁止】
・同じ表現
・似た構造
"""

    user_prompt = f"""
乱数:{seed}

{num_tweets}個生成

形式:
###1
本文
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=1.2
    )

    raw = res.choices[0].message.content

    results = []
    for b in raw.split("###"):
        if b.strip():
            results.append(b.strip())

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
