import streamlit as st
import pandas as pd
import json
import io
import asyncio # For async API calls
import numpy as np # For financial calculations

# Gemini API のための設定（APIキーはCanvas環境で自動的に提供されます）
# StreamlitのPythonバックエンドから直接APIを呼び出す形式で実装します。

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
            "inflation_rate": 0.01, # 年間インフレ率 (1%)
            "income_growth_rate": 0.01 # 10年ごとの収入上昇率 (1%)
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
        },
        "temporary_expenditures": {
            "education_lump_sum_year": 10, # 教育費一時支出の年
            "education_lump_sum_amount": 0, # 教育費一時支出額 (例: 大学入学金)
            "housing_lump_sum_year": 15, # 住宅購入一時支出の年
            "housing_lump_sum_amount": 0, # 住宅購入一時支出額 (例: 頭金)
        },
        "insurance": {
            "life_insurance_monthly_premium": 0, # 生命保険月額保険料
            "endowment_insurance_monthly_premium": 0, # 満期保険月額保険料
            "endowment_insurance_maturity_year": 20, # 満期保険の満期年
            "endowment_insurance_payout_amount": 0, # 満期保険の受取額
        },
        "housing_loan": {
            "loan_amount": 0, # 借入額
            "loan_interest_rate": 0.01, # 年間金利 (%)
            "loan_term_years": 35, # 返済期間 (年)
        }
    }

# --- 住宅ローン月額返済額計算 ---
def calculate_monthly_loan_payment(loan_amount, annual_interest_rate, loan_term_years):
    """
    住宅ローンの月額返済額を計算します。
    PMT (Payment) 関数を使用します。
    """
    if loan_amount <= 0 or loan_term_years <= 0:
        return 0

    monthly_interest_rate = annual_interest_rate / 12
    num_payments = loan_term_years * 12

    if monthly_interest_rate == 0:
        return loan_amount / num_payments
    else:
        # PMT formula: P * [ i(1 + i)^n ] / [ (1 + i)^n – 1]
        # P = Principal (loan_amount)
        # i = monthly interest rate
        # n = number of payments
        return loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate)**num_payments) / ((1 + monthly_interest_rate)**num_payments - 1)

# --- ライフプランシミュレーションロジック ---
def simulate_life_plan(data):
    """
    入力データに基づいてライフプランをシミュレーションします。
    年間収入、年間支出、年間貯蓄、年末資産を計算します。
    """
    family = data["family"]
    income = data["income"]
    expenditure = data["expenditure"]
    temporary_expenditures = data["temporary_expenditures"]
    insurance = data["insurance"]
    housing_loan = data["housing_loan"]

    years_to_simulate = family["years_to_simulate"]
    initial_assets = family["initial_assets"]
    investment_return_rate = family["investment_return_rate"]
    inflation_rate = family["inflation_rate"]
    income_growth_rate = family["income_growth_rate"]

    results = []
    current_assets = initial_assets

    # 現在の収入を追跡するための変数
    current_monthly_salary_main = income["monthly_salary_main"]
    current_monthly_salary_sub = income["monthly_salary_sub"]
    current_bonus_annual = income["bonus_annual"]

    # 住宅ローンの月額返済額を事前に計算
    monthly_loan_payment = calculate_monthly_loan_payment(
        housing_loan["loan_amount"],
        housing_loan["loan_interest_rate"],
        housing_loan["loan_term_years"]
    )

    for year in range(1, years_to_simulate + 1):
        # 収入の上昇率を10年ごとに考慮
        if (year - 1) % 10 == 0 and year > 1: # 10年目、20年目...に上昇
            current_monthly_salary_main *= (1 + income_growth_rate)
            current_bonus_annual *= (1 + income_growth_rate)

        # 年間収入の計算
        annual_income = (current_monthly_salary_main + current_monthly_salary_sub) * 12 + current_bonus_annual

        # 基本年間支出の計算 (インフレ考慮)
        base_annual_expenditure = sum(expenditure.values()) * 12
        inflated_base_annual_expenditure = base_annual_expenditure * ((1 + inflation_rate)**(year - 1))

        # 保険料の年間支出
        annual_insurance_premium = (insurance["life_insurance_monthly_premium"] + insurance["endowment_insurance_monthly_premium"]) * 12

        # 住宅ローン返済額の年間支出
        annual_loan_payment = 0
        if year <= housing_loan["loan_term_years"]: # ローン返済期間中のみ
            annual_loan_payment = monthly_loan_payment * 12

        # 合計年間支出
        current_annual_expenditure = inflated_base_annual_expenditure + annual_insurance_premium + annual_loan_payment

        # 年間貯蓄の計算
        annual_savings = annual_income - current_annual_expenditure

        # 資産の変動 (投資利回り考慮)
        current_assets = current_assets * (1 + investment_return_rate) + annual_savings

        # 一時的な支出の処理
        if year == temporary_expenditures["education_lump_sum_year"]:
            current_assets -= temporary_expenditures["education_lump_sum_amount"]
        if year == temporary_expenditures["housing_lump_sum_year"]:
            current_assets -= temporary_expenditures["housing_lump_sum_amount"]

        # 満期保険の受取処理
        if year == insurance["endowment_insurance_maturity_year"]:
            current_assets += insurance["endowment_insurance_payout_amount"]

        results.append({
            "年": year,
            "年間収入": int(annual_income),
            "年間支出": int(current_annual_expenditure),
            "年間貯蓄": int(annual_savings),
            "年末資産": int(current_assets)
        })
    return pd.DataFrame(results)

