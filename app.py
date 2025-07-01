import streamlit as st
from reconcile import load_data, match_patients, export_to_excel
import pandas as pd

st.title("🏥 Patient Data Reconciliation Tool")

file1 = st.file_uploader("Upload Patient File 1", type=["xlsx"])
file2 = st.file_uploader("Upload Patient File 2", type=["xlsx"])

if file1 and file2:
    df1, df2 = load_data(file1, file2)
    matches = match_patients(df1, df2)
    st.success(f"✅ Found {len(matches)} potential duplicate records.")

    df1['Source'] = "File 1"
    df2['Source'] = "File 2"
    combined = pd.concat([df1, df2])

    if st.button("📤 Export Reconciled Report"):
        export_to_excel(combined)
        st.success("📁 Reconciled data saved to 'output/reconciled_data.xlsx'")
