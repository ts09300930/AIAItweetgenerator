import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版・最終）")

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
    tweet_length = st.slider("文字数", 20, 120, 40)

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
# 構文パターン（完全定義）
# =====================
patterns = [
"感覚スタート型：身体の感覚から書き出す（例：指先が震えて…）",
"行動スタート型：動作から書き出す（例：膝を閉じたら…）",
"感情スタート型：感情から書き出す（例：恥ずかしくて…）",
"擬音スタート型：吐息や音から（例：あ…だめ…）",
"途中独り言型：途中から始まる（例：なんか変で…）",
"短文余韻型：短文→余韻で終わる",
"否定スタート型：否定から入る（例：だめなのに…）",
"部位スタート型：身体部位から（例：胸の先が…）",
"動作＋理由型：動作＋理由（例：枕に顔埋めたら落ち着かなくて…）",
"超短文型：極端に短い感覚のみ"
]

# =====================
# ステップ1
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成プロンプト設計者。

以下を満たす詳細プロンプトを作成せよ。

【ペルソナ】
{persona}

【ルール】
・{tweet_length}文字前後
・1〜2行
・独り言
・説明禁止

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

【内容】
・1ツイート1状況
・具体描写のみ

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
    st.session_state.edited = st.text_area("プロンプト編集", st.session_state.meta_prompt, height=200)

# =====================
# ステップ2
# =====================
st.header("ステップ2：生成")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成"):

    if "results" in st.session_state:
        del st.session_state.results

    results = []

    for i in range(num_tweets):

        seed = random.randint(0,999999)
        pattern = random.choice(patterns)

        system_prompt = f"""
{st.session_state.get("edited", st.session_state.meta_prompt)}

【今回の構文（強制）】
{pattern}

【絶対ルール】
・他のツイートと構文を被らせない
・語尾も変える

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
エロさ:{tone(ero,"ero")}
恥ずかしさ:{tone(hazu,"hazu")}

乱数:{seed}
"""

        user_prompt = "ツイートを1つ生成せよ"

        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt}
            ],
            temperature=1.2
        )

        results.append(res.choices[0].message.content.strip())

    st.session_state.results = results

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i,t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
