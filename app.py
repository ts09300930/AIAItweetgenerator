import streamlit as st
from openai import OpenAI
import random
import time

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版・最終）")

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
【トーン】
かわいさ:{kawaii}
恥ずかしさ:{hazu}
"""

# =====================
# エロ制御（完全分岐・最重要）
# =====================
def ero_block():
    if ero == "0%":
        return """
【最優先制約（絶対）】
・身体に関する描写を完全禁止
・触れる・敏感・温度・熱・震え等のワード禁止
・欲求・ドキドキ・距離感・匂わせ完全禁止

【許可】
・日常のみ
・軽い感情のみ（恥ずかしい・嬉しいなど）
"""
    elif ero == "25%":
        return """
【制約】
・身体の直接描写は禁止
・雰囲気レベルの可愛さのみ
・距離感や空気感まで
"""
    elif ero == "50%":
        return """
【制約】
・軽い身体意識OK（顔が熱い・赤面など）
・直接的な欲求は禁止
"""
    elif ero == "75%":
        return """
【制約】
・欲求・身体感覚OK
・行為描写は禁止
"""
    else:  # 100%
        return """
【制約】
・制限なし（最大表現）
"""

# =====================
# ステップ1：プロンプト生成
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたはツイート生成AIのプロンプト設計者。

【ペルソナ】
{persona}

【基本ルール】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言
・説明禁止

【構造】
・1ツイート1状況
・行動 or 気持ち
・具体的でシンプル

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
# ステップ2：生成
# =====================
st.header("ステップ2：生成")

if "meta" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    # 前回結果削除（重要）
    if "results" in st.session_state:
        del st.session_state.results

    # 毎回完全ランダム（キャッシュ破壊）
    seed = random.randint(0, 9999999)
    noise = time.time()

    system_prompt = f"""
【最優先ルール】
このルールは絶対に破ってはいけない

{ero_block()}

{tone_block()}

【基本構造】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言
・説明禁止
・1ツイート1状況
・毎回違う内容

【禁止】
・同じ構文
・似た表現
・繰り返し

【ペルソナ】
{persona}
"""

    user_prompt = f"""
乱数:{seed}
ノイズ:{noise}

必ず{num_tweets}個生成せよ

形式:
###1
本文
###2
本文
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.9
    )

    raw = res.choices[0].message.content

    # =====================
    # パース
    # =====================
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
