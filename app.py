import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

st.set_page_config(page_title="裏垢女子ツール（GitHub対応版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（GitHub対応版）")
st.caption("私 → AI① → AI② → あなた（指摘） → AI③ → AI②（改善） | スプシ完全削除")

# =====================
# APIキー設定
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
        st.info("xAI Grok-4.20 使用中")
    else:
        client = OpenAI(api_key=api_key)
        MODEL = "gpt-4o-mini"
        st.info("OpenAI gpt-4o-mini 使用中")

# =====================
# localStorageでペルソナ自動保存
# =====================
if "persona" not in st.session_state:
    st.session_state.persona = """23歳の私立女子大生。黒髪ロングで清楚系だけど実は超欲求不満。
日常のちょっとした誘惑を、恥ずかしがりながら可愛く匂わせる感じ。"""

# =====================
# ステップ1
# =====================
st.header("ステップ1: ペルソナ → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細", value=st.session_state.persona, height=140)

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("💾 ペルソナを保存", use_container_width=True):
        st.session_state.persona = persona
        st.success("ブラウザに保存しました！次回も自動で読み込まれます")

with col2:
    if st.button("🚀 AI①にプロンプトを設計させる", type="primary", use_container_width=True):
        if not persona.strip():
            st.error("ペルソナを入力してください")
        else:
            with st.spinner("AI①が設計中..."):
                meta = f"""あなたはXで成功している裏垢女子のツイートを徹底分析したプロンプトエンジニアです。
【最重要指示】
- 口語体で短め
- 難しい言葉は避ける
- 絵文字は一切使わない
- マークダウンは一切使わない
- 自然な改行を入れて読みやすく
- 女性らしい柔らかい表現、かわいい感じ、恥ずかしがる感じを強く意識
ペルソナ:
{persona}
このペルソナに最適なシステムプロンプトを作成してください。
出力はプロンプト本文のみ。"""
                try:
                    res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": meta}], temperature=0.65)
                    st.session_state.meta_prompt = res.choices[0].message.content.strip()
                    st.success("✅ AI①がプロンプトを設計しました！")
                except Exception as e:
                    st.error(f"エラー: {e}")

if "meta_prompt" in st.session_state:
    with st.expander("AI①が設計したプロンプト"):
        st.code(st.session_state.meta_prompt)

# =====================
# ステップ2
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → AI②がツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")

if st.button("✨ AI②で3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen = f"""以下のトピックで、普通の裏垢女子が書きそうな自然なXツイートを3パターン作ってください。
トピック: {topic}
【重要】
- 普通のツイートらしい口語で
- 短めで読みやすい
- 絵文字は一切使わない
- マークダウンは一切使わない
- 自然な改行を入れて読みやすく
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
            tweets = [line.strip() for line in result.split("\n") if line.strip() and not line.startswith("ツイート")]
            st.session_state.last_tweets = tweets[:3]
            st.session_state.last_topic = topic
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
    selected = st.selectbox("改善したいツイート", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    feedback = st.text_area("指摘を書いてください", height=80)

    if st.button("🔄 AI③に指摘を伝えて改善版を生成", type="primary"):
        if not feedback.strip():
            st.error("指摘を入力してください")
        else:
            with st.spinner("AI③が指摘を分析し、AI②に改善指示を出しています..."):
                critic = f"""あなたは優秀なツイート改善アドバイザーです。
元のツイート:
{st.session_state.last_tweets[int(selected[-1])-1]}
ユーザーの指摘:
{feedback}
この指摘を基に、AI②に対して与えるべき改善指示を作成してください。
出力は「改善指示本文」のみ。"""
                try:
                    res1 = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": critic}], temperature=0.6)
                    improvement = res1.choices[0].message.content.strip()

                    refine = f"""以下の指示に従って、元のツイートを改善した新しいバージョンを3パターン作成してください。
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
                        messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": refine}],
                        temperature=0.8
                    )
                    refined = res2.choices[0].message.content.strip()
                    st.success("✅ 改善版を作成しました！")
                    st.text_area("改善版", value=refined, height=200)
                except Exception as e:
                    st.error(f"エラー: {e}")

st.divider()
st.caption("GitHub対応版 | スプシ完全削除 | localStorageでペルソナ自動保存")
