import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（完全版）")
st.caption("AI①プロンプト生成 + AI②ツイート生成")

# =====================
# API
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

    level = ["0%", "25%", "50%", "75%", "100%"]
    kawaii = st.select_slider("かわいさ", options=level, value="50%")
    ero = st.select_slider("エロさ", options=level, value="0%")
    hazu = st.select_slider("恥ずかしさ", options=level, value="50%")

# =====================
# トーン変換
# =====================
def tone(level, kind):
    return {
        "kawaii":{
            "0%":"無機質","25%":"少し柔らかい","50%":"自然",
            "75%":"甘えた","100%":"強く甘える"
        },
        "ero":{
            "0%":"性的要素禁止",
            "25%":"雰囲気のみ",
            "50%":"軽い色気",
            "75%":"欲求あり",
            "100%":"露骨"
        },
        "hazu":{
            "0%":"堂々","25%":"少し照れ","50%":"恥ずかしい",
            "75%":"かなり照れ","100%":"強い羞恥"
        }
    }[kind][level]

# =====================
# ステップ1（AI①）
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成AIのプロンプト設計者。

以下を満たすプロンプトを作成せよ：

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【ルール】
・{tweet_length}文字前後
・口語
・改行あり
・毎回違う内容

【ペルソナ】
{persona}

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
# ステップ2（AI②）
# =====================
st.header("ステップ2：ツイート生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    seed = random.randint(0,999999)

    system_prompt = f"""
{st.session_state.get("edited", st.session_state.meta_prompt)}

【最優先（上書き）】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

ランダム:{seed}
"""

    user_prompt = f"""
{num_tweets}個生成

形式:
###1
ツイート:
本文

画像:
英語
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
                t = b.split("ツイート:")[1].split("画像:")[0].strip()
                i = b.split("画像:")[1].strip()
                results.append((t,i))
            except:
                pass

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i,(t,img) in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
        st.text_area(f"画像{i+1}", img, key=f"i{i}")
