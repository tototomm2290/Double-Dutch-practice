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
PERCENT_COL = "○割合"
O_COUNT_COL = "○の数"
TRIAL_COUNT_COL = "全体試行回数"
MEMO = "メモ"


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
        + [
            O_COUNT_COL,
            TRIAL_COUNT_COL,
            PERCENT_COL
        ]
    )

    rows = []

    for i in range(item_count):

        # -----------------------------
        # 判定行
        # -----------------------------

        choice_row = {
            ITEM_COL:
                f"項目{i + 1}",

            TYPE_COL:
                "判定",

            O_COUNT_COL:
                0,

            TRIAL_COUNT_COL:
                trial_count,

            PERCENT_COL:
                0.0
        }

        # -----------------------------
        # メモ行
        # -----------------------------

        memo_row = {
            ITEM_COL:
                MEMO,

            TYPE_COL:
                MEMO,

            O_COUNT_COL:
                "",

            TRIAL_COUNT_COL:
                "",

            PERCENT_COL:
                ""
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
# 試行列取得
# =========================================================

def get_trial_columns(df):

    return sorted(
        [
            str(col)
            for col in df.columns
            if str(col).isdigit()
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

    if O_COUNT_COL not in df.columns:
        df[O_COUNT_COL] = 0

    if TRIAL_COUNT_COL not in df.columns:
        df[TRIAL_COUNT_COL] = 0

    if PERCENT_COL not in df.columns:
        df[PERCENT_COL] = 0.0

    # 試行列
    trial_columns = get_trial_columns(df)

    if not trial_columns:

        df["1"] = ""

    trial_columns = get_trial_columns(df)

    # ○×以外は空欄
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

    # 判定行 / メモ行
    for row in range(len(df)):

        if row % 2 == 0:

            df.at[
                row,
                TYPE_COL
            ] = "判定"

            item = str(
                df.at[
                    row,
                    ITEM_COL
                ]
            )

            if item.strip() == "":

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
    trial_columns = get_trial_columns(df)

    ordered_columns = (
        [ITEM_COL, TYPE_COL]
        + trial_columns
        + [
            O_COUNT_COL,
            TRIAL_COUNT_COL,
            PERCENT_COL
        ]
    )

    for col in ordered_columns:

        if col not in df.columns:
            df[col] = ""

    return df[
        ordered_columns
    ]


# =========================================================
# 割合・○の数・全体回数を計算
# =========================================================

def calculate_summary(df):

    df = df.copy()

    trial_columns = get_trial_columns(df)

    if not trial_columns:

        return df

    # 1行目の数字の最大値
    max_trial = max(
        int(col)
        for col in trial_columns
    )

    for row in range(
        0,
        len(df),
        2
    ):

        # ○の数
        o_count = 0

        for col in trial_columns:

            if (
                df.at[
                    row,
                    col
                ] == "○"
            ):

                o_count += 1

        # ○の数
        df.at[
            row,
            O_COUNT_COL
        ] = o_count

        # 全体試行回数
        df.at[
            row,
            TRIAL_COUNT_COL
        ] = max_trial

        # ○割合
        if max_trial > 0:

            percentage = (
                o_count /
                max_trial
            ) * 100

        else:

            percentage = 0.0

        df.at[
            row,
            PERCENT_COL
        ] = percentage

        # メモ行
        if row + 1 < len(df):

            df.at[
                row + 1,
                O_COUNT_COL
            ] = ""

            df.at[
                row + 1,
                TRIAL_COUNT_COL
            ] = ""

            df.at[
                row + 1,
                PERCENT_COL
            ] = ""

    return df


# =========================================================
# 最後の列に入力されたら自動追加
# =========================================================

def auto_add_trial_column(df):

    df = df.copy()

    trial_columns = get_trial_columns(df)

    if not trial_columns:

        df["1"] = ""

        return df

    last_column = trial_columns[-1]

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
# 最後の項目に入力されたら自動追加
# =========================================================

def auto_add_item(df):

    df = df.copy()

    if len(df) < 2:

        return df

    last_choice_row = len(df) - 2

    trial_columns = get_trial_columns(df)

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
    # 判定
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
    # 新しい項目を追加
    # -----------------------------

    if used:

        new_item_number = (
            len(df) // 2 + 1
        )

        choice = {
            ITEM_COL:
                f"項目{new_item_number}",

            TYPE_COL:
                "判定",

            O_COUNT_COL:
                0,

            TRIAL_COUNT_COL:
                0,

            PERCENT_COL:
                0.0
        }

        memo = {
            ITEM_COL:
                MEMO,

            TYPE_COL:
                MEMO,

            O_COUNT_COL:
                "",

            TRIAL_COUNT_COL:
                "",

            PERCENT_COL:
                ""
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

st.session_state.df = normalize_data(
    st.session_state.df
)

st.session_state.df = calculate_summary(
    st.session_state.df
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

    trial_columns = get_trial_columns(df)

    item_number = (
        len(df) // 2 + 1
    )

    choice = {
        ITEM_COL:
            f"項目{item_number}",

        TYPE_COL:
            "判定",

        O_COUNT_COL:
            0,

        TRIAL_COUNT_COL:
            max(
                [
                    int(c)
                    for c in trial_columns
                ],
                default=0
            ),

        PERCENT_COL:
            0.0
    }

    memo = {
        ITEM_COL:
            MEMO,

        TYPE_COL:
            MEMO,

        O_COUNT_COL:
            "",

        TRIAL_COUNT_COL:
            "",

        PERCENT_COL:
            ""
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

    trial_columns = get_trial_columns(df)

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
    "Excelファイル",
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

            # 数字の列だけ試行列として認識
            trial_columns = [
                str(col)
                for col in excel_df.columns
                if str(col).isdigit()
            ]

            if not trial_columns:

                st.sidebar.error(
                    "試行番号の列が見つかりません。"
                )

            else:

                new_rows = []

                for i in range(
                    len(excel_df)
                ):

                    data = {
                        ITEM_COL:
                            excel_df.iloc[
                                i,
                                0
                            ]
                            if len(
                                excel_df.columns
                            ) > 0
                            else ""
                    }

                    for col in trial_columns:

                        # 列名からExcelの列位置を取得
                        col_index = (
                            excel_df.columns
                            .tolist()
                            .index(col)
                        )

                        value = (
                            excel_df.iloc[
                                i,
                                col_index
                            ]
                        )

                        if pd.isna(value):

                            value = ""

                        value = str(value)

                        if value not in [
                            "",
                            "○",
                            "×"
                        ]:

                            value = ""

                        data[col] = value

                    new_rows.append(data)

                imported_df = pd.DataFrame(
                    new_rows
                )

                # 判定 / メモ
                imported_df[TYPE_COL] = ""

                for i in range(
                    len(imported_df)
                ):

                    if i % 2 == 0:

                        imported_df.at[
                            i,
                            TYPE_COL
                        ] = "判定"

                    else:

                        imported_df.at[
                            i,
                            TYPE_COL
                        ] = MEMO

                        imported_df.at[
                            i,
                            ITEM_COL
                        ] = MEMO

                imported_df[
                    O_COUNT_COL
                ] = 0

                imported_df[
                    TRIAL_COUNT_COL
                ] = 0

                imported_df[
                    PERCENT_COL
                ] = 0.0

                imported_df = (
                    normalize_data(
                        imported_df
                    )
                )

                imported_df = (
                    calculate_summary(
                        imported_df
                    )
                )

                st.session_state.df = (
                    imported_df
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

df = calculate_summary(df)

st.session_state.df = df


# =========================================================
# 試行列
# =========================================================

trial_columns = get_trial_columns(
    st.session_state.df
)


# =========================================================
# 表設定
# =========================================================

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
        ),

    O_COUNT_COL:
        st.column_config.NumberColumn(
            "○の数",
            disabled=True,
            width="small"
        ),

    TRIAL_COUNT_COL:
        st.column_config.NumberColumn(
            "全体試行回数",
            disabled=True,
            width="small"
        ),

    PERCENT_COL:
        st.column_config.NumberColumn(
            "○割合",
            disabled=True,
            format="%.1f%%",
            width="small"
        )
}


# =========================================================
# ○ / × 選択欄
# =========================================================

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
# 表
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
# 編集結果を再計算
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

edited_df = calculate_summary(
    edited_df
)

st.session_state.df = (
    edited_df
)


# =========================================================
# 入力結果の色
# =========================================================

st.subheader(
    "🎨 入力結果"
)


def color_value(value):

    if value == "○":

        return (
            "color: red; "
            "font-weight: bold; "
            "text-align: center;"
        )

    if value == "×":

        return (
            "color: blue; "
            "font-weight: bold; "
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
# 保存
# =========================================================

st.subheader(
    "💾 データ保存"
)


# ---------------------------------------------------------
# Excel
# ---------------------------------------------------------

try:

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        st.session_state.df.to_excel(
            writer,
            index=False,
            sheet_name="試行管理表"
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

        key="excel_save"
    )

except Exception as e:

    st.error(
        f"Excel保存エラー: {e}"
    )


# ---------------------------------------------------------
# CSV
# ---------------------------------------------------------

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

        key="csv_save"
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
### 基本

- 1行1列は空白
- 1行目に1、2、3、4……と試行番号
- 項目名を入力
- 試行セルは「空欄 / ○ / ×」から選択
- 判定行の下がメモ欄
- ○は赤
- ×は青

### 自動追加

- 最後の試行列に入力すると、新しい試行列を自動追加
- 最後の項目に入力すると、新しい項目を自動追加

### 集計

- 1行目の数字の最大値 = 全体試行回数
- 各項目の「○の数」を自動計算
- 各項目の「○割合」を自動計算

例：

試行回数が 1～5 で、

○ × ○ ○ ×

なら、

○の数 = 3
全体試行回数 = 5
○割合 = 60.0%

となります。

### 保存

ExcelまたはCSVで保存できます。
        """
    )
    
