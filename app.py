import streamlit as st
import pandas as pd
import json
import io
import asyncio # For async API calls

# Gemini API のための設定（APIキーはCanvas環境で自動的に提供されます）
# const apiKey = "" と指示されているため、PythonではAPIキーを直接記述しません。
# fetch API を使用するため、フロントエンド（JavaScript）での呼び出しを想定します。
# StreamlitのPythonバックエンドから直接APIを呼び出す場合は、requestsライブラリを使用し、
# APIキーは環境変数などから取得する形になりますが、ここではフロントエンドからの呼び出しを想定した説明をします。
# ただし、StreamlitのPythonコード内で直接APIを呼び出す場合は、requestsを使うのが一般的です。
# 今回は、StreamlitのPythonコード内で直接APIを呼び出す形式で実装します。

# --- 初期データ設定 ---
def get_initial_data():
    """標準的なライフプランの初期データを返します。"""
    return {
        "family": {
            "adults": 2,
            "children": 0,
            "years_to_simulate": 30,
            "initial_assets": 5000000, # 初期資産 (円)
            "investment_return_rate": 0.03, # 年間投資利回り (3%)
            "inflation_rate": 0.01 # 年間インフレ率 (1%)
        },
        "income": {
            "monthly_salary_main": 300000, # 主たる収入 (月額)
            "monthly_salary_sub": 0,      # 副収入 (月額)
            "bonus_annual": 600000        # 年間ボーナス
        },
        "expenditure": {
            "housing": 100000,
            "food": 60000,
            "transportation": 20000,
            "education": 0,
            "utilities": 25000,
            "communication": 10000,
            "leisure": 30000,
            "medical": 10000,
            "other": 20000
        }
    }

# --- ライフプランシミュレーションロジック ---
def simulate_life_plan(data):
    """
    入力データに基づいてライフプランをシミュレーションします。
    年間収入、年間支出、年間貯蓄、年末資産を計算します。
    """
    family = data["family"]
    income = data["income"]
    expenditure = data["expenditure"]

    years_to_simulate = family["years_to_simulate"]
    initial_assets = family["initial_assets"]
    investment_return_rate = family["investment_return_rate"]
    inflation_rate = family["inflation_rate"]

    results = []
    current_assets = initial_assets

    for year in range(1, years_to_simulate + 1):
        # 年間収入の計算
        annual_income = (income["monthly_salary_main"] + income["monthly_salary_sub"]) * 12 + income["bonus_annual"]

        # 年間支出の計算 (インフレ考慮)
        current_annual_expenditure = sum(expenditure.values()) * 12 * ((1 + inflation_rate)**(year - 1))

        # 年間貯蓄の計算
        annual_savings = annual_income - current_annual_expenditure

        # 資産の変動 (投資利回り考慮)
        current_assets = current_assets * (1 + investment_return_rate) + annual_savings

        results.append({
            "年": year,
            "年間収入": int(annual_income),
            "年間支出": int(current_annual_expenditure),
            "年間貯蓄": int(annual_savings),
            "年末資産": int(current_assets)
        })
    return pd.DataFrame(results)

