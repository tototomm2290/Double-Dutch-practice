import io
import streamlit as st
import pandas as pd


# =========================================================
# ページ設定
# =========================================================

st.set_page_config(
    page_title="○×試行管理表",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ○×試行管理表")


# =========================================================
# 定数
# =========================================================

ITEM_COL = "項目名"
TYPE_COL = "種類"
MEMO = "メモ"


# =========================================================
# 初期データ
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

        # 判定行
        choice_row = {
            ITEM_COL: f"項目{i + 1}",
            TYPE_COL: "判定"
        }

        # メモ行
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
# セッション状態
# =========================================================

if "df" not in st.session_state:

    st.session_state.df = (
        create_initial_data()
    )


# =========================================================
# 試行列を取得
# =========================================================

def get_trial_columns(df):

    result = []

    for column in df.columns:

        if str(column).isdigit():

            result.append(str(column))

    return sorted(
        result,
        key=lambda x: int(x)
    )


# =========================================================
# データ整理
# =========================================================

def normalize_data(df):

    df = df.copy()

    # 不要列削除
    df = df.drop(
        columns=[
            "index",
            "_index"
        ],
        errors="ignore"
    )

    # 項目名
    if ITEM_COL not in df.columns:

        df.insert(
            0,
            ITEM_COL,
            ""
        )

    # 種類
    if TYPE_COL not in df.columns:

        df.insert(
            1,
            TYPE_COL,
            ""
        )

    # 試行列
    trial_columns = (
        get_trial_columns(df)
    )

    if not trial_columns:

        df["1"] = ""

    trial_columns = (
        get_trial_columns(df)
    )

    # ○×以外を空欄にする
    for col in trial_columns:

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
        )

        df[col] = df[col].apply(
            lambda value:
            value
            if value in [
                "",
                "○",
                "×"
            ]
            else ""
        )

    # 判定 / メモ
    for row in range(len(df)):

        if row % 2 == 0:

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
            ):

                df.at[
                    row,
                    ITEM_COL
                ] = (
                    f"項目{row // 2 + 1}"
                )

        else:

            df.at[
                row,
                TYPE_COL
            ] = MEMO

            df.at[
                row,
                ITEM_COL
            ] = MEMO

    # 列順
    trial_columns = (
        get_trial_columns(df)
    )

    columns = (
        [ITEM_COL, TYPE_COL]
        + trial_columns
    )

    return df[columns]


# =========================================================
# 最後の列を使用したら自動追加
# =========================================================

def auto_add_trial_column(df):

    df = df.copy()

    trial_columns = (
        get_trial_columns(df)
    )

    if not trial_columns:

        df["1"] = ""

        return df

    last_column = trial_columns[-1]

    # 最後の列に入力があるか
    used = (
        df[last_column]
        .astype(str)
        .str.strip()
        .ne("")
        .any()
    )

    if used:

        new_column = str(
            int(last_column) + 1
        )

        df[new_column] = ""

    return df


# =========================================================
# 最後の項目を使用したら自動追加
# =========================================================