# --- Gemini API 呼び出し（シミュレーション） ---
async def get_gemini_suggestion(user_plan_description, simulation_df, current_data):
    """
    Gemini API を呼び出してライフプランの改善点を取得します。
    ここではシミュレーションとして、シミュレーション結果を反映した応答を返します。
    """
    # 実際のAPI呼び出しは、requestsライブラリなどを使用し、
    # st.secrets["GEMINI_API_KEY"] からAPIキーを取得する形になります。

    # シミュレーション結果から主要なメトリクスを抽出
    final_assets = simulation_df['年末資産'].iloc[-1]
    initial_assets = current_data["family"]["initial_assets"]
    years_to_simulate = current_data["family"]["years_to_simulate"]
    average_annual_savings = simulation_df['年間貯蓄'].mean()
    average_annual_income = simulation_df['年間収入'].mean()
    average_annual_expenditure = simulation_df['年間支出'].mean()

    # AIへのプロンプトを構築
    prompt_text = f"""
    ユーザーのライフプランの説明: {user_plan_description}

    現在のシミュレーション結果の概要:
    - シミュレーション期間: {years_to_simulate} 年
    - 初期資産: {initial_assets:,} 円
    - 最終年末資産: {final_assets:,} 円
    - 年間平均貯蓄額: {int(average_annual_savings):,} 円
    - 年間平均収入: {int(average_annual_income):,} 円
    - 年間平均支出: {int(average_annual_expenditure):,} 円

    上記シミュレーション結果とユーザーの説明に基づき、ライフプランの改善点を具体的に提案してください。
    特に、最終資産が目標に届かない場合や、貯蓄を増やしたい場合に焦点を当て、具体的な行動計画を含めてください。
    """

    # デモのためのダミー応答
    await asyncio.sleep(2) # API呼び出しの遅延をシミュレート

    suggestion_output = f"## ライフプラン改善提案 (Gemini AIによる)\n\n"
    suggestion_output += f"現在のシミュレーションでは、**{years_to_simulate}年後の年末資産は {final_assets:,} 円** と予測されています。\n"
    suggestion_output += f"年間平均貯蓄額は {int(average_annual_savings):,} 円です。\n\n"

    if final_assets < 0:
        suggestion_output += """
        ### 🚨 資産がマイナスに転じる可能性があります！緊急の見直しが必要です。

        * **支出の大幅な削減:** 特に住居費、食費、娯楽費など、大きな割合を占める支出から見直し、可能な限り削減目標を設定しましょう。
        * **収入の増加:** 副業、転職、スキルアップなど、収入を増やすための具体的な計画を立てましょう。
        * **資産の早期取り崩し検討:** 必要であれば、初期資産の一部を計画的に取り崩すことも視野に入れる必要があります。
        """
    elif final_assets < 30000000: # 例: 3000万円を目標値の目安とする
        suggestion_output += """
        ### ⚠️ 資産形成の加速が必要です。

        * **貯蓄率の向上:**
            * 現在の年間平均貯蓄額 {int(average_annual_savings):,} 円を、例えば月5,000円（年間60,000円）増やすことを目標にしましょう。
            * 固定費（通信費、保険料など）の見直しは、一度見直せば継続的な効果があります。
        * **投資戦略の最適化:**
            * NISAやiDeCoなどの非課税制度を最大限に活用し、長期的な視点で積立投資を継続しましょう。
            * 現在の投資利回り {current_data["family"]["investment_return_rate"]*100:.1f}% を維持しつつ、分散投資を心がけましょう。
        * **臨時収入の活用:** ボーナスや臨時収入は、積極的に貯蓄や投資に回すことを検討してください。
        """
    else:
        suggestion_output += """
        ### ✅ 素晴らしいライフプランです！さらなる最適化を目指しましょう。

        * **資産運用の多様化:**
            * 現在の資産運用が順調に進んでいます。さらなるリスク分散のため、国内外の株式、債券、不動産など、投資対象の多様化を検討しましょう。
            * 目標とするリターンに応じて、ポートフォリオのリバランスを定期的に行いましょう。
        * **将来の目標再設定:**
            * 早期リタイア、セカンドハウス購入、社会貢献活動など、新たなライフイベントや目標を設定し、それに向けてプランを微調整しましょう。
        * **インフレ対策:**
            * インフレが資産価値に与える影響を考慮し、インフレに強い資産への投資も検討しましょう。
        """

    suggestion_output += "\n\n" + prompt_text # AIが受け取ったプロンプトも参考として表示

    return suggestion_output

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

