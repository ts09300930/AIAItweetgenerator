import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版）")

# =====================
# API設定（xAI対応）
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
            "100%":"強く甘える"
        },
        "ero":{
            "0%":"性的要素完全禁止",
            "25%":"雰囲気のみ",
            "50%":"軽い色気",
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
# ステップ1：プロンプト生成
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成プロンプト設計者。

以下条件を満たす「高精度プロンプト」を作成せよ。

【ペルソナ】
{persona}

【基本ルール】
・一人称「私」
・{tweet_length}文字前後
・1〜2行
・独り言
・説明禁止

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【内容ルール】
・1ツイート1状況
・行動 / 感覚 / 気持ちのいずれか必須
・具体描写優先（抽象禁止）

【構文分散ルール（必須）】
以下のいずれか1つの型で書かせるプロンプトを作れ：

①感覚スタート型
②行動スタート型
③感情スタート型
④擬音スタート型
⑤途中から独り言型
⑥短文→余韻型
⑦否定スタート型
⑧身体部位スタート型
⑨動作＋理由型
⑩超短文余白型

同じ型を連続使用禁止にすること。

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
    edited = st.text_area("プロンプト編集", st.session_state.meta_prompt, height=200)
    st.session_state.edited = edited

# =====================
# ステップ2：ツイート生成
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

【最優先ルール】
・各ツイートで必ず異なる構文パターンを使うこと
・語尾も被らせないこと
・同じ流れを禁止

【最終トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【エロ制御（厳守）】
0%: 完全禁止（身体・欲求・ドキドキ全部NG）
25%: 雰囲気のみ
50%: 軽い意識
75%: 欲求OK（行為NG）
100%: 制限なし

違反した場合は生成し直すこと

乱数:{seed}
"""

    user_prompt = f"""
{num_tweets}個生成

※必ず構文をバラけさせること

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
    for i,t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
