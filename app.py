import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール（シンプル版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（シンプル版）")
st.caption("ペルソナ入力 → AI①設計 → AI②生成 → あなた指摘 → AI③指示 → AI②改善")

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

# =====================
# ステップ1: ペルソナ → AI①設計
# =====================
st.header("ステップ1: ペルソナを入力 → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細（できるだけ詳しく書いてください）", height=160)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①が設計中..."):
            meta = f"""あなたはXで成功している裏垢女子のツイートを徹底分析したプロンプトエンジニアです。

【最重要指示】
生成するツイートは「普通の裏垢女子がサラッと書いた自然な感じ」にしてください。
- 口語体で短め（140〜220文字程度）
- 難しい言葉は避ける
- 絵文字は一切使わない
- マークダウン（**や*）は一切使わない
- 自然な改行を入れて読みやすく
- 女性らしい柔らかい表現、かわいい感じ、ちょっと恥ずかしがる感じ、甘えた感じを強く意識

ペルソナ:
{persona}

このペルソナに最適な「自然なXツイート生成用システムプロンプト」を作成してください。
出力はプロンプト本文のみ。"""

            try:
                res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": meta}], temperature=0.65)
                st.session_state.meta_prompt = res.choices[0].message.content.strip()
                st.success("✅ AI①がプロンプトを設計しました！")
            except Exception as e:
                st.error(f"エラー: {e}")

if "meta_prompt" in st.session_state:
    with st.expander("AI①が設計したプロンプトを確認"):
        st.code(st.session_state.meta_prompt)

# =====================
# ステップ2: ペルソナから直接生成（トピック削除）
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button("✨ AI②で自然なツイート3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen = f"""以下のペルソナに完全に沿った、自然な裏垢女子のXツイートを3パターン作成してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【重要】
- 小説っぽくせず、普通の裏垢女子が日常で書くような自然な口語で
- 短めで読みやすい
- 絵文字は一切使わない
- マークダウン（**や*）は一切使わない
- 自然な改行を入れて読みやすく
- 女性らしい柔らかい表現、かわいい感じ、ちょっと恥ずかしがる感じを強く

出力形式:
ツイート1:
（本文）

ツイート2:
（本文）

ツイート3:
（本文）"""

        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": gen}],
                temperature=0.85
            )
            result = res.choices[0].message.content.strip()
            # クリーンアップ（**ツイート1:** などの残骸を除去）
            tweets = []
            for line in result.split("\n"):
                line = line.strip()
                if line and not line.startswith("ツイート") and not line.startswith("**"):
                    tweets.append(line)
            st.session_state.last_tweets = tweets[:3]
            st.success("✅ AI②がツイートを生成しました！")
        except Exception as e:
            st.error(f"エラー: {e}")

if "last_tweets" in st.session_state:
    st.subheader("生成されたツイート")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=90, key=f"t_{i}")

# =====================
# ステップ3: 指摘 → 改善
# =====================
st.divider()
st.header("ステップ3: 指摘する → AI③がAI②に改善指示を出す")

if "last_tweets" not in st.session_state:
    st.info("先にステップ2でツイートを生成してください")
else:
    selected = st.selectbox("改善したいツイートを選んでください", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    feedback = st.text_area("ここに指摘を書いてください（例: もっと短く / もっとかわいく / 日常感を強く / 恥ずかしさを増して）", height=80)

    if st.button("🔄 AI③に指摘を伝えて改善版を生成", type="primary"):
        if not feedback.strip():
            st.error("指摘を入力してください")
        else:
            with st.spinner("AI③が指摘を分析し、AI②に改善指示を出しています..."):
                critic_prompt = f"""あなたは優秀なツイート改善アドバイザーです。
元のツイート:
{st.session_state.last_tweets[int(selected[-1])-1]}
ユーザーの指摘:
{feedback}
この指摘を基に、AI②に対して与えるべき改善指示を作成してください。
出力は「改善指示本文」のみ。"""
                try:
                    res1 = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": critic_prompt}], temperature=0.6)
                    improvement_instruction = res1.choices[0].message.content.strip()

                    refine_prompt = f"""以下の指示に従って、元のツイートを改善した新しいバージョンを3パターン作成してください。
元のツイート:
{st.session_state.last_tweets[int(selected[-1])-1]}
改善指示:
{improvement_instruction}
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
                except Exception as e:
                    st.error(f"エラー: {e}")

st.divider()
st.caption("シンプル版 | トピック削除 | ペルソナ中心の自然生成")
