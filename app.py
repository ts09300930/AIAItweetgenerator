import streamlit as st
from openai import OpenAI
import os

st.set_page_config(
    page_title="裏垢女子ツイート生成ツール | 自然ツイート版",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 裏垢女子ツイート生成ツール（persona.txt対応版）")

# =====================
# APIキー
# =====================
with st.sidebar:
    st.header("⚙️ 設定")
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ SecretsからAPIキーを読み込みました")
    else:
        api_key = st.text_input("APIキー（OpenAI or xAI）", type="password")
        if not api_key:
            st.warning("APIキーを入力してください")
            st.stop()

if api_key.startswith("xai-"):
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    MODEL = "grok-4.20"
else:
    client = OpenAI(api_key=api_key)
    MODEL = "gpt-4o-mini"

# =====================
# persona.txt を読み込む（これがあなたの提案した方式）
# =====================
def load_persona():
    if os.path.exists("persona.txt"):
        with open("persona.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    return """23歳の私立女子大生。黒髪ロングで清楚系だけど実は超欲求不満。
日常のちょっとした誘惑を、恥ずかしがりながら可愛く匂わせる感じ。
少し関西弁混じり。「えへへ」「やだ〜」「ドキドキしちゃう…」"""

# セッション状態
if "meta_prompt" not in st.session_state:
    st.session_state.meta_prompt = None
if "tweets" not in st.session_state:
    st.session_state.tweets = []

# =====================
# ステップ1: ペルソナ（persona.txtから自動読み込み）
# =====================
st.header("ステップ1: ペルソナ（persona.txtから自動読み込み）")

persona = st.text_area("ペルソナ詳細", value=load_persona(), height=160)

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 現在のペルソナをダウンロード", use_container_width=True):
        st.download_button(
            label="persona.txtとしてダウンロード",
            data=persona,
            file_name="persona.txt",
            mime="text/plain"
        )
        st.info("ダウンロードしたファイルをGitHubに上書きしてpushしてください")

with col2:
    if st.button("🚀 AI①にプロンプトを作らせる", type="primary", use_container_width=True):
        if not persona.strip():
            st.error("ペルソナを入力してください")
        else:
            with st.spinner("プロンプト作成中..."):
                meta_instruction = f"""あなたはXで活動する裏垢女子のツイートを分析したプロです。

【最重要】
生成するツイートは「普通の裏垢女子がサラッと書いた自然な感じ」にしてください。
- 口語体で短め
- 難しい言葉は避ける
- 絵文字を適度に使う

ペルソナ:
{persona}

このペルソナに合わせた「自然なXツイート生成用システムプロンプト」を作ってください。
出力はプロンプト本文のみ。"""

                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[{"role": "user", "content": meta_instruction}],
                        temperature=0.65
                    )
                    st.session_state.meta_prompt = response.choices[0].message.content.strip()
                    st.success("✅ プロンプト作成完了！")
                except Exception as e:
                    st.error(f"エラー: {e}")

# =====================
# ステップ2 & 3（省略せず全部記載）
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → ツイート生成")

if not st.session_state.meta_prompt:
    st.info("先にステップ1を完了してください")
    st.stop()

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")

if st.button("✨ 自然なツイート3パターン生成", type="primary"):
    with st.spinner("生成中..."):
        gen_prompt = f"""以下のトピックで、普通の裏垢女子が書きそうな自然なXツイートを3パターン作ってください。

トピック: {topic}

【重要】小説っぽくせず、普通のツイートらしい口語で短めにしてください。

出力形式:
ツイート1:
（本文）

ツイート2:
（本文）

ツイート3:
（本文）"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": st.session_state.meta_prompt},
                    {"role": "user", "content": gen_prompt}
                ],
                temperature=0.85
            )
            result = response.choices[0].message.content.strip()
            st.session_state.tweets = [line.strip() for line in result.split("\n") if line.strip() and not line.startswith("ツイート")]
            st.success("✅ 生成完了！")
        except Exception as e:
            st.error(f"エラー: {e}")

if st.session_state.tweets:
    st.subheader("生成されたツイート")
    for i, tweet in enumerate(st.session_state.tweets[:3]):
        st.text_area(f"ツイート{i+1}", value=tweet, height=100, key=f"t_{i}")
        if st.button(f"📋 コピー", key=f"copy_{i}"):
            st.toast("コピーしました！")

# ステップ3（改善）
st.divider()
st.header("ステップ3: 改善してほしい点を伝える")

if st.session_state.tweets:
    selected = st.selectbox("改善したいツイート", [f"ツイート{i+1}" for i in range(len(st.session_state.tweets))])
    feedback = st.text_area("改善してほしい点", height=60)
    
    if st.button("🔄 改善版を生成", type="primary"):
        if feedback.strip():
            with st.spinner("改善中..."):
                try:
                    refine_prompt = f"""以下のツイートを、ユーザーの指摘通りに改善したバージョンを3パターン作ってください。

元のツイート:
{st.session_state.tweets[int(selected[-1])-1]}

改善指示:
{feedback}

出力形式:
改善版1:
（本文）

改善版2:
（本文）

改善版3:
（本文）"""

                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": st.session_state.meta_prompt},
                            {"role": "user", "content": refine_prompt}
                        ],
                        temperature=0.8
                    )
                    refined = response.choices[0].message.content.strip()
                    st.success("✅ 改善版を作成しました！")
                    st.text_area("改善版", value=refined, height=160)
                except Exception as e:
                    st.error(f"エラー: {e}")
        else:
            st.error("改善点を入力してください")

st.divider()
st.caption("persona.txt対応版 | GitHubのpersona.txtを更新すると次回自動で読み込まれます")
