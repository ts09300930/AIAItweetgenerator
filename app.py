import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（完全制御版）")
st.caption("トーン段階制御 + 高速 + 安定")

# =====================
# セッション安全化
# =====================
if "results" in st.session_state:
    try:
        if len(st.session_state.results) > 0 and len(st.session_state.results[0]) != 2:
            del st.session_state.results
    except:
        del st.session_state.results

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

    client = OpenAI(api_key=api_key)
    MODEL = "gpt-4o-mini"

    num_tweets = st.slider("生成数", 1, 20, 5)
    tweet_length = st.slider("文字数", 20, 120, 40)

    # 🔥 段階制スライダー
    level_labels = ["0%", "25%", "50%", "75%", "100%"]

    kawaii_level = st.select_slider("かわいさ", options=level_labels, value="50%")
    ero_level = st.select_slider("エロさ", options=level_labels, value="0%")
    hazukashi_level = st.select_slider("恥ずかしさ", options=level_labels, value="50%")

# =====================
# レベル → 意味変換
# =====================
def tone_map(level, kind):
    mapping = {
        "kawaii": {
            "0%": "無機質で感情なし",
            "25%": "少し柔らかい",
            "50%": "自然で可愛い",
            "75%": "甘えた口調・語尾柔らかい",
            "100%": "強く甘え・依存・可愛さ全開"
        },
        "ero": {
            "0%": "性的要素完全禁止",
            "25%": "雰囲気のみ（身体・欲求NG）",
            "50%": "軽い色気（距離感・ドキドキ）",
            "75%": "欲求や身体意識を含める",
            "100%": "直接的で露骨な性的表現"
        },
        "hazukashi": {
            "0%": "堂々としている",
            "25%": "少し照れる",
            "50%": "恥ずかしがる",
            "75%": "かなり赤面・隠したがる",
            "100%": "強い羞恥・自己否定・逃げたい"
        }
    }
    return mapping[kind][level]

# =====================
# NGワード（軽量）
# =====================
NG_WORDS = ["エロ","エッチ","ムラムラ","興奮","欲情","濡れ","喘","感じ"]

def contains_ng(text):
    return any(w in text for w in NG_WORDS)

# =====================
# ステップ1
# =====================
st.header("ステップ1：ペルソナ")

persona = st.text_area("ペルソナ", height=150)

# =====================
# ステップ2
# =====================
st.header("ステップ2：生成")

if st.button("✨ 生成"):

    seed = random.randint(0, 999999)

    system_prompt = f"""
あなたは裏垢女子ツイート生成AI。

【トーン（絶対遵守）】
かわいさ:{tone_map(kawaii_level, "kawaii")}
エロさ:{tone_map(ero_level, "ero")}
恥ずかしさ:{tone_map(hazukashi_level, "hazukashi")}

【文字数】
{tweet_length}文字前後（±5）

【ルール】
- 毎回違う内容
- 同じ言い回し禁止
- 自然な口語
- 改行あり

【重要】
出力前にトーンがズレていないか自己チェックし修正すること

【ランダム性】
{seed}
"""

    user_prompt = f"""
ペルソナ:
{persona}

{num_tweets}個生成

形式:
###1
ツイート:
本文

画像:
英語プロンプト
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
    blocks = raw.split("###")

    for b in blocks:
        if "ツイート:" in b:
            try:
                t = b.split("ツイート:")[1].split("画像:")[0].strip()
                i = b.split("画像:")[1].strip()

                # エロ0%のみブロック
                if ero_level == "0%":
                    if contains_ng(t):
                        continue
                    i = "cute petite adult woman, soft lighting, natural pose"

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
        st.text_area("画像プロンプト", img, key=f"i{i}")