# --- 各項目の期待される型を定義するマップ ---
# CSVからの読み込み時にこのマップを使って型変換を行う
TYPE_MAP = {
    "family.adults": int,
    "family.children": int,
    "family.years_to_simulate": int,
    "family.initial_assets": int,
    "family.investment_return_rate": float,
    "family.inflation_rate": float,
    "family.income_growth_rate": float,

    "income.monthly_salary_main": int,
    "income.monthly_salary_sub": int,
    "income.bonus_annual": int,

    "expenditure.housing": int,
    "expenditure.food": int,
    "expenditure.transportation": int,
    "expenditure.education": int,
    "expenditure.utilities": int,
    "expenditure.communication": int,
    "expenditure.leisure": int,
    "expenditure.medical": int,
    "expenditure.other": int,

    "temporary_expenditures.education_lump_sum_year": int,
    "temporary_expenditures.education_lump_sum_amount": int,
    "temporary_expenditures.housing_lump_sum_year": int,
    "temporary_expenditures.housing_lump_sum_amount": int,

    "insurance.life_insurance_monthly_premium": int,
    "insurance.endowment_insurance_monthly_premium": int,
    "insurance.endowment_insurance_maturity_year": int,
    "insurance.endowment_insurance_payout_amount": int,

    "housing_loan.loan_amount": int,
    "housing_loan.loan_interest_rate": float,
    "housing_loan.loan_term_years": int,
}

# --- データをフラット化してCSV用に変換するヘルパー関数 ---
def flatten_data_for_csv(data_dict):
    flattened = []
    for category, items in data_dict.items():
        if isinstance(items, dict):
            for key, value in items.items():
                flattened.append({"項目": f"{category}.{key}", "値": value})
        else: # トップレベルの項目があれば (現状はなし)
            flattened.append({"項目": category, "値": items})
    return pd.DataFrame(flattened)

