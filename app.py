import streamlit as st
from openai import OpenAI
import re

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール")
st.caption("生成数・トーン調整が毎回確実に反映（超強化版）")

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
    st.markdown("### 📏 生成数調整")
    num_tweets = st.slider("生成するツイート数", 1, 30, 5, step=1, key="num_tweets_slider")
    
    st.divider()
    st.markdown("### 📏 1ツイートの目安文字数")
    tweet_length = st.slider("文字数", 10, 250, 140, step=10, key="tweet_length_slider")
    
    st.divider()
    st.markdown("### 🎚️ トーン調整")
    kawaii = st.slider("かわいさ", 0, 100, 65, key="kawaii_slider")
    ero = st.slider("エロさ", 0, 100, 0, key="ero_slider")
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70, key="hazukashi_slider")

# トーン値をsession_stateに保存
if "tone_values" not in st.session_state:
    st.session_state.tone_values = {"kawaii": 65, "ero": 0, "hazukashi": 70}

# =====================
# ステップ1
# =====================
st.header("ステップ1: ペルソナを入力 → AI①が最適プロンプトを設計")
persona = st.text_area("ペルソナ詳細", value=st.session_state.get("persona", ""), height=160)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        st.session_state.persona = persona
        with st.spinner("AI①が設計中..."):
            meta = f"""あなたはXで成功している裏垢女子のツイートを徹底分析したプロンプトエンジニアです。
生成するツイートは以下の条件を**絶対厳守**してください。
- 1ツイートあたり約{st.session_state.get("tweet_length_slider", 140)}文字程度
- 短い自然な口語体
- 自然な改行を入れて読みやすく
- 絵文字・マークダウン一切禁止
- 吐息は1ツイートに最大2回まで

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
        if st.button("🔄 元の設計プロンプトに戻す"):
            st.rerun()

# =====================
# ステップ2
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button(f"✨ AI②で{st.session_state.get('num_tweets_slider', 5)}パターン生成", type="primary"):
    # 最新トーン値を保存
    st.session_state.tone_values = {
        "kawaii": st.session_state.kawaii_slider,
        "ero": st.session_state.ero_slider,
        "hazukashi": st.session_state.hazukashi_slider
    }
    
    if "last_tweets" in st.session_state:
        del st.session_state.last_tweets
    
    with st.spinner(f"AI②が{st.session_state.num_tweets_slider}パターン生成中..."):
        gen = f"""以下のペルソナに完全に沿った自然な裏垢女子のXツイートを**正確に{st.session_state.num_tweets_slider}個**作成してください。
**絶対に**1個も欠けず、1個も余分なく、ちょうど{st.session_state.num_tweets_slider}個だけ出力してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【絶対厳守】
- 各ツイートは約{st.session_state.tweet_length_slider}文字程度
- 短い自然な口語体
- 自然な改行を入れて読みやすく
- 吐息は1ツイートに最大2回まで
- 各ツイートは明確に異なる内容にする

【最優先事項：現在のトーン調整を極端に厳密に反映】
- かわいさ: {st.session_state.tone_values["kawaii"]}%強く出す
- エロさ: {st.session_state.tone_values["ero"]}%
  - 0%の場合：**一切の性的表現・欲情描写・身体のエロい描写・疼く表現・妄想・匂わせ表現を完全排除**する
- 恥ずかしさ: {st.session_state.tone_values["hazukashi"]}%強く出す

出力形式（この形式を**厳密に守って**ください）:
ツイート1:
（本文）

ツイート2:
（本文）

...
合計でちょうど{st.session_state.num_tweets_slider}個まで"""

        use_prompt = st.session_state.get("edited_meta_prompt", st.session_state.meta_prompt)
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": use_prompt}, {"role": "user", "content": gen}],
            temperature=0.92,
            max_tokens=12000  # 生成数に応じて増加
        )
        
        result = res.choices[0].message.content.strip()
        
        # ツイート抽出ロジックを正規表現で大幅強化
        pattern = r'ツイート\s*(\d+)\s*[:：]?\s*(.*?)(?=\s*ツイート\s*\d+\s*[:：]?|\Z)'
        matches = re.findall(pattern, result, re.DOTALL | re.IGNORECASE)
        
        tweets = [match[1].strip() for match in matches]
        
        # 不足分がある場合は警告を表示
        if len(tweets) < st.session_state.num_tweets_slider:
            st.warning(f"⚠️ 生成されたツイートが{len(tweets)}個しかありませんでした（要求：{st.session_state.num_tweets_slider}個）。必要に応じて再生成してください。")
        
        st.session_state.last_tweets = tweets[:st.session_state.num_tweets_slider]
        st.success(f"✅ {len(st.session_state.last_tweets)}パターン生成完了！")

if "last_tweets" in st.session_state:
    st.subheader(f"生成されたツイート（{len(st.session_state.last_tweets)}個）")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=110, key=f"t_{i}")

st.divider()
st.caption("生成ボタンを押すたびに新しい内容が生成されます | 生成数とプロンプト変更が確実に反映")
