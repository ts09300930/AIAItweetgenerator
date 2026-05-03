import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール（究極版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（究極版）")
st.caption("ペルソナ中心 | プロンプト編集可能 | 文字数10〜250文字調整")

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
        if not api_key: st.stop()

    if api_key.startswith("xai-"):
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        MODEL = "grok-4.20"
    else:
        client = OpenAI(api_key=api_key)
        MODEL = "gpt-4o-mini"

    st.divider()
    st.markdown("### 📏 ツイート文字数調整")
    tweet_length = st.slider("1ツイートの目安文字数", 10, 250, 140, step=10)

    st.divider()
    st.markdown("### 🎚️ トーン調整")
    kawaii = st.slider("かわいさ", 0, 100, 65)
    ero = st.slider("エロさ", 0, 100, 35)
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70)

# =====================
# ステップ1: ペルソナ → AI①設計
# =====================
st.header("ステップ1: ペルソナを入力 → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細", value=st.session_state.get("persona", ""), height=160)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①が設計中..."):
            meta = f"""あなたはXで成功している裏垢女子のツイートを徹底分析したプロンプトエンジニアです。

生成するツイートは以下の条件を**絶対厳守**してください。
- 1ツイートあたり約{tweet_length}文字程度
- 短い自然な口語体
- 自然な改行を入れて読みやすく
- 絵文字・マークダウン一切禁止
- 吐息は1ツイートに最大2回まで
- 女性らしい柔らかさ、かわいい感じ、恥ずかしがる感じを自然に出す

【トーン調整】
- かわいさ: {kawaii}/100
- エロさ: {ero}/100
- 恥ずかしさ: {hazukashi}/100

ペルソナ:
{persona}

このペルソナに最適なシステムプロンプトを作成してください。
出力はプロンプト本文のみ。"""

            res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": meta}], temperature=0.65)
            st.session_state.meta_prompt = res.choices[0].message.content.strip()
            st.success("✅ AI①がプロンプトを設計しました！")

# =====================
# AI①プロンプトの編集機能（ここが新しく追加）
# =====================
if "meta_prompt" in st.session_state:
    st.divider()
    st.subheader("AI①が設計したプロンプト（ここを自由に編集できます）")
    edited_prompt = st.text_area(
        "プロンプトを編集",
        value=st.session_state.meta_prompt,
        height=300,
        key="edited_prompt_area"
    )
    st.session_state.edited_meta_prompt = edited_prompt  # 編集内容を保存

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 編集したプロンプトで保存", type="primary"):
            st.session_state.meta_prompt = edited_prompt
            st.success("プロンプトを更新しました！")
    with col2:
        if st.button("🔄 元のプロンプトに戻す"):
            st.session_state.edited_meta_prompt = st.session_state.meta_prompt
            st.rerun()

# =====================
# ステップ2: 生成
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button("✨ AI②で3パターン生成", type="primary"):
    with st.spinner("生成中..."):
        gen = f"""以下のペルソナに完全に沿った、自然な裏垢女子のXツイートを3パターン作成してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【絶対厳守】
- 1ツイートあたり約{tweet_length}文字程度
- 短い自然な口語体
- 自然な改行を入れて読みやすく
- 吐息は1ツイートに最大2回まで
- かわいさ{kawaii}・エロさ{ero}・恥ずかしさ{hazukashi}のバランスを調整

出力形式:
ツイート1:
（本文）

ツイート2:
（本文）

ツイート3:
（本文）"""

        # 編集したプロンプトがあればそれを使う
        use_prompt = st.session_state.get("edited_meta_prompt", st.session_state.meta_prompt)

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": use_prompt}, {"role": "user", "content": gen}],
            temperature=0.78,
            max_tokens=2500
        )
        result = res.choices[0].message.content.strip()

        tweets = []
        current = ""
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("ツイート") and ":" in line:
                if current:
                    tweets.append(current.strip())
                current = ""
            elif line and not line.startswith("（本文）"):
                current += line + "\n"
        if current:
            tweets.append(current.strip())

        st.session_state.last_tweets = tweets[:3]
        st.success("✅ 生成完了！")

if "last_tweets" in st.session_state:
    st.subheader("生成されたツイート")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=110, key=f"t_{i}")

st.divider()
st.caption("プロンプト編集可能 | 文字数10〜250文字調整 | トーン調整搭載")
