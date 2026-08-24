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
MEMO = "メモ"


# =========================================================
# 初期データ作成
# =========================================================

def create_initial_data(trials=10, items=10):

    columns = (
        [ITEM_COL, TYPE_COL]
        + [str(i) for i in range(1, trials + 1)]
        + [PERCENT_COL]
    )

    rows = []

    for i in range(items):

        # 判定行
        choice = {
            ITEM_COL: f"項目{i + 1}",
            TYPE_COL: "判定",
            PERCENT_COL: 0.0
        }

        # メモ行
        memo = {
            ITEM_COL: MEMO,
            TYPE_COL: MEMO,
            PERCENT_COL: ""
        }

        for col in [str(i) for i in range(1, trials + 1)]:
            choice[col] = ""
            memo[col] = ""

        rows.append(choice)
        rows.append(memo)

    return pd.DataFrame(rows, columns=columns)


# =========================================================
# セッション状態
# =========================================================

if "df" not in st.session_state:

    st.session_state.df = create_initial_data()


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
# データを正規化
# =========================================================

def normalize_data(df):

    df = df.copy()

    # 不要列削除
    df = df.drop(
        columns=["index", "_index"],
        errors="ignore"
    )

    # 必要列
    if ITEM_COL not in df.columns:
        df[ITEM_COL] = ""

    if TYPE_COL not in df.columns:
        df[TYPE_COL] = ""

    if PERCENT_COL not in df.columns:
        df[PERCENT_COL] = 0.0

    # 試行列がなければ1列作成
    trial_columns = get_trial_columns(df)

    if len(trial_columns) == 0:
        df["1"] = ""

    # 改めて試行列取得
    trial_columns = get_trial_columns(df)

    # ○×以外の値を空欄にする
    for col in trial_columns:

        df[col] = df[col].fillna("").astype(str)

        df[col] = df[col].apply(
            lambda x:
            x if x in ["", "○", "×"]
            else ""
        )

    # 判定 / メモ
    for row in range(len(df)):

        if row % 2 == 0:

            df.at[
                row,
                TYPE_COL
            ] = "判定"

            # 項目名が空なら自動入力
            value = str(
                df.at[
                    row,
                    ITEM_COL
                ]
            )

            if value.strip() == "":
                df.at[
                    row,
                    ITEM_COL
                ] = f"項目{row // 2 + 1}"

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
        + [PERCENT_COL]
    )

    df = df[ordered_columns]

    return df


# =========================================================
# ○割合計算
# =========================================================

def calculate_percentages(df):

    df = df.copy()

    trial_columns = get_trial_columns(df)

    if len(trial_columns) == 0:
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

        o_count = 0

        # ○の数
        for col in trial_columns:

            if df.at[row, col] == "○":

                o_count += 1

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

        # メモ行の割合は空欄
        if row + 1 < len(df):

            df.at[
                row + 1,
                PERCENT_COL
            ] = ""

    return df


# =========================================================
# 最後の列を使ったら自動追加
# =========================================================

def auto_add_trial_column(df):

    df = df.copy()

    trial_columns = get_trial_columns(df)

    if len(trial_columns) == 0:

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
# 最後の項目なら自動追加
# =========================================================

def auto_add_item(df):

    df = df.copy()

    if len(df) < 2:
        return df

    last_choice_row = len(df) - 2

    trial_columns = get_trial_columns(df)

    used = False

    # 項目名
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

    # 判定
    if not used:

        for col in trial_columns:

            if (
                str(
                    df.at[
                        last_choice_row,
                        col
                    ]
                ).strip() != ""
            ):

                used = True
                break

    # メモ
    if not used:

        for col in trial_columns:

            if (
                str(
                    df.at[
                        last_choice_row + 1,
                        col
                    ]
                ).strip() != ""
            ):

                used = True
                break

    if used:

        new_item_number = (
            len(df) // 2 + 1
        )

        choice = {
            ITEM_COL:
                f"項目{new_item_number}",
            TYPE_COL:
                "判定",
            PERCENT_COL:
                0.0
        }

        memo = {
            ITEM_COL:
                MEMO,
            TYPE_COL:
                MEMO,
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
                    [choice, memo]
                )
            ],
            ignore_index=True
        )

    return df


# =========================================================
# データを更新
# =========================================================

st.session_state.df = normalize_data(
    st.session_state.df
)


# =========================================================
# サイドバー
# =========================================================

st.sidebar.header("操作")


# =========================================================
# 行追加
# =========================================================

if st.sidebar.button("➕ 行を追加"):

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
        PERCENT_COL:
            0.0
    }

    memo = {
        ITEM_COL:
            MEMO,
        TYPE_COL:
            MEMO,
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
                [choice, memo]
            )
        ],
        ignore_index=True
    )

    st.session_state.df = df

    st.rerun()


# =========================================================
# 列追加
# =========================================================

if st.sidebar.button("➕ 列を追加"):

    df = st.session_state.df.copy()

    trial_columns = get_trial_columns(df)

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

if st.sidebar.button("🔄 新規作成"):

    st.session_state.df = (
        create_initial_data(
            trials=10,
            items=10
        )
    )

    st.rerun()


# =========================================================
# Excel読み込み
# =========================================================

st.sidebar.subheader("📂 ファイル読み込み")

uploaded_file = st.sidebar.file_uploader(
    "Excelファイル",
    type=["xlsx"]
)


