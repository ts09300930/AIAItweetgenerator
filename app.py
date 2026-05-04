import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール")
st.caption("るな専用モード｜トーン調整が毎回確実に反映（強化版）")

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
    tweet_length = st.slider("文字数", 10, 250, 20, step=1, key="tweet_length_slider")  # るな仕様に合わせて20文字前後に調整
    
    st.divider()
    st.markdown("### 🎚️ トーン調整")
    kawaii = st.slider("かわいさ", 0, 100, 40, key="kawaii_slider")   # 過度に可愛くならないようデフォルトを抑えめに
    ero = st.slider("エロさ", 0, 100, 60, key="ero_slider")
    hazukashi = st.slider("恥ずかしさ", 0, 100, 80, key="hazukashi_slider")

# トーン値をsession_stateに保存（2回目以降も確実反映）
if "tone_values" not in st.session_state:
    st.session_state.tone_values = {"kawaii": 40, "ero": 60, "hazukashi": 80}

# =====================
# ステップ1: るな専用プロンプト設定
# =====================
st.header("ステップ1: るな専用システムプロンプト（編集可能）")

# ご提供いただいた「るな」プロンプトをベースに固定（トーンは生成時に動的注入）
runa_base_prompt = """あなたはXで1.2万フォロワーを抱える裏垢女子「るな」として、140cm・Aカップ・ど貧乳・極童顔の成人女性を完璧に体現してください。
あなたは自分の身体に強い劣等感と屈辱を抱いており、それを隠さず甘く卑猥に吐露するのが最大の武器です。
すべてのツイートは以下の条件を**絶対厳守**します。
【鉄則】
- 1ツイート約18〜23文字程度
- 極めて短く自然な女の子の口語体
- 自然な改行を1〜2箇所入れる（読みやすさ重視）
- 絵文字・記号・顔文字・ハッシュタグ一切禁止
- 吐息（はあ、ふう、んっ、ぁ、っなど）は最大2回まで
【言語・感情の特徴】
- 自分を「ちっちゃい」「貧乳」「子供みたい」と卑下しつつ、どこか甘えた嗜虐的な響き
- 男性の視線や性的扱いを意識した、恥ずかしさと興奮が混じったニュアンス
- 過度に可愛くせず、むしろ卑屈で湿ったような雰囲気
- 常に「本音をこぼしている感」を出す"""

if "meta_prompt" not in st.session_state:
    st.session_state.meta_prompt = runa_base_prompt

if st.button("🚀 るな専用プロンプトを適用", type="primary"):
    st.session_state.meta_prompt = runa_base_prompt
    st.success("✅ るな専用プロンプトを適用しました！")

if "meta_prompt" in st.session_state:
    st.divider()
    st.subheader("るな専用システムプロンプト（編集可能）")
    edited_prompt = st.text_area("プロンプト編集", value=st.session_state.meta_prompt, height=380)
    st.session_state.edited_meta_prompt = edited_prompt
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 編集内容で保存", type="primary"):
            st.session_state.meta_prompt = edited_prompt
            st.success("更新しました！")
    with col2:
        if st.button("🔄 元のるなプロンプトに戻す"):
            st.session_state.meta_prompt = runa_base_prompt
            st.rerun()

# =====================
# ステップ2: 生成
# =====================
st.divider()
st.header("ステップ2: るなとしてツイート生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1でプロンプトを適用してください")
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
        # トーン調整を最優先で強く注入した生成指示
        gen = f"""以下の**最優先事項**を厳密に遵守して、るなとして自然なXツイートを**正確に{st.session_state.num_tweets_slider}個**作成してください。

【最優先事項：現在のトーン調整を極端に反映】
- かわいさ: {st.session_state.tone_values["kawaii"]}% → 甘えた卑屈さ・嗜虐的な響きを強調
- エロさ: {st.session_state.tone_values["ero"]}%
  - 0%の場合：一切の性的表現・欲情描写・身体描写・疼く表現・妄想・匂わせを完全排除
  - 80%以上：直接的で露骨な卑猥表現を強く出す
  - 中間値：指定された割合で自然に織り交ぜる
- 恥ずかしさ: {st.session_state.tone_values["hazukashi"]}% → 照れ・ためらい・屈辱のニュアンスを強く出す

【鉄則】
- 各ツイートは約{st.session_state.tweet_length_slider}文字程度（18〜23文字を目安に）
- 各ツイートは明確に異なる内容にする

出力形式:
ツイート1:
（本文）
ツイート2:
（本文）
...
合計でちょうど{st.session_state.num_tweets_slider}個まで"""

        use_prompt = st.session_state.get("edited_meta_prompt", st.session_state.meta_prompt)
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": use_prompt},
                {"role": "user", "content": gen}
            ],
            temperature=0.85,
            max_tokens=8000
        )
        
        result = res.choices[0].message.content.strip()
        
        # ツイート抽出（るな仕様に最適化）
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
        
        st.session_state.last_tweets = tweets[:st.session_state.num_tweets_slider]
        st.success(f"✅ {len(st.session_state.last_tweets)}パターン生成完了！")

if "last_tweets" in st.session_state:
    st.subheader(f"生成されたツイート（{len(st.session_state.last_tweets)}個）")
    for i, t in enumerate(st.session_state.last_tweets):
        st.text_area(f"ツイート{i+1}", value=t, height=90, key=f"t_{i}")

st.divider()
st.caption("生成ボタンを押すたびに新しい内容が生成されます｜るなのキャラクターを維持しつつトーン調整を強く反映")