# --- CSVからデータを読み込み、ネストされた辞書に変換するヘルパー関数 ---
def unflatten_data_from_csv(df_uploaded, initial_data_structure):
    new_data = initial_data_structure.copy() # 初期構造をコピーして変更

    for index, row in df_uploaded.iterrows():
        item_path_str = row["項目"]
        value = row["値"]

        # TYPE_MAPから期待される型を取得
        target_type = TYPE_MAP.get(item_path_str)

        if target_type:
            try:
                # pandasが数値を読み込む際にNaNになることがあるため、NaNチェック
                if pd.isna(value):
                    # NaNの場合、デフォルト値（0や0.0）を設定するか、Noneにするか検討
                    # number_inputはNoneを受け入れないので、0を設定するのが安全
                    value = 0 if target_type == int else 0.0
                else:
                    value = target_type(value)
            except (ValueError, TypeError):
                # 型変換に失敗した場合の処理
                st.warning(f"Warning: Could not convert '{value}' for '{item_path_str}' to {target_type.__name__}. Using default value (0 or 0.0).")
                value = 0 if target_type == int else 0.0 # デフォルト値を設定してエラーを回避
        # else: # TYPE_MAPにない項目はそのままの値を使用 (現状は全ての項目がマップにあるはず)
        #     pass

        current_dict = new_data
        path_parts = item_path_str.split('.')
        for i, key_part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                # 最終要素は値を設定
                current_dict[key_part] = value
            else:
                # 中間要素は辞書が存在するか確認し、なければ作成
                if key_part not in current_dict or not isinstance(current_dict[key_part], dict):
                    current_dict[key_part] = {}
                current_dict = current_dict[key_part]
    return new_data


