import io
import streamlit as st
import pandas as pd
from supabase import create_client
st.write(list(st.secrets.keys()))



# =========================================================
# ページ設定
# =========================================================

st.set_page_config(
    page_title="○×練習",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ○×練習")


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

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(
        url,
        key
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

    # 項目名
    if ITEM_COL not in df.columns:

        df[ITEM_COL] = ""

    # 種類
    if TYPE_COL not in df.columns:

        df[TYPE_COL] = ""

    # 試行列
    trial_columns = get_trial_columns(df)

    if not trial_columns:

        df["1"] = ""

    trial_columns = get_trial_columns(df)

    # ○ / × / 空欄以外を消す
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

    # 列の順番
    trial_columns = get_trial_columns(df)

    columns = (
        [ITEM_COL, TYPE_COL]
        + trial_columns
    )

    return df[columns]


# =========================================================
# 最後の列に入力したら自動追加
# =========================================================

def auto_add_trial_column(df):

    df = df.copy()

    trial_columns = get_trial_columns(df)

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
# 最後の項目に入力したら自動追加
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

    # ○ / ×
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

    # メモ
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

    # 新しい項目を追加
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

        # データがまだ存在しない
        if not result.data:

            return create_initial_data()

        saved_data = result.data[0]["data"]

        # 初期データ
        if (
            isinstance(saved_data, dict)
            and saved_data.get("initialized") is True
        ):

            return create_initial_data()

        # JSON → DataFrame
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

        # DataFrame → JSON
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

    st.session_state.df = (
        load_data()
    )


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

    st.session_state.df = normalize_data(df)

    save_data(
        st.session_state.df
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

    st.session_state.df = normalize_data(df)

    save_data(
        st.session_state.df
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

    save_data(
        st.session_state.df
    )

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

trial_columns = get_trial_columns(
    st.session_state.df
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


# ○ / × を選択
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

st.session_state.df = edited_df


# =========================================================
# 自動保存
# =========================================================

save_data(
    st.session_state.df
)


# =========================================================
# 集計
# =========================================================

trial_columns = get_trial_columns(
    st.session_state.df
)

if trial_columns:

    max_trial = max(
        int(c)
        for c in trial_columns
    )

else:

    max_trial = 0


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

        if (
            st.session_state.df.at[
                row,
                col
            ] == "○"
        ):

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
# ○ = 赤、× = 青
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
    "📥 ファイルとして保存"
)

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
    csv_data = st.session_state.df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 CSVとして保存",
        data=csv_data,
        file_name="○×試行管理表.csv",
        mime="text/csv",
        key="csv_download",
    )

except Exception as e:
    st.error(f"CSV保存エラー: {e}")
    
    
