import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール（改善版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（改善版）")
st.caption("ペルソナ中心 | 自然さ・短さ・可愛さ重視に強化")

# API設定
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

# =====================
# ステップ1
# =====================
st.header("ステップ1: ペルソナを入力 → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細", height=160)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①が設計中..."):
            meta = f"""あなたはXでフォロワー数万人の裏垢女子アカウントを長年運営しているプロンプトエンジニアです。

生成するツイートは以下の条件を**絶対厳守**してください。
- 140〜180文字程度の短め口語体
- 1ツイートは短く自然な改行を入れる
- 絵文字・マークダウン一切禁止
- 「はぁ...」「ん...」「だめだよぉ...」「むぅ」「やだぁ」などの吐息・甘い語尾は1ツイートに最大2回まで
- 女性らしい柔らかさ、ちょっと恥ずかしがる感じ、甘えた感じを自然に出す
- 自虐は可愛く照れながら、ネガティブになりすぎない

ペルソナ:
{persona}

このペルソナに最適な「自然なXツイート生成用システムプロンプト」を作成してください。
出力はプロンプト本文のみ。"""

            res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": meta}], temperature=0.65)
            st.session_state.meta_prompt = res.choices[0].message.content.strip()
            st.success("✅ AI①がプロンプトを設計しました！")

if "meta_prompt" in st.session_state:
    with st.expander("AI①が設計したプロンプト"):
        st.code(st.session_state.meta_prompt)

# =====================
# ステップ2（大幅強化）
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button("✨ AI②で自然なツイート3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen = f"""以下のペルソナに完全に沿った、自然で魅力的な裏垢女子のXツイートを3パターン作成してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【絶対厳守】
- 各ツイートは140〜180文字程度
- 短い自然な口語体で、1文を短めに
- 自然な改行を入れて読みやすく
- 吐息（はぁ...、ん...、だめだよぉ...など）は1ツイートに最大2回まで
- 女性らしい柔らかさ、恥ずかしさ、甘えた感じを自然に出す
- 自虐は可愛く照れながら、ネガティブになりすぎない

出力形式（この形式を厳密に守ること）：
ツイート1:
（ここに完全なツイート本文）

ツイート2:
（ここに完全なツイート本文）

ツイート3:
（ここに完全なツイート本文）"""

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": gen}],
            temperature=0.75,
            max_tokens=2200
        )
        result = res.choices[0].message.content.strip()

        # 頑丈なパース
        tweets = []
        current = ""
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("ツイート") and ":" in line:
                if current:
                    tweets.append(current.strip())
                current = ""
            elif line and not line.startswith("（ここに"):
                current += line + "\n"
        if current:
            tweets.append(current.strip())

        st.session_state.last_tweets = tweets[:3]
        st.success("✅ AI②がツイートを生成しました！")

if "last_tweets" in st.session_state:
    st.subheader("生成されたツイート")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=110, key=f"t_{i}")

st.divider()
st.caption("改善版 | 長さ・自然さ・吐息を厳しくコントロール")
