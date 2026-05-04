import streamlit as st
from openai import OpenAI
import re

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（安定版）")
st.caption("件数保証 + NG制御 + スコア上位表示")

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
# AIチェック
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
# スコア
# =====================
def score_tweet(client, model, text):
    prompt = f"""
以下のツイートを10点満点で評価

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
    out = res.choices[0].message.content

    nums = re.findall(r"\d+", out)
    total = sum(map(int, nums[:3])) if len(nums) >= 3 else 0

    return total, out

# =====================
# 生成1回
# =====================
def generate_once(client, model, system_prompt, user_prompt):
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=0.9
    )
    return res.choices[0].message.content

# =====================
# プール生成（件数保証）
# =====================
def generate_pool(client, model, system_prompt, user_prompt, ero, target_n):
    results = []
    max_loop = 6

    for _ in range(max_loop):
        raw = generate_once(client, model, system_prompt, user_prompt)
        blocks = raw.split("###")

        for b in blocks:
            if "ツイート:" in b:
                try:
                    t = b.split("ツイート:")[1].split("画像:")[0].strip()
                    i = b.split("画像:")[1].strip()

                    # エロ0%制御
                    if ero == 0:
                        if contains_ng(t) or ai_check(client, model, t):
                            continue
                        i = i.replace("erotic","soft").replace("lewd","natural").replace("sensual","gentle")

                    results.append((t, i))

                    if len(results) >= target_n:
                        return results

                except:
                    continue

    return results

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
    top_k = st.slider("表示上位数", 1, 10, 5)
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

ツイート生成用プロンプトのみ出力
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

    # 多めに生成
    pool = generate_pool(client, MODEL, system_prompt, user_prompt, ero, num_tweets * 2)

    # スコア付与
    scored = []
    for t, i in pool:
        s, detail = score_tweet(client, MODEL, t)
        scored.append((s, t, i, detail))

    # ソート
    scored.sort(reverse=True, key=lambda x: x[0])

    # 上位だけ
    final = scored[:top_k]

    # 🔥 必ず4要素構造で保存（ここ重要）
    st.session_state.results = final

# =====================
# 表示
# =====================
if "results" in st.session_state and len(st.session_state.results) > 0:

    for idx, (score_val, t, img, detail) in enumerate(st.session_state.results):
        st.markdown(f"## #{idx+1}（スコア:{score_val}）")

        st.text_area("ツイート", t, key=f"t{idx}")
        st.text_area("画像", img, key=f"i{idx}")
        st.text_area("評価", detail, key=f"s{idx}")
