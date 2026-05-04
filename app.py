import streamlit as st
from openai import OpenAI
import random

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツール（安定版）")

# =====================
# API設定（xAI対応）
# =====================
with st.sidebar:
    st.header("⚙️ 設定")

    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ SecretsからAPIキーを読み込みました")
    else:
        api_key = st.text_input("APIキー", type="password")

    if not api_key:
        st.stop()

    # ✅ ここ重要（エラー原因修正）
    if api_key.startswith("xai-"):
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        MODEL = "grok-4.20"
    else:
        client = OpenAI(api_key=api_key)
        MODEL = "gpt-4o-mini"

    st.divider()

    num_tweets = st.slider("生成数", 1, 20, 5)
    tweet_length = st.slider("文字数", 20, 120, 40)

    levels = ["0%", "25%", "50%", "75%", "100%"]
    kawaii = st.select_slider("かわいさ", levels, value="50%")
    ero = st.select_slider("エロさ", levels, value="0%")
    hazu = st.select_slider("恥ずかしさ", levels, value="50%")

# =====================
# トーン（AI②専用）
# =====================
def tone_block():
    return f"""
【トーン（最優先・上書き）】
かわいさ:{kawaii}
恥ずかしさ:{hazu}

【エロ制御】
0%: 性的要素完全禁止
25%: 雰囲気のみ（距離感）
50%: 軽い身体意識（近いなど）
75%: 欲求あり（行為NG）
100%: 制限なし

現在:{ero}
"""

# =====================
# ステップ1（AI①）
# =====================
st.header("ステップ1：プロンプト生成")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成"):

    meta = f"""
あなたはツイート生成AIのプロンプト設計者。

以下条件を満たす「構造プロンプト」を作成せよ。

【ペルソナ】
{persona}

【ルール】
・一人称「私」
・{tweet_length}文字前後（±5）
・1〜2行
・独り言で終わる
・説明禁止

【構造】
・1ツイート1状況
・行動 / 感覚 / 気持ち のいずれか必須
・具体描写のみ（抽象禁止）

出力はプロンプトのみ
"""

    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": meta}],
            temperature=0.7
        )
        st.session_state.meta = res.choices[0].message.content
        st.success("✅ プロンプト生成完了")
    except Exception as e:
        st.error(f"エラー: {e}")
        st.stop()

# 編集
if "meta" in st.session_state:
    st.session_state.meta = st.text_area(
        "プロンプト編集",
        st.session_state.meta,
        height=200
    )

# =====================
# ステップ2（AI②）
# =====================
st.header("ステップ2：生成")

if "meta" not in st.session_state:
    st.info("先にステップ1を実行してください")
    st.stop()

if st.button("✨ 生成"):

    # 前回結果削除（重要）
    if "results" in st.session_state:
        del st.session_state.results

    seed = random.randint(0, 999999)

    system_prompt = f"""
{st.session_state.meta}

{tone_block()}

【禁止】
・同じ表現
・似た構造

【重要】
ルール違反は書き直してから出力
"""

    user_prompt = f"""
乱数:{seed}

{num_tweets}個生成

形式:
###1
本文
"""

    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=1.2
        )

        raw = res.choices[0].message.content

        results = []
        for b in raw.split("###"):
            if b.strip():
                results.append(b.strip())

        st.session_state.results = results[:num_tweets]

        st.success(f"✅ {len(st.session_state.results)}件生成完了")

    except Exception as e:
        st.error(f"生成エラー: {e}")
        st.stop()

# =====================
# 表示
# =====================
if "results" in st.session_state:
    st.subheader("生成結果")

    for i, t in enumerate(st.session_state.results):
        st.text_area(f"ツイート{i+1}", t, height=100, key=f"t{i}")
