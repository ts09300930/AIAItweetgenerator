import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（自然化安定版）")

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
# トーン変換
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
            "0%":"なし",
            "25%":"ほんのり空気",
            "50%":"少しだけ意識",
            "75%":"にじむ欲求",
            "100%":"強め"
        },
        "hazu":{
            "0%":"堂々",
            "25%":"少し照れ",
            "50%":"自然な照れ",
            "75%":"強めに照れ",
            "100%":"かなり恥ずかしい"
        }
    }[kind][level]

# =====================
# ステップ1：プロンプト生成
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたはツイート生成AIのプロンプト設計者。

以下条件で「自然な独り言ツイート」を生成するためのプロンプトを作れ。

【ペルソナ】
{persona}

【基本】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言のみ（説明禁止）

【内容】
・1つの瞬間だけを書く
・考え込まず“ふと漏れた一言”にする
・無理に具体的にしすぎない（自然さ優先）

【表現バランス】
・行動 / 感覚 / 気持ち のどれか1つが軽く入る程度
・全部詰め込まない

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【禁止】
・説明文になること
・同じ語尾の繰り返し
・テンプレ化

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
# ステップ2：生成（修正版）
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0,999999)

    # 🔥 軽量化＋最低限の多様性だけ維持
    system_prompt = f"""
{st.session_state.get("edited", st.session_state.meta_prompt)}

自然な独り言のみ
説明は禁止

書き出しと語尾はできるだけ変える

かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

乱数:{seed}
"""

    # 🔥 複数生成を確実にさせるフォーマット
    user_prompt = f"""
{num_tweets}個のツイートを生成せよ

必ず以下形式で出力：

###1
本文

###2
本文

###3
本文
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=1.15,
        max_tokens=500
    )

    raw = res.choices[0].message.content

    # 🔥 正しく本文だけ抽出
    results = []
    for b in raw.split("###"):
        if b.strip():
            lines = b.strip().split("\n", 1)
            if len(lines) > 1:
                results.append(lines[1].strip())

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i,t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
