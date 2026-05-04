import streamlit as st
from openai import OpenAI
import json

st.set_page_config(page_title="裏垢女子ツール（最終版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール")
st.caption("生成数・トーン調整が確実に反映 | 再生成で内容が変わる")

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
    st.markdown("### 📏 生成数調整")
    num_tweets = st.slider("生成するツイート数", 1, 30, 5, step=1)

    st.divider()
    st.markdown("### 📏 1ツイートの目安文字数")
    tweet_length = st.slider("文字数", 10, 250, 140, step=10)

    st.divider()
    st.markdown("### 🎚️ トーン調整")
    kawaii = st.slider("かわいさ", 0, 100, 65)
    ero = st.slider("エロさ", 0, 100, 0)
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70)

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
- 吐息は1ツイートに最大2回まで

【トーン調整を厳密に反映】
- かわいさ: {kawaii}%強く出す
- エロさ: {ero}%強く出す（エロさが0%の場合は一切の性的表現を完全排除）
- 恥ずかしさ: {hazukashi}%強く出す

ペルソナ:
{persona}

このペルソナに最適なシステムプロンプトを作成してください。
出力はプロンプト本文のみ。"""

            res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": meta}], temperature=0.65)
            st.session_state.meta_prompt = res.choices[0].message.content.strip()
            st.success("✅ AI①がプロンプトを設計しました！")

if "meta_prompt" in st.session_state:
    st.divider()
    st.subheader("AI①が設計したプロンプト（編集可能）")
    edited_prompt = st.text_area("プロンプト編集", value=st.session_state.meta_prompt, height=300)
    st.session_state.edited_meta_prompt = edited_prompt

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 編集したプロンプトで保存", type="primary"):
            st.session_state.meta_prompt = edited_prompt
            st.success("更新しました！")
    with col2:
        if st.button("🔄 元のプロンプトに戻す"):
            st.rerun()

# =====================
# ステップ2
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button(f"✨ AI②で{num_tweets}パターン生成", type="primary"):
    # 毎回完全にクリア
    st.session_state.pop("last_tweets", None)

    with st.spinner(f"AI②が{num_tweets}パターン生成中..."):
        gen = f"""以下のペルソナに完全に沿った自然な裏垢女子のXツイートを**正確に{num_tweets}個**作成してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【絶対厳守】
- 各ツイートは約{tweet_length}文字程度
- 短い自然な口語体
- 自然な改行を入れて読みやすく
- 吐息は1ツイートに最大2回まで
- 各ツイートは明確に異なる内容にする
- かわいさ{kawaii}%・エロさ{ero}%・恥ずかしさ{hazukashi}%を厳密に反映（エロさ0%の場合は一切の性的表現を完全排除）

**必ず以下のJSON形式で出力**：
{{
  "tweets": [
    "ツイート1の完全な本文",
    "ツイート2の完全な本文",
    ... 合計でちょうど{num_tweets}個
  ]
}}"""

        use_prompt = st.session_state.get("edited_meta_prompt", st.session_state.meta_prompt)

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": use_prompt}, {"role": "user", "content": gen}],
            temperature=0.92,
            max_tokens=8000
        )
        result = res.choices[0].message.content.strip()

        # JSONパースを最優先
        tweets = []
        try:
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result[result.find("{"):result.rfind("}") + 1]
            data = json.loads(json_str)
            tweets = data.get("tweets", [])
        except:
            # フォールバック
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

        st.session_state.last_tweets = tweets[:num_tweets]
        st.success(f"✅ {len(st.session_state.last_tweets)}パターン生成完了！")

if "last_tweets" in st.session_state:
    st.subheader(f"生成されたツイート（{len(st.session_state.last_tweets)}個）")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=110, key=f"t_{i}")

st.divider()
st.caption("生成ボタン押すたびに新しい内容が出る | トーン調整厳密反映")