# --- Gemini API 呼び出し（シミュレーション） ---
# Streamlitでは直接JSのfetchを呼び出すことはできません。
# Pythonのrequestsライブラリを使ってAPIを呼び出すことを想定します。
# ただし、APIキーの扱いについては、Canvas環境の指示に従い、ここではダミーの関数とします。
async def get_gemini_suggestion(prompt_text):
    """
    Gemini API を呼び出してライフプランの改善点を取得します。
    ここではシミュレーションとしてダミーの応答を返します。
    実際のAPI呼び出しには 'requests' ライブラリを使用します。
    """
    # 実際のAPI呼び出しのペイロード例
    # import requests
    # url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    # headers = {'Content-Type': 'application/json'}
    # payload = {
    #     "contents": [{"role": "user", "parts": [{"text": prompt_text}]}]
    # }
    # response = requests.post(url, headers=headers, json=payload, params={"key": st.secrets["GEMINI_API_KEY"]})
    # if response.status_code == 200:
    #     return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    # else:
    #     return f"API呼び出しエラー: {response.status_code} - {response.text}"

    # デモのためのダミー応答
    await asyncio.sleep(2) # API呼び出しの遅延をシミュレート
    if "貯蓄" in prompt_text and "増やす" in prompt_text:
        return """
        ## ライフプラン改善提案 (Gemini AIによる)

        現在の貯蓄額を増やすための具体的な提案です：

        1.  **支出の見直し:**
            * 食費や娯楽費など、変動費を月5,000円削減する目標を設定しましょう。家計簿アプリの活用や、週ごとの予算設定が有効です。
            * サブスクリプションサービスを定期的に見直し、不要なものは解約しましょう。

        2.  **収入の増加:**
            * 副業やスキルアップのための学習を検討しましょう。
            * 現在の職場で昇給の機会を探ることも重要です。

        3.  **投資戦略の最適化:**
            * NISAやiDeCoなどの非課税制度を最大限に活用し、長期的な資産形成を目指しましょう。
            * リスク許容度に応じて、国内外のインデックスファンドへの分散投資を検討してください。

        これらの提案を組み合わせることで、より強固なライフプランを構築できるでしょう。
        """
    else:
        return """
        ## ライフプラン改善提案 (Gemini AIによる)

        あなたのライフプランについて、より詳細な情報を提供いただければ、具体的な改善点を提案できます。

        例えば、以下のような情報があると、より的確なアドバイスが可能です：
        * 将来の目標（住宅購入、子どもの教育費、老後資金など）
        * 現在の課題（貯蓄が思うように進まない、支出が多いなど）
        * リスク許容度（投資に対する考え方）

        一般的な改善点としては、以下が挙げられます：
        1.  **家計の可視化:** 毎月の収入と支出を正確に把握し、無駄な支出を特定することから始めましょう。
        2.  **目標設定:** 具体的な貯蓄目標や資産形成目標を設定することで、モチベーションを維持しやすくなります。
        3.  **早期からの投資:** 少額からでも良いので、NISAやiDeCoなどを活用し、複利の効果を最大限に活かしましょう。
        4.  **保険の見直し:** 不要な保険に加入していないか、保障内容が適切かを確認しましょう。

        これらの点を考慮し、あなたのライフプランをさらに充実させていきましょう。
        """

# --- Q&Aデータ ---
qa_data = [
    {"q": "ライフプランとは何ですか？", "a": "ライフプランとは、人生の目標や夢を実現するために、将来の収入と支出、資産形成などを計画することです。"},
    {"q": "シミュレーションで何がわかりますか？", "a": "現在の収入と支出、資産状況から、将来の貯蓄額や資産の推移を予測し、目標達成が可能かどうかの目安がわかります。"},
    {"q": "初期値を変更できますか？", "a": "はい、家族構成、収入、支出の各項目で数値を自由に変更してシミュレーションできます。"},
    {"q": "データはどのように保存できますか？", "a": "現在のシミュレーションデータをCSV形式でダウンロードできます。次回利用時にアップロードして続きから始められます。"},
    {"q": "AIからの改善提案はどのように利用しますか？", "a": "あなたのライフプランに関する情報を入力すると、AIがその内容を分析し、改善のための具体的なアドバイスを生成します。"},
    {"q": "このサイトは無料で使えますか？", "a": "はい、このサイトは無料でご利用いただけます。"},
    {"q": "家族が増えた場合のシミュレーションは？", "a": "「家族構成」の項目で「子供」の数を増やしたり、それに応じた教育費などを「支出」に追加してシミュレーションできます。"},
    {"q": "投資利回りはどのように設定すれば良いですか？", "a": "ご自身の投資経験やリスク許容度に合わせて設定してください。一般的には、低リスクの金融商品では低く、高リスクでは高く設定します。"},
    {"q": "老後資金の目標額はどのように計算しますか？", "a": "総務省などの公開データや、ご自身の理想とする老後の生活費から逆算して設定するのが一般的です。"},
    {"q": "住宅ローンのシミュレーションはできますか？", "a": "直接的な住宅ローンシミュレーション機能はありませんが、毎月の返済額を「支出」に加えることで、全体への影響を把握できます。"}
]

