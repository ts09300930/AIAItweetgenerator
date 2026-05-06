import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（高速・安定版）")

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
# トーン
# =====================
def tone(level, kind):
    return {
        "kawaii":{
            "0%":"無機質",
            "25%":"少し柔らかい",
            "50%":"自然",
            "75%":"甘えた",
            "100%":"強く甘える"
        },
        "ero":{
            "0%":"性的要素完全禁止",
            "25%":"雰囲気のみ",
            "50%":"軽い身体意識",
            "75%":"欲求あり（行為NG）",
            "100%":"露骨"
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
# 構文パターン
# =====================
patterns = [
"感覚スタート型",
"行動スタート型",
"感情スタート型",
"擬音スタート型",
"途中独り言型",
"短文→余韻型",
"否定スタート型",
"部位スタート型",
"動作＋理由型",
"超短文型"
]

# =====================
# ステップ1：プロンプト生成
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成プロンプト設計者。

以下を満たす「詳細で具体的な生成プロンプト」を作成せよ。

【ペルソナ】
{persona}

【基本ルール】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言
・説明・設定・解説は禁止

【内容ルール】
・1ツイート1状況
・「行動 / 身体感覚 / 身体反応」のいずれか必須
・抽象表現禁止（例：ドキドキ、恥ずかしい）
・具体描写のみ（指が震える、膝が閉じる、息が乱れる等）

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【禁止】
・テンプレ構文
・同じ語尾
・同じ書き出し

必ず具体例も含めて詳細に書くこと。
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
    st.session_state.edited = st.text_area("プロンプト編集", st.session_state.meta_prompt, height=220)

# =====================
# ステップ2：生成（高速版）
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0,999999)

    pattern_text = "\n".join([f"{i+1}. {p}" for i,p in enumerate(patterns)])

    system_prompt = f"""
{st.session_state.get("edited", st.session_state.meta_prompt)}

【構文パターン一覧】
{pattern_text}

【重要】
・各ツイートごとに必ず異なる構文を使用
・書き出し・語尾・リズムを全て変える

【トーン最終適用】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

乱数:{seed}
"""

    user_prompt = f"""
{num_tweets}個のツイートを生成せよ

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
        temperature=1.15,
        max_tokens=2000
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
    for i,t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
