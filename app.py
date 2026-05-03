import streamlit as st
from openai import OpenAI
import gspread
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="裏垢女子ツール（究極版）", layout="wide")
st.title("🌸 裏垢女子ツイート生成ツール（究極版）")
st.caption("私 → AI① → AI② → あなた（指摘） → AI③ → AI②（改善） | 全機能搭載")

# =====================
# Google Sheets接続
# =====================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1cwzwUjCjjHvhDbpjMZnV078pY8mLnUyQCjHasfQsVjg/edit?gid=0#gid=0"
SHEET_NAME = "History"
FAV_SHEET_NAME = "Favorites"

@st.cache_resource
def get_sheet():
    gc = gspread.service_account_from_dict(st.secrets["gspread"])
    sh = gc.open_by_url(SHEET_URL)
    return sh.worksheet(SHEET_NAME), sh.worksheet(FAV_SHEET_NAME)

history_sheet, fav_sheet = get_sheet()

# =====================
# 設定 + トーン調整（サイドバー）
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
    if api_key.startswith("xai-"):
        st.info("xAI Grok-4.20 使用中")
        MODEL = "grok-4.20"
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    else:
        st.info("OpenAI gpt-4o-mini 使用中")
        MODEL = "gpt-4o-mini"
        client = OpenAI(api_key=api_key)

    st.divider()
    st.markdown("### 🎚️ トーン調整")
    kawaii = st.slider("かわいさ", 0, 100, 60)
    ero = st.slider("エロさ", 0, 100, 40)
    hazukashi = st.slider("恥ずかしさ", 0, 100, 70)

    st.divider()
    st.markdown("### 📚 ペルソナプリセット")
    presets = {
        "清楚系欲求不満大学生": "22歳の私立女子大生。黒髪ロングで清楚系だけど実は超欲求不満。日常のちょっとした誘惑を、恥ずかしがりながら可愛く匂わせる感じ。",
        "ギャル系エロかわいい": "21歳のギャル系女子。明るくてエロかわいい感じ。積極的だけど可愛く甘えた話し方。",
        "内気系むらむら女子": "23歳の内気な女子。普段は大人しいけど夜になるとむらむらして一人で妄想しがち。",
        "欲求不満人妻": "28歳の人妻。夫には言えない欲求不満を裏垢で発散。ちょっと大人っぽい色気。",
        "黒髪ロング清楚系": "20歳の黒髪ロングの清楚系女子。見た目は上品だけど実はエロい想像が大好き。",
        "小悪魔系かわいい": "19歳の小悪魔系女子。かわいい顔して意地悪なこと言うのが好き。"
    }
    selected_preset = st.selectbox("プリセットを選択", ["-- 選択 --"] + list(presets.keys()))
    if selected_preset != "-- 選択 --":
        if st.button("📥 このプリセットを読み込む"):
            st.session_state.persona = presets[selected_preset]
            st.rerun()

# =====================
# ステップ1: ペルソナ
# =====================
st.header("ステップ1: ペルソナ → AI①が最適プロンプトを設計")

persona = st.text_area("ペルソナ詳細（できるだけ詳しく）", 
                       value=st.session_state.get("persona", ""), 
                       height=140)

