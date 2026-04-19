import streamlit as st
from openai import OpenAI
import gspread
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="裏垢女子ツール（完全版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（完全版）")
st.caption("私 → AI① → AI② → あなた（指摘） → AI③（指示） → AI②（改善）")

# =====================
# Google Sheets接続
# =====================
SHEET_URL = "https://docs.google.com/spreadsheets/d/ここにあなたのスプレッドシートIDを入れてください"
SHEET_NAME = "History"

@st.cache_resource
def get_sheet():
    gc = gspread.service_account_from_dict(st.secrets["gspread"])
    return gc.open_by_url(SHEET_URL).worksheet(SHEET_NAME)

# =====================
# 設定（サイドバー）
# =====================
with st.sidebar:
    st.header("⚙️ 設定")
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ SecretsからAPIキーを読み込みました")
    else:
        api_key = st.text_input("APIキー", type="password")
        if not api_key: st.stop()

    st.divider()
    st.markdown("**現在のモデル**")
    if api_key.startswith("xai-"):
        st.info("xAI Grok-4.20 使用中")
        MODEL = "grok-4.20"
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    else:
        st.info("OpenAI gpt-4o-mini 使用中")
        MODEL = "gpt-4o-mini"
        client = OpenAI(api_key=api_key)

# =====================
# ステップ1: ペルソナ → AI①設計
# =====================
st.header("ステップ1: ペルソナ → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細", height=140)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①が設計中..."):
            meta = f"""あなたはXの裏垢女子ツイートを分析したプロンプトエンジニアです。
生成するツイートは「普通の裏垢女子がサラッと書いた自然な感じ」にしてください。
ペルソナ: {persona}
出力はプロンプト本文のみ。"""
            try:
                res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": meta}], temperature=0.65)
                st.session_state.meta_prompt = res.choices[0].message.content.strip()
                st.success("✅ AI①がプロンプトを設計しました！")
            except Exception as e:
                st.error(str(e))

if "meta_prompt" in st.session_state:
    with st.expander("AI①が設計したプロンプト"):
        st.code(st.session_state.meta_prompt)

# =====================
# ステップ2: トピック → AI②生成
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → AI②がツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")

if st.button("✨ AI②で3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen = f"""以下のトピックで自然なXツイートを3パターン作ってください。\nトピック: {topic}\n\n出力形式:\nツイート1:\n（本文）\n\nツイート2:\n（本文）\n\nツイート3:\n（本文）"""
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
            st.error(str(e))

if "last_tweets" in st.session_state:
    st.subheader("AI②が生成したツイート")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=90, key=f"t_{i}")

# =====================
# ステップ3: あなたが指摘 → AI③が指示 → AI②が改善（これが一番大事！）
# =====================
st.divider()
st.header("ステップ3: 指摘する → AI③がAI②に改善指示を出す")

if "last_tweets" not in st.session_state:
    st.info("先にステップ2でツイートを生成してください")
else:
    selected = st.selectbox("改善したいツイートを選んでください", [f"ツイート{i+1}" for i in range(3)])
    feedback = st.text_area("ここに指摘を書いてください（例: もっと短くして / もっとカジュアルに / 谷間チラを強調して）", height=80)

    if st.button("🔄 AI③に指摘を伝えて改善版を生成", type="primary"):
        if not feedback.strip():
            st.error("指摘を入力してください")
        else:
            with st.spinner("AI③が指摘を分析し、AI②に改善指示を出しています..."):
                # AI③が指摘を処理
                critic = f"""あなたは優秀なツイート改善アドバイザーです。
元のツイート: {st.session_state.last_tweets[int(selected[-1])-1]}
ユーザーの指摘: {feedback}
この指摘を基に、AI②に対して与えるべき改善指示を作成してください。
出力は「改善指示本文」のみ。"""
                try:
                    res1 = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": critic}], temperature=0.6)
                    improvement = res1.choices[0].message.content.strip()

                    # AI②が改善版を生成
                    refine = f"""以下の指示に従って、元のツイートを改善した新しいバージョンを3パターン作ってください。\n\n元のツイート:\n{st.session_state.last_tweets[int(selected[-1])-1]}\n\n改善指示:\n{improvement}\n\n出力形式:\n改善版1:\n（本文）\n\n改善版2:\n（本文）\n\n改善版3:\n（本文）"""
                    res2 = client.chat.completions.create(
                        model=MODEL,
                        messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": refine}],
                        temperature=0.8
                    )
                    refined = res2.choices[0].message.content.strip()
                    st.success("✅ AI③が指示を出し、AI②が改善版を作成しました！")
                    st.text_area("改善版ツイート", value=refined, height=200)
                except Exception as e:
                    st.error(str(e))

st.divider()
st.caption("最終版 | 私 → AI① → AI② → あなた（指摘） → AI③ → AI②（改善） の完全チェーン")
