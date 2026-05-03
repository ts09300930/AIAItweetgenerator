import streamlit as st
from openai import OpenAI
from datetime import datetime

st.set_page_config(page_title="裏垢女子ツール（究極版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（究極版）")
st.caption("ペルソナ中心 | 文字数スライダー | 全機能搭載")

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
    tweet_length = st.slider("1ツイートの目安文字数", 120, 250, 160, step=10)

    st.divider()
    st.markdown("### 🎚️ トーン調整")
    kawaii = st.slider("かわいさ", 0, 100, 65)
    ero = st.slider("エロさ", 0, 100, 35)
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70)

    st.divider()
    st.markdown("### 📚 ペルソナプリセット")
    presets = {
        "清楚系欲求不満大学生": "22歳の私立女子大生。黒髪ロングで清楚系だけど実は超欲求不満。日常のちょっとした誘惑を、恥ずかしがりながら可愛く匂わせる感じ。",
        "ギャル系エロかわいい": "21歳のギャル系女子。明るくてエロかわいい感じ。積極的だけど可愛く甘えた話し方。",
        "内気系むらむら女子": "23歳の内気な女子。普段は大人しいけど夜になるとむらむらして一人で妄想しがち。",
        "低身長童顔貧乳": "20歳の低身長140cm童顔Aカップ貧乳女子。自分の体型にコンプレックスを抱きつつも、誰かに甘えたい欲求が強い。",
    }
    selected_preset = st.selectbox("プリセットを選択", ["-- 選択 --"] + list(presets.keys()))
    if selected_preset != "-- 選択 --" and st.button("📥 プリセットを読み込む"):
        st.session_state.persona = presets[selected_preset]
        st.rerun()

# =====================
# ステップ1
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
- 吐息（はぁ...、ん...、だめだよぉ...など）は1ツイートに最大2回まで
- 女性らしい柔らかさ、かわいい感じ、ちょっと恥ずかしがる感じを自然に出す

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

if "meta_prompt" in st.session_state:
    with st.expander("AI①が設計したプロンプト"):
        st.code(st.session_state.meta_prompt)

# =====================
# ステップ2
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button("✨ 3パターン生成", type="primary"):
    with st.spinner("生成中..."):
        gen = f"""以下のペルソナに完全に沿った、自然な裏垢女子のXツイートを3パターン作成してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【絶対厳守】
- 1ツイートあたり約{tweet_length}文字程度
- 短い自然な口語体
- 自然な改行を入れて読みやすく
- 吐息は1ツイートに最大2回まで
- かわいさ・エロさ・恥ずかしさのバランスを調整（かわいさ{kawaii}、エロさ{ero}、恥ずかしさ{hazukashi}）

出力形式:
ツイート1:
（本文）

ツイート2:
（本文）

ツイート3:
（本文）"""

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": gen}],
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

# =====================
# ステップ3: 指摘 → 改善
# =====================
st.divider()
st.header("ステップ3: 指摘する → AI③がAI②に改善指示を出す")

if "last_tweets" not in st.session_state:
    st.info("先にステップ2でツイートを生成してください")
else:
    selected = st.selectbox("改善したいツイート", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    feedback = st.text_area("指摘を書いてください", height=80)

    if st.button("🔄 AI③に指摘を伝えて改善版を生成", type="primary"):
        if not feedback.strip():
            st.error("指摘を入力してください")
        else:
            with st.spinner("改善中..."):
                # 省略せず完全な改善フロー
                critic_prompt = f"""あなたは優秀なツイート改善アドバイザーです。
元のツイート:
{st.session_state.last_tweets[int(selected[-1])-1]}
ユーザーの指摘:
{feedback}
この指摘を基に、AI②に対して与えるべき改善指示を作成してください。
出力は「改善指示本文」のみ。"""
                res1 = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": critic_prompt}], temperature=0.6)
                improvement = res1.choices[0].message.content.strip()

                refine_prompt = f"""以下の指示に従って、元のツイートを改善した新しいバージョンを3パターン作成してください。
元のツイート:
{st.session_state.last_tweets[int(selected[-1])-1]}
改善指示:
{improvement}
出力形式:
改善版1:
（本文）
改善版2:
（本文）
改善版3:
（本文）"""
                res2 = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": refine_prompt}],
                    temperature=0.8
                )
                refined = res2.choices[0].message.content.strip()
                st.success("✅ 改善版を作成しました！")
                st.text_area("改善版", value=refined, height=200)

st.divider()
st.caption("究極版 | 文字数スライダー追加 | トーン調整・プリセット・一括改善など全機能搭載")
