import io

import streamlit as st
import pandas as pd
from supabase import create_client


# =========================================================
# ページ設定
# =========================================================

st.set_page_config(
    page_title="成功確率表",
    page_icon="📊",
    layout="wide"
)

st.title("成功確率表")


# =========================================================
# 定数
# =========================================================

ITEM_COL = "回数"
TYPE_COL = "種類"
MEMO = "メモ"


# =========================================================
# Supabase接続
# =========================================================

@st.cache_resource
def get_supabase():

    if "SUPABASE_URL" not in st.secrets:

        st.error(
            "SUPABASE_URL が設定されていません。\n\n"
            "Streamlit Cloudの Settings → Secrets に "
            "SUPABASE_URL と SUPABASE_KEY を設定してください。"
        )

        st.stop()

    if "SUPABASE_KEY" not in st.secrets:

        st.error(
            "SUPABASE_KEY が設定されていません。\n\n"
            "Streamlit Cloudの Settings → Secrets に "
            "SUPABASE_KEY を設定してください。"
        )

        st.stop()

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = get_supabase()


# =========================================================
# 初期データ作成
# =========================================================

def create_initial_data(
    trial_count=10,
    item_count=10
):

    trial_columns = [
        str(i)
        for i in range(
            1,
            trial_count + 1
        )
    ]

    columns = (
        [ITEM_COL, TYPE_COL]
        + trial_columns
    )

    rows = []

    for i in range(item_count):

        # ---------------------------------------------
        # 判定行
        # ---------------------------------------------

        choice_row = {
            ITEM_COL: f"{i + 1}回目",
            TYPE_COL: "判定"
        }

        # ---------------------------------------------
        # メモ行
        # ---------------------------------------------

        memo_row = {
            ITEM_COL: MEMO,
            TYPE_COL: MEMO
        }

        for col in trial_columns:

            choice_row[col] = ""
            memo_row[col] = ""

        rows.append(choice_row)
        rows.append(memo_row)

    return pd.DataFrame(
        rows,
        columns=columns
    )


# =========================================================
# 試行列取得
# =========================================================

def get_trial_columns(df):

    return sorted(
        [
            str(column)
            for column in df.columns
            if str(column).isdigit()
        ],
        key=lambda x: int(x)
    )


# =========================================================
# データ整理
# =========================================================

def normalize_data(df):

    df = df.copy()

    # 不要な列を削除
    df = df.drop(
        columns=[
            "index",
            "_index"
        ],
        errors="ignore"
    )

    # 必須列
    if ITEM_COL not in df.columns:

        df[ITEM_COL] = ""

    if TYPE_COL not in df.columns:

        df[TYPE_COL] = ""

    # 試行列
    trial_columns = get_trial_columns(df)

    if not trial_columns:

        df["1"] = ""

    trial_columns = get_trial_columns(df)

    # 試行データを文字列化
    for col in trial_columns:

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
        )

    # ---------------------------------------------
    # 判定行 / メモ行
    # ---------------------------------------------

    for row in range(len(df)):

        if row % 2 == 0:

            # 判定行
            df.at[
                row,
                TYPE_COL
            ] = "判定"

            current = str(
                df.at[
                    row,
                    ITEM_COL
                ]
            )

            if (
                current.strip() == ""
                or current == "nan"
                or current == MEMO
            ):

                df.at[
                    row,
                    ITEM_COL
                ] = (
                    f"{row // 2 + 1}回目"
                )

        else:

            # メモ行
            df.at[
                row,
                TYPE_COL
            ] = MEMO

            df.at[
                row,
                ITEM_COL
            ] = MEMO

    # ---------------------------------------------
    # 列順
    # ---------------------------------------------

    trial_columns = get_trial_columns(df)

    columns = (
        [ITEM_COL, TYPE_COL]
        + trial_columns
    )

    for col in columns:

        if col not in df.columns:

            df[col] = ""

    return df[
        columns
    ]


# =========================================================
# Supabaseから読み込み
# 型判定を強化した修正版
# =========================================================

