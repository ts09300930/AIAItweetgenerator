import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="裏垢女子ツイート生成ツール | 私→AI→AI→改善",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 裏垢女子ツイート生成ツール（Bバージョン）")
st.markdown("### **私 → AI①（分析・プロンプト設計） → AI②（生成） → あなた → AI③（指示） → AI②（改善）**")
st.caption("AIが自分でXを分析 → プロンプト作成 → 生成 → あなたのフィードバックでさらにAIが指示して改善")

# =====================
# APIキー取得 + 自動モデル選択
# =====================
with st.sidebar:
    st.header("⚙️ 設定")
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ Streamlit SecretsからAPIキーを読み込みました")
    else:
        api_key = st.text_input("APIキー（OpenAI or xAI）", type="password")
        if not api_key:
            st.warning("APIキーを入力してください")
            st.stop()
    
    st.divider()
    st.markdown("""
    **このバージョンの特徴**
    - xAI（Grok）APIとOpenAI APIの両方に対応
    - AI①が自分でXを分析してプロンプト作成
    - ハッシュタグ完全禁止
    - フィードバックでAIが改善指示を出す
    """)

# xAIかOpenAIかを自動判別
if api_key.startswith("xai-"):
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
    MODEL = "grok-4.20"          # ← 現在確実に使える最新モデル
    st.sidebar.info("xAI Grok APIを使用中（grok-4.20）")
else:
    client = OpenAI(api_key=api_key)
    MODEL = "gpt-4o-mini"
    st.sidebar.info("OpenAI APIを使用中（gpt-4o-mini）")

# セッション状態
if "meta_prompt" not in st.session_state:
    st.session_state.meta_prompt = None
if "tweets" not in st.session_state:
    st.session_state.tweets = []
if "persona" not in st.session_state:
    st.session_state.persona = ""

# =====================
# ステップ1
# =====================
st.header("ステップ1: ペルソナを入力 → AI①が自分で分析して最適プロンプトを作成")

default_persona = """23歳の私立女子大生。黒髪ロングで清楚系だけど実は超欲求不満。
日常のちょっとした誘惑を、恥ずかしがりながら可愛く匂わせる感じ。
少し関西弁混じり。「えへへ」「やだ〜」「ドキドキしちゃう…」"""

persona = st.text_area("ペルソナ詳細", value=default_persona, height=160)

if st.button("🚀 AI①に『自分で分析してプロンプトを作れ』と指示", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①がXの最新成功パターンを自分で分析中..."):
            meta_instruction = f"""あなたはX（旧Twitter）で最も成功している裏垢女子アカウントを徹底的に研究した、最高のプロンプトエンジニアです。

【タスク】
1. まず、2026年現在のXで「バズりやすい」「むらむらさせる」「会いたくなる」裏垢女子ツイートの傾向を**自分で分析**してください。
2. その分析結果を基に、以下のペルソナに完全に最適化した「ツイート生成専用システムプロンプト」を作成してください。

ペルソナ:
{persona}

【必須条件】
- ハッシュタグは絶対に使わない
- 露骨単語は一切禁止
- 文字数140〜240文字程度
- 出力形式は「3パターンのツイート＋解説」

出力は「システムプロンプト本文」のみ。"""

            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "あなたはX裏垢のトップアナリスト兼プロンプトエンジニアです。"},
                        {"role": "user", "content": meta_instruction}
                    ],
                    temperature=0.7,
                    max_tokens=2200
                )
                st.session_state.meta_prompt = response.choices[0].message.content.strip()
                st.session_state.persona = persona
                st.success("✅ AI①が分析を終え、最適プロンプトを作成しました！")
            except Exception as e:
                st.error(f"エラー: {e}")

if st.session_state.meta_prompt:
    with st.expander("🔍 AI①が作成したプロンプト", expanded=False):
        st.code(st.session_state.meta_prompt, language="markdown")

# =====================
# ステップ2
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → AI②がツイートを生成")

