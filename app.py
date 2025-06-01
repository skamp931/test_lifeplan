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
            "members": [ # 家族構成をリストで管理
                {"name": "A", "initial_age": 30},
                {"name": "B", "initial_age": 30}
            ],
            "years_to_simulate": 30,
            "initial_assets": 500, # 初期資産 (万円)
            "investment_return_rate": 0.03, # 年間投資利回り (3%)
            "inflation_rate": 0.01, # 年間インフレ率 (1%)
            "income_growth_rate": 0.01, # 10年ごとの収入上昇率 (1%)
            "income_growth_step_years": 10 # 収入上昇の発生ステップ年数
        },
        "income": {
            "monthly_salary_main": 30, # 主たる月収 (万円)
            "monthly_salary_sub": 0,      # 副業月収 (万円)
            "bonus_annual": 60        # 年間ボーナス (万円)
        },
        "expenditure": { # 月額支出 (千円)
            "housing": 100, # 10万円 = 100千円
            "food": 60,
            "transportation": 20,
            "education": 0,
            "utilities": 25,
            "communication": 10,
            "leisure": 30,
            "medical": 10,
            "other": 20
        },
        "school_lump_sums": { # 学校一時金 (万円)
            "kindergarten": {"amount": 50, "start_age": 3}, # 幼稚園入園時に発生する費用
            "elementary_school": {"amount": 100, "start_age": 6}, # 小学校入学時に発生する費用
            "junior_high_school": {"amount": 150, "start_age": 12}, # 中学校入学時に発生する費用
            "high_school": {"amount": 200, "start_age": 15}, # 高校入学時に発生する費用
            "university": {"amount": 300, "start_age": 18}, # 大学入学時に発生する費用
        },
        "insurance_policies": [ # 保険をリストで管理
            # {"name": "生命保険A", "monthly_premium": 10000, "maturity_year": 0, "payout_amount": 0}, # 満期年数0は満期なし
            # {"name": "学資保険B", "monthly_premium": 5000, "maturity_year": 18, "payout_amount": 200},
        ],
        "housing_loan": {
            "loan_amount": 0, # 借入額 (万円)
            "loan_interest_rate": 0.01, # 年間金利 (%)
            "loan_term_years": 35, # 返済期間 (年)
        }
    }

# --- 住宅ローン月額返済額計算 ---
def calculate_monthly_loan_payment(loan_amount_man, annual_interest_rate, loan_term_years):
    """
    住宅ローンの月額返済額を計算します。(万円単位の入力)
    PMT (Payment) 関数を使用します。
    """
    loan_amount_yen = loan_amount_man * 10000 # 万円を円に変換
    if loan_amount_yen <= 0 or loan_term_years <= 0:
        return 0

    monthly_interest_rate = annual_interest_rate / 12
    num_payments = loan_term_years * 12

    if monthly_interest_rate == 0:
        return loan_amount_yen / num_payments
    else:
        # PMT formula: P * [ i(1 + i)^n ] / [ (1 + i)^n – 1]
        # P = Principal (loan_amount_yen)
        # i = monthly interest rate
        # n = number of payments
        return loan_amount_yen * (monthly_interest_rate * (1 + monthly_interest_rate)**num_payments) / ((1 + monthly_interest_rate)**num_payments - 1)

