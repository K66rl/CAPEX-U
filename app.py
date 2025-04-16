
import streamlit as st
import pandas as pd
import sqlite3

st.title("📊 Multi-Entity CAPEX Loader")

# Define column mapping and required fields
COLUMN_ALIASES = {
    "account name": "account_name",
    "period": "period",
    "transaction date": "transaction_date",
    "reference": "reference",
    "amount": "amount",
    "aud": "amount",
    "amount (aud)": "amount",
    "description": "description",
    "other amount": "nzd",
    "journal type": "journal_type",
    "building/hotel/site/dev stage": "stage_code",
    "dev cost category": "cost_category",
    "project": "project",
    "building/hotel/site/dev stage (name)": "stage_name"
}

REQUIRED_FIELDS = [
    "account_name", "period", "transaction_date", "reference", "amount",
    "description", "journal_type", "stage_code", "cost_category", "project", "stage_name"
]

def standardize_and_map_columns(df, sheet_name):
    mapped_columns = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_ALIASES:
            mapped_columns[col] = COLUMN_ALIASES[key]

    df.rename(columns=mapped_columns, inplace=True)
    df.columns = df.columns.str.strip().str.lower()

    missing = [col for col in REQUIRED_FIELDS if col not in df.columns]
    if missing:
        return None, f"❌ Sheet '{sheet_name}' missing columns: {', '.join(missing)}"

    df = df[[col for col in df.columns if col in REQUIRED_FIELDS or col == 'nzd']]
    df['entity'] = sheet_name
    return df, None

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    xlsx = pd.ExcelFile(uploaded_file)
    all_data = []
    validation_errors = []

    for sheet in xlsx.sheet_names:
        df = xlsx.parse(sheet)
        cleaned_df, error = standardize_and_map_columns(df, sheet)
        if error:
            validation_errors.append(error)
        else:
            all_data.append(cleaned_df)

    if validation_errors:
        st.warning("Validation Issues:")
        for msg in validation_errors:
            st.write("-", msg)

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        st.subheader("Preview of Valid Data")
        st.dataframe(full_df)

        if st.button("Append to Database"):
            conn = sqlite3.connect("storage_capex.db")
            full_df.to_sql("capex_data", conn, if_exists="append", index=False)
            conn.close()
            st.success("✅ Data successfully appended.")
    elif not validation_errors:
        st.info("No valid sheets found.")