# --- Streamlit アプリケーションの構築 ---
def main():
    st.set_page_config(layout="wide", page_title="ライフプランシミュレーション")

    st.title("🏡 ライフプランシミュレーション")
    st.markdown("将来の資産形成を計画し、AIからのアドバイスで改善しましょう。")

    # --- サイドバーにQ&Aセクションを配置 ---
    with st.sidebar:
        st.header("よくある質問 (Q&A)")
        st.markdown("ライフプランに関するよくある質問と回答です。")
        for i, qa in enumerate(qa_data):
            with st.expander(f"Q{i+1}. {qa['q']}"):
                st.write(qa['a'])

    # --- データ管理セクション ---
    st.header("1. データ管理")
    st.markdown("現在のライフプランデータをアップロードまたはダウンロードできます。")

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            st.write("--- アップロードされたデータ ---")
            st.dataframe(df_uploaded, use_container_width=True) # アップロードされたデータを表示

            # アップロードされたデータをセッションステートに反映
            # この処理により、st.session_state.dataが更新され、
            # その後の入力フィールドのvalueが自動的に更新されます。
            st.session_state.data = unflatten_data_from_csv(df_uploaded, get_initial_data())
            st.success("データが正常にアップロードされ、反映されました！")
        except Exception as e:
            st.error(f"ファイルの読み込み中にエラーが発生しました。ファイル形式が正しいか確認してください。エラー: {e}")
            # エラー時に初期データを再設定
            if "data" not in st.session_state:
                st.session_state.data = get_initial_data()
    else:
        # アプリ初回起動時やファイルがアップロードされていない場合に初期データを設定
        if "data" not in st.session_state:
            st.session_state.data = get_initial_data()

    # --- ライフプラン設定セクション ---
    st.header("2. ライフプラン設定")
    st.markdown("標準的な値を参考に、ご自身のライフプランに合わせて数値を調整してください。")

    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2) # 新しいセクションのための列

    with col1:
        st.subheader("家族構成・基本設定")
        # 各st.number_inputのvalueはst.session_state.dataから取得されるため、
        # アップロードによってst.session_state.dataが更新されると、
        # これらの入力フィールドも自動的に更新されます。
        st.session_state.data["family"]["adults"] = st.number_input(
            "大人 (人数)",
            min_value=1, max_value=10, value=st.session_state.data["family"]["adults"], step=1, key="adults_input"
        )
        st.session_state.data["family"]["children"] = st.number_input(
            "子供 (人数)",
            min_value=0, max_value=10, value=st.session_state.data["family"]["children"], step=1, key="children_input"
        )
        st.session_state.data["family"]["years_to_simulate"] = st.number_input(
            "シミュレーション年数",
            min_value=5, max_value=60, value=st.session_state.data["family"]["years_to_simulate"], step=5, key="years_input"
        )
        st.session_state.data["family"]["initial_assets"] = st.number_input(
            "初期資産 (円)",
            min_value=0, value=st.session_state.data["family"]["initial_assets"], step=100000, key="initial_assets_input"
        )
        st.session_state.data["family"]["investment_return_rate"] = st.number_input(
            "年間投資利回り (%)",
            min_value=0.0, max_value=20.0, value=st.session_state.data["family"]["investment_return_rate"] * 100, step=0.1, format="%.1f", key="investment_rate_input"
        ) / 100
        st.session_state.data["family"]["inflation_rate"] = st.number_input(
            "年間インフレ率 (%)",
            min_value=0.0, max_value=10.0, value=st.session_state.data["family"]["inflation_rate"] * 100, step=0.1, format="%.1f", key="inflation_rate_input"
        ) / 100
        st.session_state.data["family"]["income_growth_rate"] = st.number_input(
            "10年ごとの収入上昇率 (%)",
            min_value=0.0, max_value=10.0, value=st.session_state.data["family"]["income_growth_rate"] * 100, step=0.1, format="%.1f", key="income_growth_rate_input"
        ) / 100

    with col2:
        st.subheader("収入 (月額)")
        st.session_state.data["income"]["monthly_salary_main"] = st.number_input(
            "主たる月収 (円)",
            min_value=0, value=st.session_state.data["income"]["monthly_salary_main"], step=10000, key="salary_main_input"
        )
        st.session_state.data["income"]["monthly_salary_sub"] = st.number_input(
            "副業月収 (円)",
            min_value=0, value=st.session_state.data["income"]["monthly_salary_sub"], step=5000, key="salary_sub_input"
        )
        st.session_state.data["income"]["bonus_annual"] = st.number_input(
            "年間ボーナス (円)",
            min_value=0, value=st.session_state.data["income"]["bonus_annual"], step=100000, key="bonus_annual_input"
        )

    with col3:
        st.subheader("支出 (月額)")
        st.session_state.data["expenditure"]["housing"] = st.number_input("住居費 (円)", min_value=0, value=st.session_state.data["expenditure"]["housing"], step=5000, key="housing_input")
        st.session_state.data["expenditure"]["food"] = st.number_input("食費 (円)", min_value=0, value=st.session_state.data["expenditure"]["food"], step=1000, key="food_input")
        st.session_state.data["expenditure"]["transportation"] = st.number_input("交通費 (円)", min_value=0, value=st.session_state.data["expenditure"]["transportation"], step=1000, key="transportation_input")
        st.session_state.data["expenditure"]["education"] = st.number_input("教育費 (円)", min_value=0, value=st.session_state.data["expenditure"]["education"], step=1000, key="education_input")
        st.session_state.data["expenditure"]["utilities"] = st.number_input("光熱費 (円)", min_value=0, value=st.session_state.data["expenditure"]["utilities"], step=500, key="utilities_input")
        st.session_state.data["expenditure"]["communication"] = st.number_input("通信費 (円)", min_value=0, value=st.session_state.data["expenditure"]["communication"], step=500, key="communication_input")
        st.session_state.data["expenditure"]["leisure"] = st.number_input("娯楽費 (円)", min_value=0, value=st.session_state.data["expenditure"]["leisure"], step=1000, key="leisure_input")
        st.session_state.data["expenditure"]["medical"] = st.number_input("医療費 (円)", min_value=0, value=st.session_state.data["expenditure"]["medical"], step=500, key="medical_input")
        st.session_state.data["expenditure"]["other"] = st.number_input("その他 (円)", min_value=0, value=st.session_state.data["expenditure"]["other"], step=1000, key="other_input")

    with col4:
        st.subheader("一時的な支出 (三大支出)")
        st.markdown("特定の年に発生する大きな支出を入力します。")
        st.session_state.data["temporary_expenditures"]["education_lump_sum_year"] = st.number_input(
            "教育費一時支出の年 (シミュレーション開始から)",
            min_value=0, max_value=st.session_state.data["family"]["years_to_simulate"], value=st.session_state.data["temporary_expenditures"]["education_lump_sum_year"], step=1, key="edu_year_input"
        )
        st.session_state.data["temporary_expenditures"]["education_lump_sum_amount"] = st.number_input(
            "教育費一時支出額 (円)",
            min_value=0, value=st.session_state.data["temporary_expenditures"]["education_lump_sum_amount"], step=100000, key="edu_amount_input"
        )
        st.session_state.data["temporary_expenditures"]["housing_lump_sum_year"] = st.number_input(
            "住宅購入一時支出の年 (シミュレーション開始から)",
            min_value=0, max_value=st.session_state.data["family"]["years_to_simulate"], value=st.session_state.data["temporary_expenditures"]["housing_lump_sum_year"], step=1, key="housing_year_input"
        )
        st.session_state.data["temporary_expenditures"]["housing_lump_sum_amount"] = st.number_input(
            "住宅購入一時支出額 (円)",
            min_value=0, value=st.session_state.data["temporary_expenditures"]["housing_lump_sum_amount"], step=100000, key="housing_amount_input"
        )

        st.subheader("住宅ローン設定")
        st.session_state.data["housing_loan"]["loan_amount"] = st.number_input(
            "借入額 (円)",
            min_value=0, value=st.session_state.data["housing_loan"]["loan_amount"], step=1000000, key="loan_amount_input"
        )
        st.session_state.data["housing_loan"]["loan_interest_rate"] = st.number_input(
            "年間金利 (%)",
            min_value=0.0, max_value=10.0, value=st.session_state.data["housing_loan"]["loan_interest_rate"] * 100, step=0.01, format="%.2f", key="loan_interest_rate_input"
        ) / 100
        st.session_state.data["housing_loan"]["loan_term_years"] = st.number_input(
            "返済期間 (年)",
            min_value=0, max_value=50, value=st.session_state.data["housing_loan"]["loan_term_years"], step=1, key="loan_term_years_input"
        )
        monthly_loan_payment_display = calculate_monthly_loan_payment(
            st.session_state.data["housing_loan"]["loan_amount"],
            st.session_state.data["housing_loan"]["loan_interest_rate"],
            st.session_state.data["housing_loan"]["loan_term_years"]
        )
        st.info(f"**月々のローン返済額 (目安):** {int(monthly_loan_payment_display):,} 円")


    with col5:
        st.subheader("保険設定")
        st.session_state.data["insurance"]["life_insurance_monthly_premium"] = st.number_input(
            "生命保険 月額保険料 (円)",
            min_value=0, value=st.session_state.data["insurance"]["life_insurance_monthly_premium"], step=1000, key="life_ins_premium_input"
        )
        st.session_state.data["insurance"]["endowment_insurance_monthly_premium"] = st.number_input(
            "満期保険 月額保険料 (円)",
            min_value=0, value=st.session_state.data["insurance"]["endowment_insurance_monthly_premium"], step=1000, key="endow_ins_premium_input"
        )
        st.session_state.data["insurance"]["endowment_insurance_maturity_year"] = st.number_input(
            "満期保険の満期年 (シミュレーション開始から)",
            min_value=0, max_value=st.session_state.data["family"]["years_to_simulate"], value=st.session_state.data["insurance"]["endowment_insurance_maturity_year"], step=1, key="endow_ins_maturity_year_input"
        )
        st.session_state.data["insurance"]["endowment_insurance_payout_amount"] = st.number_input(
            "満期保険の受取額 (円)",
            min_value=0, value=st.session_state.data["insurance"]["endowment_insurance_payout_amount"], step=100000, key="endow_ins_payout_input"
        )


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
    df_to_download = flatten_data_for_csv(st.session_state.data)
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
                # シミュレーション結果と現在のデータをAI関数に渡す
                suggestion = asyncio.run(get_gemini_suggestion(user_plan_description, simulation_df, st.session_state.data))
                st.markdown(suggestion)
        else:
            st.warning("ライフプランの説明を入力してください。")


if __name__ == "__main__":
    main()