# --- ライフプランシミュレーションロジック ---
def simulate_life_plan(data):
    """
    入力データに基づいてライフプランをシミュレーションします。
    年間収入、年間支出、住宅ローン額、学校一時金、年間収支、年末資産を計算します。
    """
    family = data["family"]
    income = data["income"]
    expenditure = data["expenditure"]
    school_lump_sums_config = data["school_lump_sums"]
    insurance_policies = data["insurance_policies"]
    housing_loan = data["housing_loan"]

    years_to_simulate = family["years_to_simulate"]
    initial_assets = family["initial_assets"] * 10000 # 万円を円に変換
    investment_return_rate = family["investment_return_rate"]
    inflation_rate = family["inflation_rate"]
    income_growth_rate = family["income_growth_rate"]
    income_growth_step_years = family["income_growth_step_years"]

    results = []
    current_assets = initial_assets

    # 現在の収入を追跡するための変数 (円単位)
    current_monthly_salary_main_yen = income["monthly_salary_main"] * 10000
    current_monthly_salary_sub_yen = income["monthly_salary_sub"] * 10000
    current_bonus_annual_yen = income["bonus_annual"] * 10000

    # 家族メンバーの現在の年齢を追跡
    current_member_ages = {member["name"]: member["initial_age"] for member in family["members"]}

    # 住宅ローンの月額返済額を事前に計算 (円)
    monthly_loan_payment_yen = calculate_monthly_loan_payment(
        housing_loan["loan_amount"],
        housing_loan["loan_interest_rate"],
        housing_loan["loan_term_years"]
    )

    for year in range(1, years_to_simulate + 1):
        # 収入の上昇率をステップ年数ごとに考慮
        if (year - 1) % income_growth_step_years == 0 and year > 1:
            current_monthly_salary_main_yen *= (1 + income_growth_rate)
            current_bonus_annual_yen *= (1 + income_growth_rate)

        # 年間収入の計算 (円)
        annual_income_yen = (current_monthly_salary_main_yen + current_monthly_salary_sub_yen) * 12 + current_bonus_annual_yen

        # 基本年間支出の計算 (千円を円に、インフレ考慮)
        base_annual_expenditure_yen = sum(expenditure.values()) * 1000 * 12 # 千円を円に
        inflated_base_annual_expenditure_yen = base_annual_expenditure_yen * ((1 + inflation_rate)**(year - 1))

        # 保険料の年間支出 (円)
        annual_insurance_premium_yen = sum(policy["monthly_premium"] for policy in insurance_policies) * 12

        # 住宅ローン返済額の年間支出 (円)
        annual_housing_loan_payment_yen = 0
        if year <= housing_loan["loan_term_years"]: # ローン返済期間中のみ
            annual_housing_loan_payment_yen = monthly_loan_payment_yen * 12

        # 学校一時金の年間支出 (円)
        annual_school_lump_sum_yen = 0
        for member_name, age in current_member_ages.items():
            current_age_in_year = age + (year - 1) # シミュレーション開始からの経過年数を加算
            for school_type, school_info in school_lump_sums_config.items():
                if school_info["start_age"] > 0 and current_age_in_year == school_info["start_age"]:
                    annual_school_lump_sum_yen += school_info["amount"] * 10000 # 万円を円に

        # 合計年間支出 (円)
        current_annual_expenditure_yen = inflated_base_annual_expenditure_yen + annual_insurance_premium_yen + annual_housing_loan_payment_yen + annual_school_lump_sum_yen

        # 年間収支 (円)
        annual_balance_yen = annual_income_yen - current_annual_expenditure_yen

        # 資産の変動 (投資利回り考慮)
        current_assets = current_assets * (1 + investment_return_rate) + annual_balance_yen

        # 満期保険の受取処理 (円)
        for policy in insurance_policies:
            if policy["maturity_year"] > 0 and year == policy["maturity_year"]:
                current_assets += policy["payout_amount"] * 10000 # 万円を円に

        results.append({
            "年": year,
            "年間収入": int(annual_income_yen),
            "年間支出": int(current_annual_expenditure_yen),
            "住宅ローン額": int(annual_housing_loan_payment_yen),
            "学校一時金": int(annual_school_lump_sum_yen),
            "年間収支": int(annual_balance_yen),
            "年末資産": int(current_assets)
        })

        # 家族メンバーの年齢を更新
        for name in current_member_ages:
            current_member_ages[name] += 1

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
    initial_assets = current_data["family"]["initial_assets"] * 10000 # 万円を円に
    years_to_simulate = current_data["family"]["years_to_simulate"]
    average_annual_savings = simulation_df['年間収支'].mean() # 年間収支を貯蓄として扱う
    average_annual_income = simulation_df['年間収入'].mean()
    average_annual_expenditure = simulation_df['年間支出'].mean()

    # AIへのプロンプトを構築
    prompt_text = f"""
    ユーザーのライフプランの説明: {user_plan_description}

    現在のシミュレーション結果の概要:
    - シミュレーション期間: {years_to_simulate} 年
    - 初期資産: {initial_assets:,} 円
    - 最終年末資産: {final_assets:,} 円
    - 年間平均収支（貯蓄）: {int(average_annual_savings):,} 円
    - 年間平均収入: {int(average_annual_income):,} 円
    - 年間平均支出: {int(average_annual_expenditure):,} 円

    上記シミュレーション結果とユーザーの説明に基づき、ライフプランの改善点を具体的に提案してください。
    特に、最終資産が目標に届かない場合や、貯蓄を増やしたい場合に焦点を当て、具体的な行動計画を含めてください。
    """

    # デモのためのダミー応答
    await asyncio.sleep(2) # API呼び出しの遅延をシミュレート

    suggestion_output = f"## ライフプラン改善提案 (Gemini AIによる)\n\n"
    suggestion_output += f"現在のシミュレーションでは、**{years_to_simulate}年後の年末資産は {final_assets:,} 円** と予測されています。\n"
    suggestion_output += f"年間平均収支は {int(average_annual_savings):,} 円です。\n\n"

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
            * 現在の年間平均収支 {int(average_annual_savings):,} 円を、例えば月5,000円（年間60,000円）増やすことを目標にしましょう。
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
    "family.years_to_simulate": int,
    "family.initial_assets": int, # 万円
    "family.investment_return_rate": float,
    "family.inflation_rate": float,
    "family.income_growth_rate": float,
    "family.income_growth_step_years": int,

    "income.monthly_salary_main": int, # 万円
    "income.monthly_salary_sub": int,  # 万円
    "income.bonus_annual": int,        # 万円

    "expenditure.housing": int, # 千円
    "expenditure.food": int,
    "expenditure.transportation": int,
    "expenditure.education": int,
    "expenditure.utilities": int,
    "expenditure.communication": int,
    "expenditure.leisure": int,
    "expenditure.medical": int,
    "expenditure.other": int,

    "school_lump_sums.kindergarten.amount": int, # 万円
    "school_lump_sums.kindergarten.start_age": int,
    "school_lump_sums.elementary_school.amount": int, # 万円
    "school_lump_sums.elementary_school.start_age": int,
    "school_lump_sums.junior_high_school.amount": int, # 万円
    "school_lump_sums.junior_high_school.start_age": int,
    "school_lump_sums.high_school.amount": int, # 万円
    "school_lump_sums.high_school.start_age": int,
    "school_lump_sums.university.amount": int, # 万円
    "school_lump_sums.university.start_age": int,

    "housing_loan.loan_amount": int, # 万円
    "housing_loan.loan_interest_rate": float,
    "housing_loan.loan_term_years": int,
}

