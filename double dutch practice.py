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
# 試行列
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

    # 不要列
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

    # 全データを文字列にする
    for col in trial_columns:

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
        )

    # 判定行 / メモ行
    for row in range(len(df)):

        if row % 2 == 0:

            # 判定
            df.at[
                row,
                TYPE_COL
            ] = "判定"

            item_name = str(
                df.at[
                    row,
                    ITEM_COL
                ]
            )

            if (
                item_name.strip() == ""
                or item_name == "nan"
                or item_name == MEMO
            ):

                df.at[
                    row,
                    ITEM_COL
                ] = (
                    f"項目{row // 2 + 1}"
                )

        else:

            # メモ
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
# 列を自動追加
# =========================================================

def auto_add_trial_column(df):

    df = df.copy()

    trial_columns = get_trial_columns(df)

    if not trial_columns:

        df["1"] = ""

        return df

    last_column = trial_columns[-1]

    # 最後の判定列だけを確認
    should_add = False

    for row in range(
        0,
        len(df),
        2
    ):

        value = str(
            df.at[
                row,
                last_column
            ]
        )

        if value in [
            "○",
            "×"
        ]:

            should_add = True
            break

    if should_add:

        new_column = str(
            int(last_column) + 1
        )

        if new_column not in df.columns:

            df[new_column] = ""

    return df


# =========================================================
# 行を自動追加
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

            value = str(
                df.at[
                    last_choice_row,
                    col
                ]
            )

            if value in [
                "○",
                "×"
            ]:

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

    # 新しい項目
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
# Supabase読み込み
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
            isinstance(saved_data, dict)
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
# Supabase保存
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

    df = normalize_data(df)

    st.session_state.df = df

    save_data(df)

    st.rerun()


# =========================================================
# 試行列追加
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
# 最新データ
# =========================================================

df = normalize_data(
    st.session_state.df
)


# =========================================================
# 表計算エリア
# =========================================================

st.subheader(
    "📊 表計算エリア"
)

trial_columns = get_trial_columns(
    df
)


# ---------------------------------------------------------
# ヘッダー
# ---------------------------------------------------------

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
# 表の入力
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
        [2] + [1] * len(trial_columns)
    )

    # 項目名
    with choice_columns[0]:

        item_name = st.text_input(
            " ",
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

            selected = st.selectbox(
                f"{item_index}_{col}",
                options=[
                    "",
                    "○",
                    "×"
                ],
                index=[
                    "",
                    "○",
                    "×"
                ].index(
                    current_value
                ),
                key=f"choice_{item_index}_{col}",
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
        [2] + [1] * len(trial_columns)
    )

    # 「メモ」
    with memo_columns[0]:

        st.markdown(
            "📝 メモ"
        )

    new_df.at[
        item_index + 1,
        ITEM_COL
    ] = MEMO

    # 自由入力
    for i, col in enumerate(
        trial_columns,
        start=1
    ):

        with memo_columns[i]:

            memo_value = st.text_input(
                f"memo_{item_index}_{col}",
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

    # 区切り
    st.divider()


# =========================================================
# 自動追加
# =========================================================

new_df = normalize_data(
    new_df
)

new_df = auto_add_item(
    new_df
)

new_df = auto_add_trial_column(
    new_df
)


# =========================================================
# 保存
# =========================================================

st.session_state.df = new_df

save_data(
    new_df
)


# =========================================================
# ○割合計算
# =========================================================

trial_columns = get_trial_columns(
    new_df
)


if trial_columns:

    max_trial = max(
        int(col)
        for col in trial_columns
    )

else:

    max_trial = 0


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

    o_count = 0

    for col in trial_columns:

        if new_df.at[
            row,
            col
        ] == "○":

            o_count += 1

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
# ○割合
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
# 色付き表示
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
        )
    )

except Exception as e:

    st.error(
        f"Excel保存エラー: {e}"
    )


# =========================================================
# CSV保存
# =========================================================

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

    mime="text/csv"
)


# =========================================================
# 状態
# =========================================================

st.sidebar.divider()

st.sidebar.success(
    "データは自動保存されています"
)

st.sidebar.caption(
    "ブラウザを閉じてもデータはSupabaseに保存されています。"
)
