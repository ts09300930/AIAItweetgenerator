import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版・改良）")

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
# 構文パターン（固定定義）
# =====================
patterns = [
"感覚スタート型：身体の感覚から始める（例：指先が震えて…）",
"行動スタート型：動作から始める（例：膝を閉じたら…）",
"感情スタート型：感情から始める（例：恥ずかしくて…）",
"擬音スタート型：吐息や反応から始める（例：あ…だめ…）",
"途中独り言型：途中から始める（例：なんか変で…）",
"短文→余韻型：1行目短く→2行目で余韻",
"否定スタート型：否定から入る（例：だめなのに…）",
"部位スタート型：身体部位から（例：胸の先が…）",
"動作＋理由型：動作＋理由（例：枕に顔埋めたら落ち着かなくて…）",
"超短文型：極端に短く感覚のみ"
]

# =====================
# ステップ1：プロンプト生成
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたは裏垢女子ツイート生成プロンプト設計者。

以下を満たす「詳細かつ具体的な生成プロンプト」を作成せよ。

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
・「行動 / 感覚 / 気持ち」のいずれかを必ず含める
・抽象表現禁止（例：ドキドキ、寂しい など）
・具体的な身体の動きや反応のみを書く
（例：指が震える、膝を閉じる、息が乱れる）

【トーン】
かわいさ:{tone(kawaii,"kawaii")}
→ 語尾・間・口調で表現

エロさ:{tone(ero,"ero")}
→ 身体反応としてのみ表現（直接表現禁止）

恥ずかしさ:{tone(hazu,"hazu")}
→ 行動・仕草で表現（顔を隠す、動きがぎこちない等）

【禁止】
・テンプレ構文
・同じ語尾
・同じ書き出し

必ず具体例を含めて詳細に書くこと。
短くまとめないこと。

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
# ステップ2：ツイート生成
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

【最優先ルール】
・他のツイートと構文を被らせない
・書き出しを変える
・語尾を変える

【トーン最終適用】
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
            temperature=1.15
        )

        results.append(res.choices[0].message.content.strip())

    st.session_state.results = results

# =====================
# 表示
# =====================
if "results" in st.session_state:
    for i,t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, key=f"t{i}")