if uploaded_file is not None:

    if st.sidebar.button(
        "📂 Excelを読み込む"
    ):

        try:

            # pandasで直接読み込む
            imported = pd.read_excel(
                uploaded_file,
                sheet_name=0,
                header=None
            )

            # 空ファイル対策
            if imported.empty:

                st.sidebar.error(
                    "Excelにデータがありません。"
                )

            else:

                # 1行目から試行番号を取得
                headers = imported.iloc[0].tolist()

                trial_columns = []

                for value in headers[1:]:

                    if pd.notna(value):

                        text = str(value)

                        if (
                            text.isdigit()
                            and text != "0"
                        ):

                            trial_columns.append(
                                text
                            )

                # 試行列が無い場合
                if not trial_columns:

                    trial_columns = [
                        str(i)
                        for i in range(
                            1,
                            11
                        )
                    ]

                rows = []

                # Excelの2行目以降
                for row_index in range(
                    1,
                    len(imported)
                ):

                    row_data = {}

                    # A列
                    first_value = (
                        imported.iloc[
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

                    # 判定 / メモ
                    if (
                        (row_index - 1) % 2 == 0
                    ):

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

                    # 試行データ
                    for col_index, trial in enumerate(
                        trial_columns,
                        start=1
                    ):

                        if (
                            col_index
                            < imported.shape[1]
                        ):

                            value = (
                                imported.iloc[
                                    row_index,
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

                        else:

                            value = ""

                        row_data[
                            trial
                        ] = value

                    rows.append(
                        row_data
                    )

                loaded_df = pd.DataFrame(
                    rows
                )

                # 割合列
                loaded_df[
                    PERCENT_COL
                ] = 0.0

                loaded_df = (
                    normalize_data(
                        loaded_df
                    )
                )

                loaded_df = (
                    calculate_percentages(
                        loaded_df
                    )
                )

                st.session_state.df = (
                    loaded_df
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

df = calculate_percentages(df)

st.session_state.df = df


# =========================================================
# 表示用設定
# =========================================================

trial_columns = get_trial_columns(df)

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

    PERCENT_COL:
        st.column_config.NumberColumn(
            "○割合",
            format="%.1f%%",
            disabled=True,
            width="small"
        )
}


# =========================================================
# ○ / × の選択欄
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
# 表編集
# =========================================================

st.subheader(
    "📊 表計算エリア"
)

edited_df = st.data_editor(
    df,
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    key="table_editor"
)


# =========================================================
# 編集後処理
# =========================================================

edited_df = normalize_data(
    edited_df
)

# 自動追加
edited_df = auto_add_item(
    edited_df
)

edited_df = auto_add_trial_column(
    edited_df
)

# 割合計算
edited_df = calculate_percentages(
    edited_df
)

st.session_state.df = (
    edited_df
)


# =========================================================
# 集計
# =========================================================

st.subheader(
    "📈 集計結果"
)

trial_columns = get_trial_columns(
    st.session_state.df
)

# 全体試行回数
if trial_columns:

    max_trial = max(
        int(col)
        for col in trial_columns
    )

else:

    max_trial = 0


# 全体の○・×
total_o = 0
total_x = 0


# 項目ごとの集計
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

    o_count = 0
    x_count = 0

    for col in trial_columns:

        value = (
            st.session_state.df.at[
                row,
                col
            ]
        )

        if value == "○":

            o_count += 1
            total_o += 1

        elif value == "×":

            x_count += 1
            total_x += 1

    # 最大試行回数に対する割合
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

            "×の数":
                x_count,

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
# 全体集計
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "全体試行回数",
        max_trial
    )

with col2:

    st.metric(
        "○の合計",
        total_o
    )

with col3:

    st.metric(
        "×の合計",
        total_x
    )

with col4:

    if max_trial > 0:

        overall_percentage = (
            total_o /
            (max_trial * len(summary_rows))
        ) * 100

    else:

        overall_percentage = 0.0

    st.metric(
        "○割合",
        f"{overall_percentage:.1f}%"
    )


# =========================================================
# 項目ごとの集計
# =========================================================

st.dataframe(
    summary_df.style.format(
        {
            "○割合": "{:.1f}%"
        }
    ),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# ○は赤、×は青で表示
# =========================================================

st.subheader(
    "🎨 入力結果"
)


def color_cells(value):

    if value == "○":

        return (
            "color: red;"
            "font-weight: bold;"
            "text-align: center;"
        )

    elif value == "×":

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
        color_cells,
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
    "💾 データ保存"
)


try:

    excel_buffer = io.BytesIO()

    # ExcelWriter
    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        # 元データ
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

with st.expander("📖 使い方"):

    st.write(
        """
### 基本

- 1行1列は空白
- 1行目に1、2、3、4……と試行番号
- 項目名を入力
- 試行セルは「空欄 / ○ / ×」から選択
- 判定行の下がメモ欄
- ○は赤、×は青

### 自動追加

- 最後の試行列に入力すると、新しい試行列を自動追加
- 最後の項目に入力すると、新しい項目を自動追加

### 集計

- 「1行目の数字の最大値」を全体試行回数として使用
- 各項目の○の数を計算
- 各項目の×の数を計算
- 各項目の○割合を計算
- 全項目の○合計、×合計も表示

### 保存

- Excel
- CSV

の2種類で保存できます。

### 読み込み

左側の「Excelを読み込む」から、
保存したExcelファイルを選択してください。
        """
    )
    