# 動的なリスト（家族メンバー、保険）の項目はTYPE_MAPで直接定義できないため、
# unflatten_data_from_csv内で個別に処理するか、汎用的な型推論に頼る。
# 今回は、汎用的な型推論と、必要に応じてint/floatへの変換を試みる。


# --- データをフラット化してCSV用に変換するヘルパー関数 ---
def flatten_data_for_csv(data_dict, parent_key=''):
    flattened = []
    for key, value in data_dict.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            flattened.extend(flatten_data_for_csv(value, new_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flattened.extend(flatten_data_for_csv(item, f"{new_key}.{i}"))
                else: # リスト内に辞書以外の要素がある場合
                    flattened.append({"項目": f"{new_key}.{i}", "値": item})
        else:
            flattened.append({"項目": new_key, "値": value})
    return flattened

# --- CSVからデータを読み込み、ネストされた辞書に変換するヘルパー関数 ---
def unflatten_data_from_csv(df_uploaded, initial_data_structure):
    new_data = initial_data_structure.copy() # 初期構造をコピーして変更

    # リストの初期化
    new_data["family"]["members"] = []
    new_data["insurance_policies"] = []

    for index, row in df_uploaded.iterrows():
        item_path_str = row["項目"]
        value = row["値"]

        path_parts = item_path_str.split('.')
        current_level = new_data

        for i, key_part in enumerate(path_parts):
            if i == len(path_parts) - 1: # 最終要素
                # 型変換を試みる
                target_type = TYPE_MAP.get(item_path_str)
                if target_type:
                    try:
                        if pd.isna(value):
                            value = 0 if target_type == int else 0.0
                        else:
                            value = target_type(value)
                    except (ValueError, TypeError):
                        st.warning(f"Warning: Could not convert '{value}' for '{item_path_str}' to {target_type.__name__}. Using default value (0 or 0.0).")
                        value = 0 if target_type == int else 0.0
                else: # TYPE_MAPにない項目 (例: 家族名など文字列、または動的なリストの要素)
                    if pd.isna(value):
                        value = "" # 文字列の場合は空文字列
                    # それ以外はそのままの値を使用

                # 値を設定
                if key_part.isdigit() and isinstance(current_level, list): # リストのインデックスの場合
                    idx = int(key_part)
                    while len(current_level) <= idx: # リストのサイズを調整
                        if path_parts[i-1] == "members":
                            current_level.append({"name": "", "initial_age": 0}) # 家族メンバーのデフォルト構造
                        elif path_parts[i-1] == "insurance_policies":
                            current_level.append({"name": "", "monthly_premium": 0, "maturity_year": 0, "payout_amount": 0}) # 保険のデフォルト構造
                        else:
                            current_level.append({}) # その他の辞書リスト
                    current_level[idx][path_parts[i+1]] = value if i+1 < len(path_parts) else value # ここは少し複雑になる
                    # 動的なリスト内の要素は、key_partが数字で、次の要素が実際のキーになるため、
                    # 最終要素の処理を少し調整する必要がある。
                    # 以下のロジックは、リスト内の辞書を想定している。
                    if i + 1 == len(path_parts): # 最後のキーが数字の場合（例: list.0）
                        current_level[idx] = value
                    else: # リスト内の辞書の場合（例: list.0.key）
                        if path_parts[i-1] == "members":
                            current_level[idx][key_part] = value # name, initial_age
                        elif path_parts[i-1] == "insurance_policies":
                            current_level[idx][key_part] = value # name, monthly_premium, etc.
                        else:
                            current_level[idx][key_part] = value # fallback
                else:
                    current_level[key_part] = value

            else: # 中間要素
                if key_part.isdigit(): # リストのインデックス
                    idx = int(key_part)
                    # 親がリストであることを確認
                    if not isinstance(current_level, list):
                        # これはエラーケースか、またはCSV構造が期待と異なる
                        # ここでは、リストとして初期化する
                        # st.error(f"Error: Expected list at {'.'.join(path_parts[:i])}, but found {type(current_level)}")
                        current_level[path_parts[i-1]] = [] # これは間違ったパスになる可能性あり
                        # より安全なのは、path_partsを再構築して、正しくリストにアクセスすること
                        # この複雑さを避けるため、動的なリストの処理は別途考慮する
                        pass # このケースは現在のflatten/unflattenでは発生しないはず

                    while len(current_level) <= idx:
                        if path_parts[i-1] == "members":
                            current_level.append({"name": "", "initial_age": 0})
                        elif path_parts[i-1] == "insurance_policies":
                            current_level.append({"name": "", "monthly_premium": 0, "maturity_year": 0, "payout_amount": 0})
                        else:
                            current_level.append({}) # 未知のリスト内の辞書
                    current_level = current_level[idx]
                else: # 辞書のキー
                    if key_part not in current_level or not isinstance(current_level[key_part], (dict, list)):
                        # 次の要素が数字ならリスト、そうでなければ辞書
                        if i + 1 < len(path_parts) and path_parts[i+1].isdigit():
                            current_level[key_part] = []
                        else:
                            current_level[key_part] = {}
                    current_level = current_level[key_part]
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
            # アップロードされたデータをセッションステートに反映
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
        # 家族メンバーの動的な追加・削除
        if "members_count" not in st.session_state:
            st.session_state.members_count = len(st.session_state.data["family"]["members"])

        for i in range(st.session_state.members_count):
            st.markdown(f"**メンバー {i+1}**")
            member_name = st.text_input(f"名前", value=st.session_state.data["family"]["members"][i]["name"], key=f"member_name_{i}")
            member_age = st.number_input(f"初期年齢", min_value=0, max_value=100, value=st.session_state.data["family"]["members"][i]["initial_age"], step=1, key=f"member_age_{i}")
            st.session_state.data["family"]["members"][i]["name"] = member_name
            st.session_state.data["family"]["members"][i]["initial_age"] = member_age

        if st.button("メンバーを追加", key="add_member_btn"):
            st.session_state.data["family"]["members"].append({"name": f"New Member {st.session_state.members_count + 1}", "initial_age": 0})
            st.session_state.members_count += 1
            st.experimental_rerun() # メンバー追加後にUIを更新

        if st.session_state.members_count > 0 and st.button("最後のメンバーを削除", key="remove_member_btn"):
            st.session_state.data["family"]["members"].pop()
            st.session_state.members_count -= 1
            st.experimental_rerun() # メンバー削除後にUIを更新

        st.session_state.data["family"]["years_to_simulate"] = st.number_input(
            "シミュレーション年数 (年)",
            min_value=5, max_value=60, value=st.session_state.data["family"]["years_to_simulate"], step=5, key="years_input"
        )
        st.session_state.data["family"]["initial_assets"] = st.number_input(
            "初期資産 (万円)",
            min_value=0, value=st.session_state.data["family"]["initial_assets"], step=100, key="initial_assets_input"
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
            "収入上昇率 (%)",
            min_value=0.0, max_value=10.0, value=st.session_state.data["family"]["income_growth_rate"] * 100, step=0.1, format="%.1f", key="income_growth_rate_input"
        ) / 100
        st.session_state.data["family"]["income_growth_step_years"] = st.number_input(
            "上昇率の発生するステップ年数 (年)",
            min_value=1, max_value=30, value=st.session_state.data["family"]["income_growth_step_years"], step=1, key="income_growth_step_years_input"
        )

    with col2:
        st.subheader("収入")
        st.session_state.data["income"]["monthly_salary_main"] = st.number_input(
            "主たる月収 (万円)",
            min_value=0, value=st.session_state.data["income"]["monthly_salary_main"], step=10, key="salary_main_input"
        )
        st.session_state.data["income"]["monthly_salary_sub"] = st.number_input(
            "副業月収 (万円)",
            min_value=0, value=st.session_state.data["income"]["monthly_salary_sub"], step=5, key="salary_sub_input"
        )
        st.session_state.data["income"]["bonus_annual"] = st.number_input(
            "年間賞与 (万円)",
            min_value=0, value=st.session_state.data["income"]["bonus_annual"], step=10, key="bonus_annual_input"
        )

        st.subheader("学校一時金 (万円)")
        st.markdown("各学校の入学時に発生する平均的な費用です。")
        for school_type, school_info in st.session_state.data["school_lump_sums"].items():
            st.session_state.data["school_lump_sums"][school_type]["amount"] = st.number_input(
                f"{school_type.replace('_', ' ').title()} 費用",
                min_value=0, value=school_info["amount"], step=10, key=f"school_{school_type}_amount"
            )
            st.session_state.data["school_lump_sums"][school_type]["start_age"] = st.number_input(
                f"{school_type.replace('_', ' ').title()} 開始年齢",
                min_value=0, max_value=30, value=school_info["start_age"], step=1, key=f"school_{school_type}_age"
            )


    with col3:
        st.subheader("支出 (月額/千円)")
        st.session_state.data["expenditure"]["housing"] = st.number_input("住居費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["housing"], step=5, key="housing_input")
        st.session_state.data["expenditure"]["food"] = st.number_input("食費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["food"], step=1, key="food_input")
        st.session_state.data["expenditure"]["transportation"] = st.number_input("交通費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["transportation"], step=1, key="transportation_input")
        st.session_state.data["expenditure"]["education"] = st.number_input("教育費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["education"], step=1, key="education_input")
        st.session_state.data["expenditure"]["utilities"] = st.number_input("光熱費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["utilities"], step=1, key="utilities_input")
        st.session_state.data["expenditure"]["communication"] = st.number_input("通信費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["communication"], step=1, key="communication_input")
        st.session_state.data["expenditure"]["leisure"] = st.number_input("娯楽費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["leisure"], step=1, key="leisure_input")
        st.session_state.data["expenditure"]["medical"] = st.number_input("医療費 (千円)", min_value=0, value=st.session_state.data["expenditure"]["medical"], step=1, key="medical_input")
        st.session_state.data["expenditure"]["other"] = st.number_input("その他 (千円)", min_value=0, value=st.session_state.data["expenditure"]["other"], step=1, key="other_input")

    with col4:
        st.subheader("住宅ローン設定")
        st.session_state.data["housing_loan"]["loan_amount"] = st.number_input(
            "借入額 (万円)",
            min_value=0, value=st.session_state.data["housing_loan"]["loan_amount"], step=100, key="loan_amount_input"
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
        # 保険の動的な追加・削除
        if "insurance_count" not in st.session_state:
            st.session_state.insurance_count = len(st.session_state.data["insurance_policies"])

        for i in range(st.session_state.insurance_count):
            st.markdown(f"**保険 {i+1}**")
            policy = st.session_state.data["insurance_policies"][i]
            policy["name"] = st.text_input(f"保険名", value=policy["name"], key=f"ins_name_{i}")
            policy["monthly_premium"] = st.number_input(f"月額保険料 (円)", min_value=0, value=policy["monthly_premium"], step=1000, key=f"ins_premium_{i}")
            policy["maturity_year"] = st.number_input(f"満期年数 (シミュレーション開始から)", min_value=0, max_value=st.session_state.data["family"]["years_to_simulate"], value=policy["maturity_year"], step=1, key=f"ins_maturity_year_{i}")
            policy["payout_amount"] = st.number_input(f"満期時の受取額 (万円)", min_value=0, value=policy["payout_amount"], step=10, key=f"ins_payout_{i}")

        if st.button("保険を追加", key="add_insurance_btn"):
            st.session_state.data["insurance_policies"].append({"name": f"新規保険 {st.session_state.insurance_count + 1}", "monthly_premium": 0, "maturity_year": 0, "payout_amount": 0})
            st.session_state.insurance_count += 1
            st.experimental_rerun() # 保険追加後にUIを更新

        if st.session_state.insurance_count > 0 and st.button("最後の保険を削除", key="remove_insurance_btn"):
            st.session_state.data["insurance_policies"].pop()
            st.session_state.insurance_count -= 1
            st.experimental_rerun() # 保険削除後にUIを更新


    # --- シミュレーション実行ボタン ---
    st.markdown("---")
    if st.button("シミュレーションを実行", type="primary"):
        st.session_state.run_simulation = True
    else:
        # 初期状態またはボタンが押されていない場合はシミュレーション結果をクリア
        if "simulation_df" not in st.session_state:
            st.session_state.simulation_df = pd.DataFrame()
        st.session_state.run_simulation = False


    # --- シミュレーション結果 ---
    st.header("3. シミュレーション結果")
    st.markdown("設定したライフプランに基づいた将来の資産推移です。")

    if st.session_state.run_simulation:
        simulation_df = simulate_life_plan(st.session_state.data)
        st.session_state.simulation_df = simulation_df # 結果をセッションステートに保存

        st.dataframe(simulation_df.style.format({
            "年間収入": "{:,}円",
            "年間支出": "{:,}円",
            "住宅ローン額": "{:,}円",
            "学校一時金": "{:,}円",
            "年間収支": "{:,}円",
            "年末資産": "{:,}円"
        }), use_container_width=True)

        st.line_chart(simulation_df.set_index("年")["年末資産"])

        # マイナスになる年数と最大マイナス額の表示
        negative_assets_df = simulation_df[simulation_df['年末資産'] < 0]
        if not negative_assets_df.empty:
            first_negative_year = negative_assets_df['年'].iloc[0]
            max_negative_amount = negative_assets_df['年末資産'].min()
            st.error(f"**資産がマイナスになる年数:** {first_negative_year}年目")
            st.error(f"**最大マイナス額:** {max_negative_amount:,}円")
        else:
            st.success("**シミュレーション期間中、資産がマイナスになることはありませんでした。**")
            st.markdown(f"**最終的な年末資産:** {simulation_df['年末資産'].iloc[-1]:,}円")

    else:
        st.info("「シミュレーションを実行」ボタンを押して結果を表示してください。")


    # ダウンロードボタン
    # 現在のデータをCSV形式に変換
    df_to_download = pd.DataFrame(flatten_data_for_csv(st.session_state.data))
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
    st.info("AIによる改善提案は、現在**定型文**であることを記載しています。") # 定型文であることを記載

    user_plan_description = st.text_area(
        "あなたのライフプランについて、目標や課題、現在の状況などを具体的に教えてください。",
        value="現在の収入と支出で、20年後に老後資金として5,000万円を貯蓄したいと考えています。何か改善できる点はありますか？",
        height=150
    )

    if st.button("AIに改善点を尋ねる"):
        if user_plan_description and "simulation_df" in st.session_state and not st.session_state.simulation_df.empty:
            with st.spinner("AIが改善点を考えています..."):
                # シミュレーション結果と現在のデータをAI関数に渡す
                suggestion = asyncio.run(get_gemini_suggestion(user_plan_description, st.session_state.simulation_df, st.session_state.data))
                st.markdown(suggestion)
        else:
            st.warning("ライフプランの説明を入力し、「シミュレーションを実行」してからAIに尋ねてください。")


if __name__ == "__main__":
    main()