if st.button("🚀 AI①にプロンプトを設計させる", type="primary"):
    if not persona.strip():
        st.error("ペルソナを入力してください")
    else:
        with st.spinner("AI①がXの成功パターンを分析しながらプロンプトを設計中..."):
            meta = f"""あなたはXで成功している裏垢女子のツイートを徹底分析したプロンプトエンジニアです。

【最重要指示】
生成するツイートは「普通の裏垢女子がサラッと書いた自然な感じ」にしてください。
- 口語体で短め
- 難しい言葉は避ける
- 絵文字は一切使わない
- マークダウン（**や*）は一切使わない。純粋なプレーンテキストのみ
- **自然な改行を入れて読みやすくしてください**。1行が長くなりすぎないように意識的に改行を入れて。
- **女性らしい柔らかい表現、かわいい感じ、ちょっと恥ずかしがる感じ、甘えた感じを強く意識**してください。

【トーン調整】
- かわいさレベル: {kawaii}/100
- エロさレベル: {ero}/100
- 恥ずかしさレベル: {hazukashi}/100
これらのレベルに合わせて表現の強さを調整してください。

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
# ステップ2: トピック → AI②生成
# =====================
st.divider()
st.header("ステップ2: トピックを入力 → AI②がツイートを生成")

if "meta_prompt" not in st.session_state:
    st.info("先にステップ1を完了してください")
    st.stop()

topic = st.text_input("トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")

col1, col2 = st.columns(2)
with col1:
    if st.button("✨ AI②で3パターン生成", type="primary"):
        with st.spinner("AI②が生成中..."):
            gen = f"""以下のトピックで、普通の裏垢女子が書きそうな自然なXツイートを3パターン作ってください。

トピック: {topic}

【重要】
- 小説っぽくせず、普通のツイートらしい口語で
- 短めで読みやすい
- 絵文字は一切使わない
- マークダウン（**や*）は一切使わない。純粋なプレーンテキストのみ
- **自然な改行を入れて読みやすく**。1行が長くなりすぎないように意識的に改行を入れて。
- **女性らしい柔らかい表現、かわいい感じ、ちょっと恥ずかしがる感じ、甘えた感じを強く意識**してください。

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

with col2:
    if st.button("🔥 もっとバリエーションを (6ツイート)", type="primary"):
        with st.spinner("AI②が6パターン生成中..."):
            gen = f"""以下のトピックで、普通の裏垢女子が書きそうな自然なXツイートを6パターン作ってください。

トピック: {topic}

【重要】
- 小説っぽくせず、普通のツイートらしい口語で
- 短めで読みやすい
- 絵文字は一切使わない
- マークダウン（**や*）は一切使わない。純粋なプレーンテキストのみ
- **自然な改行を入れて読みやすく**。1行が長くなりすぎないように意識的に改行を入れて。
- **女性らしい柔らかい表現、かわいい感じ、ちょっと恥ずかしがる感じ、甘えた感じを強く意識**してください。

出力形式:
ツイート1:
（本文）

ツイート2:
（本文）

ツイート3:
（本文）

ツイート4:
（本文）

ツイート5:
（本文）

ツイート6:
（本文）"""

            try:
                res = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": gen}],
                    temperature=0.85
                )
                result = res.choices[0].message.content.strip()
                tweets = [line.strip() for line in result.split("\n") if line.strip() and not line.startswith("ツイート")]
                st.session_state.last_tweets = tweets[:6]
                st.session_state.last_topic = topic
                st.success("✅ AI②が6パターン生成しました！")
            except Exception as e:
                st.error(f"エラー: {e}")

if "last_tweets" in st.session_state:
    st.subheader("AI②が生成したツイート")
    for i, t in enumerate(st.session_state.last_tweets):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.text_area(f"ツイート{i+1}", value=t, height=80, key=f"t_{i}")
        with col2:
            if st.button("❤️", key=f"heart_{i}"):
                try:
                    fav_sheet.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        persona,
                        st.session_state.last_topic,
                        t
                    ])
                    st.toast("お気に入りに追加しました！")
                except Exception as e:
                    st.error(f"保存エラー: {e}")

# =====================
# ステップ3: 指摘 → AI③指示 → AI②改善
# =====================
st.divider()
st.header("ステップ3: 指摘する → AI③がAI②に改善指示を出す")

if "last_tweets" not in st.session_state:
    st.info("先にステップ2でツイートを生成してください")