if not st.session_state.meta_prompt:
    st.info("先にステップ1を完了してください")
    st.stop()

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てエロい妄想しちゃった話")

if st.button("✨ AI②で3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen_prompt = f"""以下のトピックで3パターンのツイートを生成してください。

トピック: {topic}

【出力形式】
ツイート1:
（本文）

解説: （なぜ効果的か）

ツイート2:
（本文）

解説: （なぜ効果的か）

ツイート3:
（本文）

解説: （なぜ効果的か）"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": st.session_state.meta_prompt},
                    {"role": "user", "content": gen_prompt}
                ],
                temperature=0.85,
                max_tokens=1600
            )
            result = response.choices[0].message.content.strip()
            st.session_state.tweets = []
            
            lines = result.split("\n")
            current = ""
            for line in lines:
                line = line.strip()
                if line.startswith("ツイート") and ":" in line:
                    if current:
                        st.session_state.tweets.append(current.strip())
                    current = ""
                elif line and not line.startswith("解説:"):
                    current += line + "\n"
            if current:
                st.session_state.tweets.append(current.strip())
            
            st.success("✅ 3パターン生成完了！")
        except Exception as e:
            st.error(f"エラー: {e}")

if st.session_state.tweets:
    st.subheader("生成されたツイート")
    cols = st.columns(3)
    for i, tweet in enumerate(st.session_state.tweets[:3]):
        with cols[i]:
            st.text_area(f"ツイート{i+1}", value=tweet, height=160, key=f"t_{i}")
            if st.button(f"📋 コピー", key=f"copy_{i}"):
                st.toast("コピーしました！")

# =====================
# ステップ3: 改善ループ
# =====================
st.divider()
st.header("ステップ3: 改善してほしい点を伝える → AI③がAI②に指示して改善版を作成")

if not st.session_state.tweets:
    st.info("先にツイートを生成してください")
else:
    selected = st.selectbox("改善したいツイートを選んでください", 
                           [f"ツイート{i+1}" for i in range(len(st.session_state.tweets))])
    feedback = st.text_area("ダメなところ・改善してほしい点", 
                            placeholder="例: もっと恥ずかしがってる感じを強くして",
                            height=100)
    
    if st.button("🔄 AI③にフィードバックを伝えて改善版を生成", type="primary"):
        if not feedback.strip():
            st.error("改善点を入力してください")
        else:
            with st.spinner("AI③が指摘を分析し、AI②に改善指示を出しています..."):
                critic_prompt = f"""あなたは優秀なツイート改善アドバイザーです。

元のツイート:
{st.session_state.tweets[int(selected[-1])-1]}

ユーザーの指摘:
{feedback}

この指摘を基に、AI②に対して与えるべき改善指示を作成してください。
出力は「改善指示本文」のみ。"""

                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": "あなたはツイート改善の専門家です。"},
                            {"role": "user", "content": critic_prompt}
                        ],
                        temperature=0.6
                    )
                    improvement_instruction = response.choices[0].message.content.strip()
                    
                    refine_prompt = f"""以下の指示に従って、元のツイートを改善した新しいバージョンを3パターン作成してください。

元のツイート:
{st.session_state.tweets[int(selected[-1])-1]}

改善指示:
{improvement_instruction}

出力形式:
改善版ツイート1:
（本文）

改善版ツイート2:
（本文）

改善版ツイート3:
（本文）"""

                    response2 = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": st.session_state.meta_prompt},
                            {"role": "user", "content": refine_prompt}
                        ],
                        temperature=0.8
                    )
                    refined = response2.choices[0].message.content.strip()
                    
                    st.success("✅ 改善版を作成しました！")
                    st.subheader("改善版ツイート")
                    st.text_area("改善版", value=refined, height=200)
                    
                except Exception as e:
                    st.error(f"エラー: {e}")

st.divider()
st.caption("xAI Grok API / OpenAI API 両対応（モデル自動選択）")
