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
            "0%":"性的要素禁止",
            "25%":"雰囲気のみ",
            "50%":"軽い色気",
            "75%":"欲求あり",
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
# UI
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

# =====================
# AI① プロンプト生成（ここだけ強化）
# =====================
if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成プロンプトの専門家。

以下の**厳密フォーマットに従って**プロンプトを作成せよ。
曖昧な表現は禁止。すべて具体的に書くこと。

【出力フォーマット】

あなたは〇〇（ペルソナを具体的に要約）

【基本ルール】
・一人称:
・文字数: 約{tweet_length}文字
・文体: 口語（自然な独り言）
・改行: あり（読みやすさ重視）
・ツイート構造: 1〜2行・1ツイート1状況

【内容ルール】
・必ず「行動 / 感覚 / 気持ち」のいずれかを含める
・1ツイートにつき1つの状況のみ
・具体的な描写を優先（例：手が震える、視線を逸らすなど）
・抽象表現は禁止（例：いい感じ、なんとなく）

【禁止表現】
・説明文（〜について、〜という設定など）
・状況解説
・同じ構文の繰り返し

【トーン詳細】
かわいさ:{tone(kawaii,"kawaii")}
→ 語尾・話し方・態度を具体的に定義する

エロさ:{tone(ero,"ero")}
→ 許可される表現 / 禁止される表現を明確に書く

恥ずかしさ:{tone(hazu,"hazu")}
→ 表情・行動・言葉でどう表現するか具体化

【ペルソナ】
{persona}

出力は完成されたプロンプトのみ
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
# AI② ツイート生成（変更なし）
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
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【エロ制御（厳守）】
0%: 性的表現完全禁止
25%: 雰囲気のみ（身体・行為・欲求NG）
50%: 軽いドキドキのみ
75%: 欲求はOK（行為NG）
100%: 制限なし

違反した場合は書き直してから出力

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
    for i,t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