def load_data():

    try:

        result = (
            supabase
            .table("app_data")
            .select("data")
            .eq("id", 1)
            .execute()
        )

        # ---------------------------------------------
        # データが存在しない
        # ---------------------------------------------

        if not result.data:

            return create_initial_data()

        # ---------------------------------------------
        # data取得
        # ---------------------------------------------

        saved_data = (
            result.data[0].get("data")
        )

        # ---------------------------------------------
        # None / 空
        # ---------------------------------------------

        if not saved_data:

            return create_initial_data()

        # ---------------------------------------------
        # 1. 辞書型
        # ---------------------------------------------

        if isinstance(
            saved_data,
            dict
        ):

            # 初期状態
            if saved_data.get(
                "initialized"
            ) is True:

                return create_initial_data()

            # 辞書1件
            df = pd.DataFrame(
                [saved_data]
            )

        # ---------------------------------------------
        # 2. リスト型
        # ---------------------------------------------

        elif isinstance(
            saved_data,
            list
        ):

            if len(saved_data) == 0:

                return create_initial_data()

            df = pd.DataFrame(
                saved_data
            )

        # ---------------------------------------------
        # 3. その他
        # ---------------------------------------------

        else:

            return create_initial_data()

        return normalize_data(df)

    except Exception as e:

        st.error(
            f"Supabaseからの読み込みに失敗しました。\n\n{e}"
        )

        return create_initial_data()


# =========================================================
# Supabaseへ保存
# =========================================================

def save_data(df):

    try:

        df = normalize_data(
            df
        )

        data = df.to_dict(
            orient="records"
        )

        (
            supabase
            .table("app_data")
            .upsert(
                {
                    "id": 1,
                    "data": data
                }
            )
            .execute()
        )

        return True

    except Exception as e:

        st.error(
            f"Supabaseへの保存に失敗しました。\n\n{e}"
        )

        return False


# =========================================================
# 起動時だけSupabaseから読み込み
# =========================================================

if (
    "loaded_from_supabase"
    not in st.session_state
    or
    "df"
    not in st.session_state
):

    st.session_state.df = load_data()

    st.session_state.loaded_from_supabase = True


# =========================================================
# 取得したデータを正規化
# =========================================================

st.session_state.df = normalize_data(
    st.session_state.df
)


# =========================================================
# サイドバー
# =========================================================

st.sidebar.header(
    "操作"
)


# =========================================================
# 項目の追加
# =========================================================

if st.sidebar.button(
    "➕ 項目の追加"
):

    df = (
        st.session_state.df
        .copy()
    )

    trial_columns = (
        get_trial_columns(
            df
        )
    )

    item_number = (
        len(df) // 2 + 1
    )

    choice = {

        ITEM_COL:
            f"{item_number}回目",

        TYPE_COL:
            "判定"
    }

    memo = {

        ITEM_COL:
            MEMO,

        TYPE_COL:
            MEMO
    }

    for col in trial_columns:

        choice[col] = ""
        memo[col] = ""

    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    choice,
                    memo
                ]
            )
        ],
        ignore_index=True
    )

    df = normalize_data(
        df
    )

    st.session_state.df = df

    save_data(df)

    st.rerun()


# =========================================================
# 項目の削除
# =========================================================

if st.sidebar.button(
    "➖ 項目の削除"
):

    df = (
        st.session_state.df
        .copy()
    )

    if len(df) <= 2:

        st.sidebar.warning(
            "これ以上項目を削除できません。"
        )

    else:

        # 最後の項目を削除
        df = (
            df.iloc[:-2]
            .reset_index(
                drop=True
            )
        )

        df = normalize_data(
            df
        )

        st.session_state.df = df

        save_data(df)

        st.rerun()


# =========================================================
# 回数の追加
# =========================================================

if st.sidebar.button(
    "➕ 回数の追加"
):

    df = (
        st.session_state.df
        .copy()
    )

    trial_columns = (
        get_trial_columns(
            df
        )
    )

    if trial_columns:

        new_column = str(
            max(
                int(c)
                for c in trial_columns
            ) + 1
        )

    else:

        new_column = "1"

    df[new_column] = ""

    df = normalize_data(
        df
    )

    st.session_state.df = df

    save_data(df)

    st.rerun()


# =========================================================
# 回数の削除
# =========================================================

