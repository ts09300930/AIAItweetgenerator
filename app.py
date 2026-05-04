import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（強化版）")
st.caption("トーン100%反映 + 画像プロンプト生成対応")

# =====================
# API設定
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

    if api_key.startswith("xai-"):
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        MODEL = "grok-4.20"
    else:
        client = OpenAI(api_key=api_key)
        MODEL = "gpt-4o-mini"

    st.divider()

    num_tweets = st.slider("生成するツイート数", 1, 30, 5)
    tweet_length = st.slider("文字数", 10, 250, 140)

    st.divider()

    kawaii = st.slider("かわいさ", 0, 100, 65)
    ero = st.slider("エロさ", 0, 100, 0)
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70)

# =====================
# ステップ1（AI①）
# =====================
st.header("ステップ1: ペルソナ → プロンプト設計")

persona = st.text_area("ペルソナ", height=150)

if st.button("🚀 プロンプト生成", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("設計中..."):

            meta = f"""
あなたは裏垢女子ツイートのプロンプトエンジニアです。

以下のトーンを**必ず数値付きでプロンプトに組み込むこと**：

- かわいさ: {kawaii}%
- エロさ: {ero}%
- 恥ずかしさ: {hazukashi}%

ルール:
- 1ツイート約{tweet_length}文字
- 自然な口語
- 改行あり
- 吐息最大2回

ペルソナ:
{persona}

出力はプロンプトのみ
"""

            res = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": meta}],
                temperature=0.7
            )

            st.session_state.meta_prompt = res.choices[0].message.content.strip()
            st.success("✅ プロンプト生成完了")

# 編集
if "meta_prompt" in st.session_state:
    st.subheader("プロンプト（編集可）")

    edited = st.text_area("", st.session_state.meta_prompt, height=250)
    st.session_state.edited_meta_prompt = edited

# =====================
# ステップ2（AI②）
# =====================
st.header("ステップ2: ツイート生成 + 画像プロンプト")

if "meta_prompt" not in st.session_state:
    st.stop()

if st.button("✨ 生成", type="primary"):

    with st.spinner("生成中..."):

        # 🔥 ここが重要：毎回トーンを上書き
        dynamic_prompt = f"""
{st.session_state.get("edited_meta_prompt", st.session_state.meta_prompt)}

【最優先トーン（上書き強制）】
- かわいさ: {kawaii}%
- エロさ: {ero}%
- 恥ずかしさ: {hazukashi}%
"""

        gen = f"""
以下のペルソナに完全準拠して出力してください。

【絶対条件】
- ツイート数は必ず{num_tweets}個
- 各ツイート約{tweet_length}文字
- 全て異なる内容

【エロ制御】
- 0% → 完全排除
- 80%以上 → 強めに

【出力形式（厳守）】

###1
ツイート:
本文

画像:
英語プロンプト

###2
...
"""

        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": dynamic_prompt},
                {"role": "user", "content": gen}
            ],
            temperature=0.95
        )

        raw = res.choices[0].message.content

        # =====================
        # パース安定化
        # =====================
        blocks = raw.split("###")
        results = []

        for b in blocks:
            if "ツイート:" in b:
                try:
                    tweet = b.split("ツイート:")[1].split("画像:")[0].strip()
                    image = b.split("画像:")[1].strip()
                    results.append((tweet, image))
                except:
                    continue

        st.session_state.results = results[:num_tweets]

# =====================
# 表示
# =====================
if "results" in st.session_state:

    for i, (t, img) in enumerate(st.session_state.results):
        st.markdown(f"### {i+1}")

        st.text_area("ツイート", t, height=100, key=f"t{i}")
        st.text_area("画像プロンプト", img, height=100, key=f"i{i}")
