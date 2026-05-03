import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="裏垢女子ツール（最終修正版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（最終修正版）")
st.caption("ペルソナ中心 | 自然生成 | 形式厳守強化済み")

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
            meta = f"""あなたはXでフォロワー数万人の裏垢女子アカウントを長年運営しているプロンプトエンジニアです。

生成するツイートは以下の条件を**絶対厳守**してください。
- 140〜220文字程度の短め口語体
- 一切絵文字を使わない
- マークダウン（**や*）など一切の装飾を使わない
- 難しい言葉は完全禁止、超日常的な女の子の言葉遣いのみ
- 自然な改行を入れて、読んだ時に「ふとした瞬間に投稿した感」を出す
- 女性らしい柔らかさ、ちょっと恥ずかしがるニュアンス、甘えた感じ、拗ねた感じを強く出す
- 低身長・童顔・貧乳などのコンプレックスをネタにしつつも、直接的すぎず「かわいいのに…」みたいな遠回しで可愛い自虐を入れる
- 「はぁ...」「ん...」「だめだよぉ...」などの甘い溜息や語尾を自然に使う
- 裏垢女子特有の「誰にも言えないような欲求や照れ」をサラッと零す雰囲気

ペルソナ:
{persona}

このペルソナに完全に最適化した「自然なXツイート生成用システムプロンプト」を作成してください。
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
# ステップ2: ペルソナから直接生成（形式を極限まで強化）
# =====================
st.divider()
st.header("ステップ2: ペルソナからAI②が自然にツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

if st.button("✨ AI②で自然なツイート3パターン生成", type="primary"):
    with st.spinner("AI②が生成中..."):
        gen = f"""以下のペルソナに完全に沿った、自然で魅力的な裏垢女子のXツイートを**3パターン**作成してください。

ペルソナ:
{st.session_state.get("persona", persona)}

【絶対厳守ルール】
- 各ツイートは140〜220文字程度の**完全な一つのツイート**として出力
- 短い断片や不完全な文章は絶対に作らない
- 絵文字は一切使わない
- マークダウン（**や*）は一切使わない
- 自然な改行を入れて読みやすく
- 女性らしい柔らかさ、恥ずかしさ、甘えた感じを強く出す

**以下の形式でしか出力しない**：
ツイート1:
（ここに完全なツイート本文）

ツイート2:
（ここに完全なツイート本文）

ツイート3:
（ここに完全なツイート本文）"""

        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": st.session_state.meta_prompt},
                    {"role": "user", "content": gen}
                ],
                temperature=0.75,   # 少し下げて形式を守りやすく
                max_tokens=2000
            )
            result = res.choices[0].message.content.strip()

            # より頑丈なパース処理
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
            st.success("✅ AI②がツイートを生成しました！")
        except Exception as e:
            st.error(f"エラー: {e}")

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
    selected = st.selectbox("改善したいツイートを選んでください", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    feedback = st.text_area("指摘を書いてください", height=80)

    if st.button("🔄 AI③に指摘を伝えて改善版を生成", type="primary"):
        if not feedback.strip():
            st.error("指摘を入力してください")
        else:
            with st.spinner("改善中..."):
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
st.caption("最終修正版 | 生成形式を極限まで強化")