if st.sidebar.button(
    "➖ 回数の削除"
):

    df = (
        st.session_state.df
        .copy()
    )

    trial_columns = (
        get_trial_columns(
            df
        )
    )

    if len(trial_columns) <= 1:

        st.sidebar.warning(
            "これ以上回数を削除できません。"
        )

    else:

        last_column = trial_columns[-1]

        df = df.drop(
            columns=[
                last_column
            ]
        )

        df = normalize_data(
            df
        )

        st.session_state.df = df

        save_data(df)

        st.rerun()


# =========================================================
# 新規作成
# =========================================================

if st.sidebar.button(
    "🔄 新規作成"
):

    new_df = create_initial_data()

    st.session_state.df = new_df

    save_data(new_df)

    st.rerun()


# =========================================================
# 手動保存
# =========================================================

if st.sidebar.button(
    "💾 データを保存"
):

    if save_data(
        st.session_state.df
    ):

        st.sidebar.success(
            "保存しました。"
        )


# =========================================================
# 入力エリア
# =========================================================

df = (
    st.session_state.df
    .copy()
)

trial_columns = (
    get_trial_columns(
        df
    )
)


st.subheader(
    "🪢 入力エリア"
)


# =========================================================
# ヘッダー
# =========================================================

header_columns = st.columns(
    [2] + [1] * len(
        trial_columns
    )
)


with header_columns[0]:

    st.markdown(
        "**回数**"
    )


for i, col in enumerate(
    trial_columns,
    start=1
):

    with header_columns[i]:

        st.markdown(
            f"**{col}**"
        )


# =========================================================
# 入力
# =========================================================

new_df = df.copy()


for item_index in range(
    0,
    len(df),
    2
):

    # =====================================================
    # 判定行
    # =====================================================

    choice_columns = st.columns(
        [2] + [1] * len(
            trial_columns
        )
    )


    # -----------------------------------------------------
    # 回数
    # -----------------------------------------------------

    with choice_columns[0]:

        item_name = st.text_input(

            "回数",

            value=str(
                df.at[
                    item_index,
                    ITEM_COL
                ]
            ),

            key=(
                f"item_"
                f"{item_index}"
            ),

            label_visibility="collapsed"
        )

        new_df.at[
            item_index,
            ITEM_COL
        ] = item_name


    # -----------------------------------------------------
    # ○ / ×
    # -----------------------------------------------------

    for i, col in enumerate(
        trial_columns,
        start=1
    ):

        with choice_columns[i]:

            current_value = str(
                df.at[
                    item_index,
                    col
                ]
            )

            options = [
                "",
                "○",
                "×"
            ]

            if current_value not in options:

                current_value = ""

            selected = st.selectbox(

                f"判定_{item_index}_{col}",

                options=options,

                index=options.index(
                    current_value
                ),

                key=(
                    f"choice_"
                    f"{item_index}_"
                    f"{col}"
                ),

                label_visibility="collapsed"
            )

            new_df.at[
                item_index,
                col
            ] = selected


    # =====================================================
    # メモ行
    # =====================================================

    memo_columns = st.columns(
        [2] + [1] * len(
            trial_columns
        )
    )


    with memo_columns[0]:

        st.markdown(
            "📝 **メモ**"
        )


    new_df.at[
        item_index + 1,
        ITEM_COL
    ] = MEMO


    # -----------------------------------------------------
    # メモ自由入力
    # -----------------------------------------------------

    for i, col in enumerate(
        trial_columns,
        start=1
    ):

        with memo_columns[i]:

            memo_value = st.text_input(

                f"メモ_{item_index}_{col}",

                value=str(
                    df.at[
                        item_index + 1,
                        col
                    ]
                ),

                key=(
                    f"memo_"
                    f"{item_index}_"
                    f"{col}"
                ),

                label_visibility="collapsed"
            )

            new_df.at[
                item_index + 1,
                col
            ] = memo_value


    st.divider()


# =========================================================
# 編集結果確定
# =========================================================

new_df = normalize_data(
    new_df
)

st.session_state.df = new_df


# =========================================================
# 自動保存
# =========================================================

save_data(
    new_df
)


# =========================================================
# 集計
# =========================================================

trial_columns = (
    get_trial_columns(
        new_df
    )
)


# =========================================================
# 項目ごとの集計
# =========================================================

summary_rows = []


