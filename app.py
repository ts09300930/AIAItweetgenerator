import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（高速＋安全版）")
st.caption("AI検閲あり / スコア削除で高速化")

# =====================
# NGワード
# =====================
NG_WORDS = [
    "エロ","エッチ","ムラムラ","興奮","欲情",
    "おっぱい","胸","乳","舐め","キス",
    "抱いて","濡れ","喘","感じ","誘"
]

def contains_ng(text):
    return any(w in text for w in NG_WORDS)

# =====================
# AI検閲
# =====================
def ai_check(client, model, text):
    prompt = f"""
以下に性的要素が含まれるか判定せよ

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

    num_tweets = st.slider("生成数", 1, 30, 10)
    tweet_length = st.slider("文字数", 10, 250, 60)

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
トーン:
かわいさ:{kawaii}%
エロさ:{ero}%
恥ずかしさ:{hazukashi}%

ペルソナ:
{persona}

ツイート生成プロンプトのみ出力
"""
    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":meta}],
        temperature=0.7
    )
    st.session_state.meta_prompt = res.choices[0].message.content

if "meta_prompt" in st.session_state:
    edited = st.text_area("プロンプト編集", st.session_state.meta_prompt, height=200)
    st.session_state.edited_meta_prompt = edited

# =====================
# ステップ2
# =====================
st.header("ステップ2")

if "meta_prompt" not in st.session_state:
    st.stop()

def generate_once(system_prompt, user_prompt):
    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.85
    )
    return res.choices[0].message.content

if st.button("✨ 生成"):

    system_prompt = f"""
{st.session_state.get("edited_meta_prompt")}

最優先:
かわいさ:{kawaii}%
エロさ:{ero}%
恥ずかしさ:{hazukashi}%
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

    results = []
    max_loop = 5

    for _ in range(max_loop):
        raw = generate_once(system_prompt, user_prompt)
        blocks = raw.split("###")

        for b in blocks:
            if "ツイート:" in b:
                try:
                    t = b.split("ツイート:")[1].split("画像:")[0].strip()
                    i = b.split("画像:")[1].strip()

                    # 🔥 AI検閲あり
                    if ero == 0:
                        if contains_ng(t) or ai_check(client, MODEL, t):
                            continue

                        i = i.replace("erotic","soft").replace("lewd","natural")

                    results.append((t, i))

                    if len(results) >= num_tweets:
                        break

                except:
                    continue

        if len(results) >= num_tweets:
            break

    st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:

    for i, (t, img) in enumerate(st.session_state.results):
        st.markdown(f"### {i+1}")
        st.text_area("ツイート", t, key=f"t{i}")
        st.text_area("画像プロンプト", img, key=f"i{i}")
