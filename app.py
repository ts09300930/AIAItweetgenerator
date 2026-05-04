import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（完成版）")
st.caption("AI①で深いプロンプト生成 → AI②でツイート生成")

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
            "0%":"無機質で感情なし",
            "25%":"少し柔らかい",
            "50%":"自然で可愛い",
            "75%":"甘えた口調・語尾柔らかい",
            "100%":"強く甘え・依存的"
        },
        "ero":{
            "0%":"性的要素完全禁止",
            "25%":"雰囲気のみ（ドキドキ・距離感）",
            "50%":"軽い色気（触れたい・近い）",
            "75%":"欲求・身体意識あり（行為NG）",
            "100%":"直接的で露骨な性的表現"
        },
        "hazu":{
            "0%":"堂々としている",
            "25%":"少し照れる",
            "50%":"恥ずかしがる",
            "75%":"かなり赤面・隠したがる",
            "100%":"強い羞恥・自己否定"
        }
    }[kind][level]

# =====================
# UI
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

# =====================
# AI①（深いプロンプト生成）
# =====================
if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成AIのプロンプト設計者。

以下の条件を満たす「生成用プロンプト」を作成せよ。

【ペルソナ】
{persona}

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【出力スタイル（厳密）】
・一人称は「私」
・1〜2行で完結
・独り言のように終わる
・説明は禁止（感情・感覚のみ）

【内容ルール】
・1ツイートにつき1つの状況
・「行動」「感覚」「気持ち」のいずれかを必ず含める
・具体的な身体感覚・動作を優先
・抽象表現は禁止

【エロ制御】
0% → 性的表現完全禁止
25% → 雰囲気のみ
50% → 軽い身体意識
75% → 欲求あり（行為NG）
100% → 制限なし

【文字数】
{tweet_length}文字前後（±5）

【禁止】
・同じ表現の繰り返し
・説明文（〜について等）
・長文

【出力】
ツイート生成用プロンプトのみ
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
# AI②（ツイート生成）
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    # 前回削除
    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0,999999)

    system_prompt = f"""
{st.session_state.get("edited", st.session_state.meta_prompt)}

【最優先トーン（上書き）】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【エロ制御（最終チェック）】
ルール違反は必ず書き直す

【ランダム性】
{seed}
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