for row in range(
    0,
    len(new_df),
    2
):

    item_name = (
        new_df.at[
            row,
            ITEM_COL
        ]
    )


    # -----------------------------------------------------
    # ○の数
    # -----------------------------------------------------

    o_count = 0


    # -----------------------------------------------------
    # ×の数
    # -----------------------------------------------------

    x_count = 0


    # -----------------------------------------------------
    # 入力済みの回数
    #
    # 空欄は数えない
    # ○と×だけを数える
    # -----------------------------------------------------

    input_count = 0


    for col in trial_columns:

        value = (
            new_df.at[
                row,
                col
            ]
        )


        if value == "○":

            o_count += 1

            input_count += 1


        elif value == "×":

            x_count += 1

            input_count += 1


    # -----------------------------------------------------
    # 成功確率
    # -----------------------------------------------------

    if input_count > 0:

        success_rate = (
            o_count /
            input_count
        ) * 100

    else:

        success_rate = 0.0


    summary_rows.append(
        {
            "回数":
                item_name,

            "○の数":
                o_count,

            "×の数":
                x_count,

            "入力済み回数":
                input_count,

            "成功確率":
                success_rate
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# =========================================================
# 全体の回数
# =========================================================

if trial_columns:

    total_trial_count = max(
        int(c)
        for c in trial_columns
    )

else:

    total_trial_count = 0


# =========================================================
# 集計結果
# =========================================================

st.subheader(
    "📈 集計結果"
)


st.dataframe(

    summary_df.style.format(
        {
            "成功確率":
                "{:.1f}%"
        }
    ),

    use_container_width=True,

    hide_index=True
)


# =========================================================
# 入力結果
# =========================================================

st.subheader(
    "🎨 入力結果"
)


result_df = new_df.copy()


# 成功確率列
result_df["成功確率"] = ""


for index in range(
    0,
    len(result_df),
    2
):

    # ○
    o_count = 0

    # ×
    x_count = 0

    # 実際に入力された数
    input_count = 0


    for col in trial_columns:

        value = (
            result_df.at[
                index,
                col
            ]
        )


        if value == "○":

            o_count += 1

            input_count += 1


        elif value == "×":

            x_count += 1

            input_count += 1


    # 成功確率
    if input_count > 0:

        rate = (
            o_count /
            input_count
        ) * 100

    else:

        rate = 0.0


    result_df.at[
        index,
        "成功確率"
    ] = (
        f"{rate:.1f}%"
    )


# 種類列を削除
result_df = result_df.drop(
    columns=[
        TYPE_COL
    ]
)


# =========================================================
# ○ = 赤 / × = 青
# =========================================================

def color_value(
    value
):

    if value == "○":

        return (
            "color: red;"
            "font-weight: bold;"
            "text-align: center;"
        )

    if value == "×":

        return (
            "color: blue;"
            "font-weight: bold;"
            "text-align: center;"
        )

    return ""


result_style = (
    result_df
    .style
    .map(
        color_value,
        subset=trial_columns
    )
)


st.dataframe(
    result_style,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# Excel保存
# =========================================================

st.subheader(
    "📥 ファイルとして保存"
)


try:

    excel_buffer = io.BytesIO()


    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:


        result_df.to_excel(

            writer,

            index=False,

            sheet_name="成功確率表"
        )


        summary_df.to_excel(

            writer,

            index=False,

            sheet_name="集計結果"
        )


    excel_buffer.seek(0)


    st.download_button(

        label="📊 Excelとして保存",

        data=(
            excel_buffer.getvalue()
        ),

        file_name=(
            "成功確率表.xlsx"
        ),

        mime=(
            "application/"
            "vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),

        key="excel_download"
    )


except Exception as e:

    st.error(
        f"Excel保存エラー: {e}"
    )


# =========================================================
# CSV保存
# =========================================================

try:

    csv_data = (

        result_df

        .to_csv(

            index=False,

            encoding="utf-8-sig"
        )
    )


    st.download_button(

        label="📥 CSVとして保存",

        data=csv_data,

        file_name=(
            "成功確率表.csv"
        ),

        mime="text/csv",

        key="csv_download"
    )


except Exception as e:

    st.error(
        f"CSV保存エラー: {e}"
    )


# =========================================================
# 状態
# =========================================================

st.sidebar.divider()


st.sidebar.success(
    "データは自動保存されています"
)


st.sidebar.caption(
    "ブラウザを閉じたりリロードしてもデータは残ります。"
)
