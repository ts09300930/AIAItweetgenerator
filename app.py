import streamlit as st
from openai import OpenAI
import re

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（完全版）")
st.caption("トーン反映 + NG制御 + スコアリング")

# =====================
# NGワード（最低限）
# =====================
NG_WORDS = [
    "エロ","エッチ","ムラムラ","興奮","欲情",
    "おっぱい","胸","乳","舐め","キス",
    "抱いて","濡れ","喘","感じ","誘"
]

def contains_ng(text):
    return any(w in text for w in NG_WORDS)

# =====================
# AIチェック（軽量）
# =====================
def ai_check(client, model, text):
    prompt = f"""
以下に性的・センシティブ要素があるか判定せよ

{text}

SAFE or NG
"""
    res = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    return "NG" in res.choices[0].message.content

# =====================
# 再生成ループ
# =====================
def generate_safe(client, model, system_prompt, user_prompt, ero, max_retry=3):
    for _ in range(max_retry):

        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt}
            ],
            temperature=0.9
        )

        output = res.choices[0].message.content

        # 🔥 エロ0%時のみ強制フィルタ
        if ero == 0:
            if contains_ng(output) or ai_check(client, model, output):
                continue

        return output

    return output  # 最後の結果を返す（完全失敗回避）

# =====================
# スコアリング
# =====================
def score(client, model, text):
    prompt = f"""
以下のツイートを評価（10点満点）

{text}

共感度:
リアル度:
刺さり度:
"""
    res = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content

# =====================
# API設定
# =====================
with st.sidebar:
    st.header("⚙️ 設定")

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
    tweet_length = st.slider("文字数", 10, 250, 140)

    kawaii = st.slider("かわいさ", 0, 100, 65)
    ero = st.slider("エロさ", 0, 100, 0)
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70)

# =====================
# ステップ1
# =====================
st.header("ステップ1")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
トーンを必ず含める:

かわいさ:{kawaii}%
エロさ:{ero}%
恥ずかしさ:{hazukashi}%

ペルソナ:
{persona}

ツイート生成用プロンプトのみ出力
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":meta}],
        temperature=0.7
    )

    st.session_state.meta_prompt = res.choices[0].message.content

# 編集
if "meta_prompt" in st.session_state:
    edited = st.text_area("プロンプト", st.session_state.meta_prompt, height=200)
    st.session_state.edited_meta_prompt = edited

# =====================
# ステップ2
# =====================
st.header("ステップ2")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    dynamic_prompt = f"""
{st.session_state.get("edited_meta_prompt")}

最優先:
かわいさ:{kawaii}%
エロさ:{ero}%
恥ずかしさ:{hazukashi}%
"""

    gen = f"""
{num_tweets}個生成

形式:

###1
ツイート:
本文

画像:
英語

###2
"""

    raw = generate_safe(client, MODEL, dynamic_prompt, gen, ero)

    # =====================
    # パース
    # =====================
    blocks = raw.split("###")
    results = []

    for b in blocks:
        if "ツイート:" in b:
            try:
                t = b.split("ツイート:")[1].split("画像:")[0].strip()
                i = b.split("画像:")[1].strip()
                results.append((t, i))
            except:
                continue

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:

    for i, (t, img) in enumerate(st.session_state.results):
        st.markdown(f"### {i+1}")

        st.text_area("ツイート", t, key=f"t{i}")
        st.text_area("画像", img, key=f"i{i}")

        sc = score(client, MODEL, t)
        st.text_area("スコア", sc, key=f"s{i}")