# --- Streamlit アプリケーションの構築 ---
def main():
    st.set_page_config(layout="wide", page_title="ライフプランシミュレーション")

    st.title("🏡 ライフプランシミュレーション")
    st.markdown("将来の資産形成を計画し、AIからのアドバイスで改善しましょう。")

    # --- データ管理セクション ---
    st.header("1. データ管理")
    st.markdown("現在のライフプランデータをアップロードまたはダウンロードできます。")

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            # アップロードされたデータを初期データ構造に変換
            st.session_state.data = {
                "family": {
                    "adults": df_uploaded.loc[df_uploaded['項目'] == '大人', '値'].iloc[0] if '大人' in df_uploaded['項目'].values else 2,
                    "children": df_uploaded.loc[df_uploaded['項目'] == '子供', '値'].iloc[0] if '子供' in df_uploaded['項目'].values else 0,
                    "years_to_simulate": df_uploaded.loc[df_uploaded['項目'] == 'シミュレーション年数', '値'].iloc[0] if 'シミュレーション年数' in df_uploaded['項目'].values else 30,
                    "initial_assets": df_uploaded.loc[df_uploaded['項目'] == '初期資産', '値'].iloc[0] if '初期資産' in df_uploaded['項目'].values else 5000000,
                    "investment_return_rate": df_uploaded.loc[df_uploaded['項目'] == '投資利回り', '値'].iloc[0] if '投資利回り' in df_uploaded['項目'].values else 0.03,
                    "inflation_rate": df_uploaded.loc[df_uploaded['項目'] == 'インフレ率', '値'].iloc[0] if 'インフレ率' in df_uploaded['項目'].values else 0.01
                },
                "income": {
                    "monthly_salary_main": df_uploaded.loc[df_uploaded['項目'] == '主たる月収', '値'].iloc[0] if '主たる月収' in df_uploaded['項目'].values else 300000,
                    "monthly_salary_sub": df_uploaded.loc[df_uploaded['項目'] == '副業月収', '値'].iloc[0] if '副業月収' in df_uploaded['項目'].values else 0,
                    "bonus_annual": df_uploaded.loc[df_uploaded['項目'] == '年間ボーナス', '値'].iloc[0] if '年間ボーナス' in df_uploaded['項目'].values else 600000
                },
                "expenditure": {
                    "housing": df_uploaded.loc[df_uploaded['項目'] == '住居費', '値'].iloc[0] if '住居費' in df_uploaded['項目'].values else 100000,
                    "food": df_uploaded.loc[df_uploaded['項目'] == '食費', '値'].iloc[0] if '食費' in df_uploaded['項目'].values else 60000,
                    "transportation": df_uploaded.loc[df_uploaded['項目'] == '交通費', '値'].iloc[0] if '交通費' in df_uploaded['項目'].values else 20000,
                    "education": df_uploaded.loc[df_uploaded['項目'] == '教育費', '値'].iloc[0] if '教育費' in df_uploaded['項目'].values else 0,
                    "utilities": df_uploaded.loc[df_uploaded['項目'] == '光熱費', '値'].iloc[0] if '光熱費' in df_uploaded['項目'].values else 25000,
                    "communication": df_uploaded.loc[df_uploaded['項目'] == '通信費', '値'].iloc[0] if '通信費' in df_uploaded['項目'].values else 10000,
                    "leisure": df_uploaded.loc[df_uploaded['項目'] == '娯楽費', '値'].iloc[0] if '娯楽費' in df_uploaded['項目'].values else 30000,
                    "medical": df_uploaded.loc[df_uploaded['項目'] == '医療費', '値'].iloc[0] if '医療費' in df_uploaded['項目'].values else 10000,
                    "other": df_uploaded.loc[df_uploaded['項目'] == 'その他', '値'].iloc[0] if 'その他' in df_uploaded['項目'].values else 20000
                }
            }
            st.success("データが正常にアップロードされました！")
        except Exception as e:
            st.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
    else:
        if "data" not in st.session_state:
            st.session_state.data = get_initial_data()

    # --- ライフプラン設定セクション ---
    st.header("2. ライフプラン設定")
    st.markdown("標準的な値を参考に、ご自身のライフプランに合わせて数値を調整してください。")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("家族構成・基本設定")
        st.session_state.data["family"]["adults"] = st.number_input(
            "大人 (人数)",
            min_value=1, max_value=10, value=st.session_state.data["family"]["adults"], step=1
        )
        st.session_state.data["family"]["children"] = st.number_input(
            "子供 (人数)",
            min_value=0, max_value=10, value=st.session_state.data["family"]["children"], step=1
        )
        st.session_state.data["family"]["years_to_simulate"] = st.number_input(
            "シミュレーション年数",
            min_value=5, max_value=60, value=st.session_state.data["family"]["years_to_simulate"], step=5
        )
        st.session_state.data["family"]["initial_assets"] = st.number_input(
            "初期資産 (円)",
            min_value=0, value=st.session_state.data["family"]["initial_assets"], step=100000
        )
        st.session_state.data["family"]["investment_return_rate"] = st.number_input(
            "年間投資利回り (%)",
            min_value=0.0, max_value=20.0, value=st.session_state.data["family"]["investment_return_rate"] * 100, step=0.1, format="%.1f"
        ) / 100
        st.session_state.data["family"]["inflation_rate"] = st.number_input(
            "年間インフレ率 (%)",
            min_value=0.0, max_value=10.0, value=st.session_state.data["family"]["inflation_rate"] * 100, step=0.1, format="%.1f"
        ) / 100

    with col2:
        st.subheader("収入 (月額)")
        st.session_state.data["income"]["monthly_salary_main"] = st.number_input(
            "主たる月収 (円)",
            min_value=0, value=st.session_state.data["income"]["monthly_salary_main"], step=10000
        )
        st.session_state.data["income"]["monthly_salary_sub"] = st.number_input(
            "副業月収 (円)",
            min_value=0, value=st.session_state.data["income"]["monthly_salary_sub"], step=5000
        )
        st.session_state.data["income"]["bonus_annual"] = st.number_input(
            "年間ボーナス (円)",
            min_value=0, value=st.session_state.data["income"]["bonus_annual"], step=100000
        )

    with col3:
        st.subheader("支出 (月額)")
        st.session_state.data["expenditure"]["housing"] = st.number_input("住居費 (円)", min_value=0, value=st.session_state.data["expenditure"]["housing"], step=5000)
        st.session_state.data["expenditure"]["food"] = st.number_input("食費 (円)", min_value=0, value=st.session_state.data["expenditure"]["food"], step=1000)
        st.session_state.data["expenditure"]["transportation"] = st.number_input("交通費 (円)", min_value=0, value=st.session_state.data["expenditure"]["transportation"], step=1000)
        st.session_state.data["expenditure"]["education"] = st.number_input("教育費 (円)", min_value=0, value=st.session_state.data["expenditure"]["education"], step=1000)
        st.session_state.data["expenditure"]["utilities"] = st.number_input("光熱費 (円)", min_value=0, value=st.session_state.data["expenditure"]["utilities"], step=500)
        st.session_state.data["expenditure"]["communication"] = st.number_input("通信費 (円)", min_value=0, value=st.session_state.data["expenditure"]["communication"], step=500)
        st.session_state.data["expenditure"]["leisure"] = st.number_input("娯楽費 (円)", min_value=0, value=st.session_state.data["expenditure"]["leisure"], step=1000)
        st.session_state.data["expenditure"]["medical"] = st.number_input("医療費 (円)", min_value=0, value=st.session_state.data["expenditure"]["medical"], step=500)
        st.session_state.data["expenditure"]["other"] = st.number_input("その他 (円)", min_value=0, value=st.session_state.data["expenditure"]["other"], step=1000)

    # --- シミュレーション結果 ---
    st.header("3. シミュレーション結果")
    st.markdown("設定したライフプランに基づいた将来の資産推移です。")

    simulation_df = simulate_life_plan(st.session_state.data)
    st.dataframe(simulation_df.style.format({
        "年間収入": "{:,}円",
        "年間支出": "{:,}円",
        "年間貯蓄": "{:,}円",
        "年末資産": "{:,}円"
    }), use_container_width=True)

    st.line_chart(simulation_df.set_index("年")["年末資産"])
    st.markdown(f"**最終的な年末資産:** {simulation_df['年末資産'].iloc[-1]:,}円")

    # ダウンロードボタン
    # 現在のデータをCSV形式に変換
    download_data = []
    for category, items in st.session_state.data.items():
        for key, value in items.items():
            # 利回りやインフレ率はパーセンテージ表示から元の数値に戻す
            if key == "investment_return_rate" or key == "inflation_rate":
                download_data.append({"項目": key, "値": value})
            else:
                download_data.append({"項目": key, "値": value})

    df_to_download = pd.DataFrame(download_data)
    csv = df_to_download.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="現在のライフプランデータをダウンロード (CSV)",
        data=csv,
        file_name="life_plan_data.csv",
        mime="text/csv",
    )

    # --- AIによる改善提案 ---
    st.header("4. AIによる改善提案")
    st.markdown("あなたのライフプランに関する情報を入力すると、AIが改善点を提案します。")

    user_plan_description = st.text_area(
        "あなたのライフプランについて、目標や課題、現在の状況などを具体的に教えてください。",
        value="現在の収入と支出で、20年後に老後資金として5,000万円を貯蓄したいと考えています。何か改善できる点はありますか？",
        height=150
    )

    if st.button("AIに改善点を尋ねる"):
        if user_plan_description:
            with st.spinner("AIが改善点を考えています..."):
                # ここで非同期関数を呼び出すためにasyncioを使用
                suggestion = asyncio.run(get_gemini_suggestion(user_plan_description))
                st.markdown(suggestion)
        else:
            st.warning("ライフプランの説明を入力してください。")

    # --- Q&Aセクション ---
    st.header("5. よくある質問 (Q&A)")
    st.markdown("ライフプランに関するよくある質問と回答です。")

    for i, qa in enumerate(qa_data):
        with st.expander(f"Q{i+1}. {qa['q']}"):
            st.write(qa['a'])

if __name__ == "__main__":
    main()

