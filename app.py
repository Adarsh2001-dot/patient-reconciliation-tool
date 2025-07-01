import streamlit as st
from reconcile import load_data, match_patients, export_to_excel
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏥 Patient Data Reconciliation Tool")

file1 = st.file_uploader("Upload Patient File 1", type=["xlsx"])
file2 = st.file_uploader("Upload Patient File 2", type=["xlsx"])

if file1 and file2:
    df1, df2 = load_data(file1, file2)
    matches = match_patients(df1, df2)

    st.success(f"✅ Found {len(matches)} potential duplicate records.")

    if matches:
        match_df = pd.DataFrame(matches, columns=["File1_PatientID", "File2_PatientID", "MatchScore"])
        st.subheader("🔍 Duplicate Record Match Scores")

        score_range = st.slider("🎯 Filter by Match Score", 0, 100, (85, 100))
        filtered_matches = match_df[(match_df["MatchScore"] >= score_range[0]) & (match_df["MatchScore"] <= score_range[1])]
        st.dataframe(filtered_matches)

        st.bar_chart(filtered_matches.set_index("File1_PatientID")["MatchScore"])

        st.subheader("📋 Side-by-Side Comparison")
        for idx, row in filtered_matches.iterrows():
            left = df1[df1["PatientID"] == row["File1_PatientID"]].iloc[0]
            right = df2[df2["PatientID"] == row["File2_PatientID"]].iloc[0]

            with st.expander(f"Compare: {row['File1_PatientID']} vs {row['File2_PatientID']} (Score: {row['MatchScore']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**From File 1**")
                    st.json(left.to_dict())
                with col2:
                    st.markdown("**From File 2**")
                    st.json(right.to_dict())

    df1['Source'] = "File 1"
    df2['Source'] = "File 2"
    combined = pd.concat([df1, df2])

    if st.button("📤 Export Reconciled Report"):
        output_file = export_to_excel(combined)
        st.success("📁 Reconciled data is ready!")
        st.download_button(
            label="⬇ Download Reconciled File",
            data=output_file,
            file_name="reconciled_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