def auto_add_item(df):

    df = df.copy()

    if len(df) < 2:

        return df

    last_choice_row = (
        len(df) - 2
    )

    trial_columns = (
        get_trial_columns(df)
    )

    used = False

    # -----------------------------
    # 項目名
    # -----------------------------

    item_name = str(
        df.at[
            last_choice_row,
            ITEM_COL
        ]
    )

    default_name = (
        f"項目{last_choice_row // 2 + 1}"
    )

    if (
        item_name.strip() != ""
        and item_name != default_name
    ):

        used = True

    # -----------------------------
    # ○ / ×
    # -----------------------------

    if not used:

        for col in trial_columns:

            value = str(
                df.at[
                    last_choice_row,
                    col
                ]
            )

            if value.strip() != "":

                used = True
                break

    # -----------------------------
    # メモ
    # -----------------------------

    if not used:

        for col in trial_columns:

            value = str(
                df.at[
                    last_choice_row + 1,
                    col
                ]
            )

            if value.strip() != "":

                used = True
                break

    # -----------------------------
    # 行追加
    # -----------------------------

    if used:

        item_number = (
            len(df) // 2 + 1
        )

        choice = {
            ITEM_COL:
                f"項目{item_number}",

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

    return df


# =========================================================
# 初期データ整理
# =========================================================

st.session_state.df = (
    normalize_data(
        st.session_state.df
    )
)


# =========================================================
# サイドバー
# =========================================================

st.sidebar.header("操作")


# =========================================================
# 行追加
# =========================================================

if st.sidebar.button(
    "➕ 行を追加"
):

    df = st.session_state.df.copy()

    trial_columns = (
        get_trial_columns(df)
    )

    item_number = (
        len(df) // 2 + 1
    )

    choice = {
        ITEM_COL:
            f"項目{item_number}",

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

    st.session_state.df = (
        normalize_data(df)
    )

    st.rerun()


# =========================================================
# 列追加
# =========================================================

if st.sidebar.button(
    "➕ 試行列を追加"
):

    df = st.session_state.df.copy()

    trial_columns = (
        get_trial_columns(df)
    )

    if trial_columns:

        new_column = str(
            max(
                int(col)
                for col in trial_columns
            ) + 1
        )

    else:

        new_column = "1"

    df[new_column] = ""

    st.session_state.df = (
        normalize_data(df)
    )

    st.rerun()


# =========================================================
# 新規作成
# =========================================================

if st.sidebar.button(
    "🔄 新規作成"
):

    st.session_state.df = (
        create_initial_data()
    )

    st.rerun()


# =========================================================
# Excel読み込み
# =========================================================

st.sidebar.subheader(
    "📂 Excel読み込み"
)

uploaded_file = st.sidebar.file_uploader(
    "Excelファイルを選択",
    type=["xlsx"]
)


if uploaded_file is not None:

    if st.sidebar.button(
        "Excelを読み込む"
    ):

        try:

            excel_df = pd.read_excel(
                uploaded_file,
                sheet_name=0
            )

            trial_columns = [
                str(column)
                for column in excel_df.columns
                if str(column).isdigit()
            ]

            if not trial_columns:

                st.sidebar.error(
                    "試行番号の列が見つかりません。"
                )

            else:

                rows = []

                for row_index in range(
                    len(excel_df)
                ):

                    row_data = {}

                    # A列
                    first_value = (
                        excel_df.iloc[
                            row_index,
                            0
                        ]
                    )

                    if pd.isna(
                        first_value
                    ):

                        first_value = ""

                    row_data[
                        ITEM_COL
                    ] = str(first_value)

                    # 種類
                    if row_index % 2 == 0:

                        row_data[
                            TYPE_COL
                        ] = "判定"

                    else:

                        row_data[
                            TYPE_COL
                        ] = MEMO

                        row_data[
                            ITEM_COL
                        ] = MEMO

                    # 試行
                    for col in trial_columns:

                        value = (
                            excel_df.loc[
                                row_index,
                                col
                            ]
                        )

                        if pd.isna(
                            value
                        ):

                            value = ""

                        value = str(value)

                        if value not in [
                            "",
                            "○",
                            "×"
                        ]:

                            value = ""

                        row_data[
                            col
                        ] = value

                    rows.append(
                        row_data
                    )

                st.session_state.df = (
                    normalize_data(
                        pd.DataFrame(rows)
                    )
                )

                st.sidebar.success(
                    "Excelを読み込みました。"
                )

                st.rerun()

        except Exception as e:

            st.sidebar.error(
                f"読み込みエラー: {e}"
            )


# =========================================================
# 自動追加
# =========================================================

df = st.session_state.df.copy()

df = normalize_data(df)

df = auto_add_item(df)

df = auto_add_trial_column(df)

st.session_state.df = df


# =========================================================
# 表設定
# =========================================================

trial_columns = (
    get_trial_columns(
        st.session_state.df
    )
)


column_config = {

    ITEM_COL:
        st.column_config.TextColumn(
            "項目名 / メモ",
            width="medium"
        ),

    TYPE_COL:
        st.column_config.TextColumn(
            "種類",
            disabled=True,
            width="small"
        )
}


# ○ / ×
for col in trial_columns:

    column_config[col] = (
        st.column_config.SelectboxColumn(
            str(col),
            options=[
                "",
                "○",
                "×"
            ],
            width="small"
        )
    )


# =========================================================
# 編集表
# =========================================================

st.subheader(
    "📊 表計算エリア"
)


edited_df = st.data_editor(

    st.session_state.df,

    column_config=column_config,

    use_container_width=True,

    hide_index=True,

    num_rows="dynamic",

    key="main_editor"
)


# =========================================================
# 編集結果を保存
# =========================================================

edited_df = normalize_data(
    edited_df
)

edited_df = auto_add_item(
    edited_df
)

edited_df = auto_add_trial_column(
    edited_df
)

st.session_state.df = (
    edited_df
)


# =========================================================
# ○割合の計算
# =========================================================

trial_columns = (
    get_trial_columns(
        st.session_state.df
    )
)

# 全体試行回数
if trial_columns:

    max_trial = max(
        int(column)
        for column in trial_columns
    )

else:

    max_trial = 0


# =========================================================
# 項目ごとの集計
# =========================================================

summary_rows = []


for row in range(
    0,
    len(st.session_state.df),
    2
):

    item_name = (
        st.session_state.df.at[
            row,
            ITEM_COL
        ]
    )

    # ○の数
    o_count = 0

    for col in trial_columns:

        value = (
            st.session_state.df.at[
                row,
                col
            ]
        )

        if value == "○":

            o_count += 1

    # 割合
    if max_trial > 0:

        percentage = (
            o_count /
            max_trial
        ) * 100

    else:

        percentage = 0.0

    summary_rows.append(
        {
            "項目名":
                item_name,

            "○の数":
                o_count,

            "全体試行回数":
                max_trial,

            "○割合":
                percentage
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# =========================================================
# 集計結果
# =========================================================

st.subheader(
    "📈 集計結果"
)


# ここが今回の重要部分
# ○の数・全体試行回数・割合を必ず別表として表示

st.dataframe(

    summary_df.style.format(
        {
            "○割合":
                "{:.1f}%"
        }
    ),

    use_container_width=True,

    hide_index=True
)


# =========================================================
# ○ / × の色表示
# =========================================================

st.subheader(
    "🎨 入力結果"
)


def color_value(value):

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


colored_df = (
    st.session_state.df
    .style
    .map(
        color_value,
        subset=trial_columns
    )
)


st.dataframe(
    colored_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# Excel保存
# =========================================================

st.subheader(
    "💾 保存"
)


try:

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        # 入力データ
        st.session_state.df.to_excel(
            writer,
            index=False,
            sheet_name="試行管理表"
        )

        # 集計結果
        summary_df.to_excel(
            writer,
            index=False,
            sheet_name="集計結果"
        )

    excel_buffer.seek(0)

    st.download_button(

        label="📊 Excelとして保存",

        data=excel_buffer.getvalue(),

        file_name="○×試行管理表.xlsx",

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
        st.session_state.df
        .to_csv(
            index=False,
            encoding="utf-8-sig"
        )
    )

    st.download_button(

        label="📥 CSVとして保存",

        data=csv_data,

        file_name="○×試行管理表.csv",

        mime="text/csv",

        key="csv_download"
    )

except Exception as e:

    st.error(
        f"CSV保存エラー: {e}"
    )


# =========================================================
# 使い方
# =========================================================

with st.expander(
    "📖 使い方"
):

    st.write(
        """
### 入力

1. 項目名を入力
2. 試行番号のセルをクリック
3. 「○」「×」「空欄」から選択
4. 判定行の下にメモを入力

### 集計

例えば

1  2  3  4  5
○  ×  ○  ○  ×

なら、

○の数 → 3
全体試行回数 → 5
○割合 → 60.0%

となります。

### 自動追加

最後の試行列に入力すると、
次の試行列が自動的に追加されます。

最後の項目に入力すると、
次の項目が自動的に追加されます。
        """
    )
    