else:
    selected = st.selectbox("改善したいツイートを選んでください（個別改善の場合）", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    feedback = st.text_area("指摘を書いてください（例: もっと短くして / もっとカジュアルに / 谷間チラを強調して / 日常感を強くして）", height=80)

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 このツイートだけ改善", type="primary"):
            if not feedback.strip():
                st.error("指摘を入力してください")
            else:
                with st.spinner("AI③が指摘を分析し、AI②に改善指示を出しています..."):
                    critic_prompt = f"""あなたは優秀なツイート改善アドバイザーです。
元のツイート:
{st.session_state.last_tweets[int(selected[-1])-1]}
ユーザーの指摘:
{feedback}
この指摘を基に、AI②（ツイート生成AI）に対して与えるべき改善指示を作成してください。
指示は具体的で、AI②がすぐに理解してより良いツイートを作れる形にしてください。
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
改善版ツイート1:
（本文）
改善版ツイート2:
（本文）
改善版ツイート3:
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

    with col2:
        if st.button("🔄 この指摘で全部改善（おすすめ）", type="primary"):
            if not feedback.strip():
                st.error("指摘を入力してください")
            else:
                with st.spinner("AI③が指摘を分析し、全部改善しています..."):
                    critic_prompt = f"""あなたは優秀なツイート改善アドバイザーです。
以下の{len(st.session_state.last_tweets)}つのツイートに対して、ユーザーの指摘を反映した改善指示を作成してください。

"""
                    for i, t in enumerate(st.session_state.last_tweets):
                        critic_prompt += f"ツイート{i+1}:\n{t}\n\n"
                    critic_prompt += f"ユーザーの指摘:\n{feedback}\n\nこの指摘を基に、AI②（ツイート生成AI）に対して与えるべき改善指示を作成してください。\n指示は具体的で、全部に適用できる形にしてください。\n出力は「改善指示本文」のみ。"""
                    
                    try:
                        res1 = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": critic_prompt}], temperature=0.6)
                        improvement_instruction = res1.choices[0].message.content.strip()

                        refine_prompt = f"""以下の指示に従って、{len(st.session_state.last_tweets)}つのツイートをすべて改善したバージョンを{len(st.session_state.last_tweets)}パターン作成してください。

"""
                        for i, t in enumerate(st.session_state.last_tweets):
                            refine_prompt += f"ツイート{i+1}:\n{t}\n\n"
                        refine_prompt += f"改善指示:\n{improvement_instruction}\n\n出力形式:\n"
                        for i in range(len(st.session_state.last_tweets)):
                            refine_prompt += f"改善版ツイート{i+1}:\n（本文）\n\n"

                        res2 = client.chat.completions.create(
                            model=MODEL,
                            messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": refine_prompt}],
                            temperature=0.8
                        )
                        refined = res2.choices[0].message.content.strip()
                        st.success("✅ 全部改善版を作成しました！")
                        st.text_area("全部の改善版", value=refined, height=300)
                    except Exception as e:
                        st.error(f"エラー: {e}")

# =====================
# 画像プロンプト生成
# =====================
st.divider()
st.header("📸 画像プロンプト生成（おまけ）")

if "last_tweets" in st.session_state:
    selected_for_img = st.selectbox("画像プロンプトを作りたいツイートを選んでください", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    if st.button("🖼️ このツイートに合う画像プロンプトを生成"):
        with st.spinner("画像プロンプト生成中..."):
            img_prompt = f"""以下のツイートにぴったり合う、AI画像生成用の英語プロンプトを作成してください。

ツイート内容:
{st.session_state.last_tweets[int(selected_for_img[-1])-1]}

【要件】
- 美しい日本人女性（20代前半〜中盤）
- 自然な照明、iPhone撮影風
- 清楚だけどちょっとエロい雰囲気
- 詳細な服装・表情・背景の描写
- 英語で出力してください

出力は英語のプロンプトのみ。"""
            try:
                res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": img_prompt}], temperature=0.7)
                st.success("✅ 画像プロンプト生成完了！")
                st.code(res.choices[0].message.content.strip())
            except Exception as e:
                st.error(f"エラー: {e}")

# =====================
# 投稿プレビュー
# =====================
st.divider()
st.header("📱 投稿プレビュー（おまけ）")

if "last_tweets" in st.session_state:
    selected_for_preview = st.selectbox("プレビューしたいツイートを選んでください", [f"ツイート{i+1}" for i in range(len(st.session_state.last_tweets))])
    if st.button("👀 Xのタイムライン風プレビュー"):
        tweet_text = st.session_state.last_tweets[int(selected_for_preview[-1])-1]
        st.markdown("### 📱 Xタイムライン風プレビュー")
        st.markdown(f"""
        **@ura_aka_girl** · たった今
        \n
        {tweet_text}
        \n
        ❤️ 1,234　🔁 567　💬 89
        """)

# =====================
# A/Bテストモード
# =====================
st.divider()
st.header("🆚 A/Bテストモード（おまけ）")

if "meta_prompt" in st.session_state:
    ab_topic = st.text_input("A/Bテスト用トピック", value="お風呂上がりに鏡を見てちょっとエロいこと想像しちゃった話")
    if st.button("🆚 A/Bテスト生成（かわいい寄り vs エロ寄り）"):
        with st.spinner("A/Bテスト生成中..."):
            # A: かわいい寄り
            gen_a = f"""以下のトピックで、**かわいい寄り**の自然なXツイートを3パターン作ってください。

トピック: {ab_topic}

【重要】
- かわいい感じを強く
- 恥ずかしがる感じを強く
- 甘えた表現を多めに
- 絵文字は一切使わない
- マークダウンは一切使わない

出力形式:
ツイートA1:
（本文）

ツイートA2:
（本文）

ツイートA3:
（本文）"""

            # B: エロ寄り
            gen_b = f"""以下のトピックで、**エロ寄り**の自然なXツイートを3パターン作ってください。

トピック: {ab_topic}

【重要】
- エロい感じを強く
- 欲情した感じを強く
- 大人っぽい色気を多めに
- 絵文字は一切使わない
- マークダウンは一切使わない

出力形式:
ツイートB1:
（本文）

ツイートB2:
（本文）

ツイートB3:
（本文）"""

            try:
                res_a = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": gen_a}],
                    temperature=0.85
                )
                res_b = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": st.session_state.meta_prompt}, {"role": "user", "content": gen_b}],
                    temperature=0.85
                )
                
                st.success("✅ A/Bテスト生成完了！")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("### 🟦 A: かわいい寄りバージョン")
                    st.text_area("A1", value=res_a.choices[0].message.content.split("ツイートA2:")[0].replace("ツイートA1:", "").strip(), height=100)
                    st.text_area("A2", value=res_a.choices[0].message.content.split("ツイートA2:")[1].split("ツイートA3:")[0].strip(), height=100)
                    st.text_area("A3", value=res_a.choices[0].message.content.split("ツイートA3:")[1].strip(), height=100)
                
                with col_b:
                    st.markdown("### 🟥 B: エロ寄りバージョン")
                    st.text_area("B1", value=res_b.choices[0].message.content.split("ツイートB2:")[0].replace("ツイートB1:", "").strip(), height=100)
                    st.text_area("B2", value=res_b.choices[0].message.content.split("ツイートB2:")[1].split("ツイートB3:")[0].strip(), height=100)
                    st.text_area("B3", value=res_b.choices[0].message.content.split("ツイートB3:")[1].strip(), height=100)
                    
            except Exception as e:
                st.error(f"エラー: {e}")

# =====================
# 保存機能
# =====================
st.divider()
if st.button("💾 このペルソナ＋ツイートをスプシに保存", type="primary"):
    if "last_tweets" in st.session_state:
        try:
            sheet = get_sheet()[0]
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                persona,
                st.session_state.last_topic,
                st.session_state.last_tweets[0],
                st.session_state.last_tweets[1],
                st.session_state.last_tweets[2]
            ])
            st.success("✅ スプレッドシートに保存しました！")
        except Exception as e:
            st.error(f"保存エラー: {e}")
    else:
        st.warning("先にツイートを生成してください")

st.caption("究極版 | 全機能搭載 | スプシ保存対応")
