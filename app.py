import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（完成版）")

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
    kawaii = st.select_slider("かわいさ", options=levels, value="50%")
    ero = st.select_slider("エロさ", options=levels, value="0%")
    hazu = st.select_slider("恥ずかしさ", options=levels, value="50%")

# =====================
# トーン変換
# =====================
def tone(level, kind):
    return {
        "kawaii":{
            "0%":"無機質",
            "25%":"少し柔らかい",
            "50%":"自然",
            "75%":"甘えた",
            "100%":"強い甘え"
        },
        "hazu":{
            "0%":"堂々",
            "25%":"少し照れ",
            "50%":"恥ずかしい",
            "75%":"かなり照れ",
            "100%":"強い羞恥"
        }
    }[kind][level]

# =====================
# エロ制御（ここが本質修正）
# =====================
def ero_block(level):
    return f"""
【エロ制御（最重要）】

■0%
・性的連想・身体強調すべて禁止

■25%
・距離感・ドキドキのみ
・身体描写は禁止

■50%
・軽い身体意識までOK（距離が近い等）
・欲求は禁止
・胸など具体部位NG

■75%
・欲求・身体意識OK
・ただし行為NG

■100%
・制限なし

【現在の設定】
エロ制御: {level}
"""

# =====================
# UI
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

# =====================
# AI① プロンプト生成
# =====================
if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成AIのプロンプト設計者。

以下条件を満たす生成用プロンプトを作成せよ。

【ペルソナ】
{persona}

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
恥ずかしさ:{tone(hazu,"hazu")}

【絶対条件】
・一人称「私」
・{tweet_length}文字前後（±5）
・1〜2行
・独り言で終わる
・説明禁止

【構成】
・1ツイート1状況
・行動 / 感覚 / 気持ち のいずれか必須
・具体描写のみ（抽象禁止）

{ero_block(ero)}

【禁止】
・同じ表現
・長文

出力は生成用プロンプトのみ
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":meta}],
        temperature=0.7
    )

    st.session_state.meta_prompt = res.choices[0].message.content

# 編集
if "meta_prompt" in st.session_state:
    edited = st.text_area("プロンプト編集", st.session_state.meta_prompt, height=250)
    st.session_state.edited = edited

# =====================
# AI② ツイート生成
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0,999999)

    system_prompt = f"""
{st.session_state.get("edited", st.session_state.meta_prompt)}

【最優先トーン】
かわいさ:{tone(kawaii,"kawaii")}
恥ずかしさ:{tone(hazu,"hazu")}

{ero_block(ero)}

違反した場合は必ず修正

ランダム:{seed}
"""

    user_prompt = f"""
{num_tweets}個生成

形式:
###1
ツイート:
本文
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=1.1
    )

    raw = res.choices[0].message.content

    results = []
    for b in raw.split("###"):
        if "ツイート:" in b:
            try:
                t = b.split("ツイート:")[1].strip()
                results.append(t)
            except:
                pass

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
