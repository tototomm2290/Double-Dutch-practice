import io
import streamlit as st
import pandas as pd
from supabase import create_client


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
# Supabase接続
# =========================================================

@st.cache_resource
def get_supabase():

    if "SUPABASE_URL" not in st.secrets:
        st.error(
            "SUPABASE_URL が設定されていません。"
        )
        st.stop()

    if "SUPABASE_KEY" not in st.secrets:
        st.error(
            "SUPABASE_KEY が設定されていません。"
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
# 試行列を取得
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

    # 不要列を削除
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

    # 試行列は文字列
    for col in trial_columns:

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
        )

    # 判定行 / メモ行
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
                    f"項目{row // 2 + 1}"
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

    # 列順
    trial_columns = get_trial_columns(df)

    columns = (
        [ITEM_COL, TYPE_COL]
        + trial_columns
    )

    for col in columns:

        if col not in df.columns:
            df[col] = ""

    return df[columns]


# =========================================================
# Supabaseから読み込み
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

        if not result.data:

            return create_initial_data()

        saved_data = result.data[0]["data"]

        # 初期状態
        if (
            isinstance(
                saved_data,
                dict
            )
            and saved_data.get(
                "initialized"
            ) is True
        ):

            return create_initial_data()

        df = pd.DataFrame(
            saved_data
        )

        return normalize_data(df)

    except Exception as e:

        st.error(
            f"データ読み込みエラー: {e}"
        )

        return create_initial_data()


# =========================================================
# Supabaseへ保存
# =========================================================

def save_data(df):

    try:

        df = normalize_data(df)

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
            f"データ保存エラー: {e}"
        )

        return False


# =========================================================
# 初回読み込み
# =========================================================

if "df" not in st.session_state:

    st.session_state.df = load_data()


# =========================================================
# データ整理
# =========================================================

st.session_state.df = normalize_data(
    st.session_state.df
)


# =========================================================
# サイドバー
# =========================================================

st.sidebar.header("操作")


# =========================================================
# 手動：行追加
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

    df = normalize_data(df)

    st.session_state.df = df

    save_data(df)

    st.rerun()


# =========================================================
# 手動：試行列追加
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

    if new_column not in df.columns:

        df[new_column] = ""

    df = normalize_data(df)

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
# 表計算エリア
# =========================================================

df = normalize_data(
    st.session_state.df
)

trial_columns = get_trial_columns(df)


st.subheader(
    "📊 表計算エリア"
)


# =========================================================
# ヘッダー
# =========================================================

header_columns = st.columns(
    [2] + [1] * len(trial_columns)
)

with header_columns[0]:

    st.markdown(
        "**項目名**"
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
# 編集用DataFrame
# =========================================================

new_df = df.copy()


# =========================================================
# 表の入力
# =========================================================

for item_index in range(
    0,
    len(df),
    2
):

    # -----------------------------------------------------
    # 判定行
    # -----------------------------------------------------

    choice_columns = st.columns(
        [2] + [1] * len(trial_columns)
    )

    # 項目名
    with choice_columns[0]:

        item_name = st.text_input(
            "項目名",
            value=str(
                df.at[
                    item_index,
                    ITEM_COL
                ]
            ),
            key=f"item_{item_index}",
            label_visibility="collapsed"
        )

        new_df.at[
            item_index,
            ITEM_COL
        ] = item_name


    # ○ / ×
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

            if current_value not in [
                "",
                "○",
                "×"
            ]:

                current_value = ""

            options = [
                "",
                "○",
                "×"
            ]

            selected = st.selectbox(

                f"判定_{item_index}_{col}",

                options=options,

                index=options.index(
                    current_value
                ),

                key=f"choice_{item_index}_{col}",

                label_visibility="collapsed"
            )

            new_df.at[
                item_index,
                col
            ] = selected


    # -----------------------------------------------------
    # メモ行
    # -----------------------------------------------------

    memo_columns = st.columns(
        [2] + [1] * len(trial_columns)
    )

    with memo_columns[0]:

        st.markdown(
            "📝 **メモ**"
        )

    new_df.at[
        item_index + 1,
        ITEM_COL
    ] = MEMO

    # メモは完全自由入力
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

                key=f"memo_{item_index}_{col}",

                label_visibility="collapsed"
            )

            new_df.at[
                item_index + 1,
                col
            ] = memo_value


    st.divider()


# =========================================================
# 編集結果
# =========================================================

new_df = normalize_data(
    new_df
)


# =========================================================
# 自動追加処理は一切しない
# =========================================================

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

trial_columns = get_trial_columns(
    new_df
)


# 全体試行回数
if trial_columns:

    max_trial = max(
        int(col)
        for col in trial_columns
    )

else:

    max_trial = 0


# =========================================================
# 項目別集計
# =========================================================

summary_rows = []


for row in range(
    0,
    len(new_df),
    2
):

    item_name = new_df.at[
        row,
        ITEM_COL
    ]

    # ○の数
    o_count = 0

    for col in trial_columns:

        if new_df.at[
            row,
            col
        ] == "○":

            o_count += 1


    # ○割合
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
# 色付き結果
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
    new_df
    .drop(
        columns=[TYPE_COL]
    )
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
    "📥 ファイルとして保存"
)


try:

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        new_df.drop(
            columns=[TYPE_COL]
        ).to_excel(
            writer,
            index=False,
            sheet_name="試行管理表"
        )

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
        new_df
        .drop(
            columns=[TYPE_COL]
        )
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
# 状態
# =========================================================

st.sidebar.divider()

st.sidebar.success(
    "データは自動保存されています"
)

st.sidebar.caption(
    "ブラウザを閉じてもSupabaseに保存されています。"
)
