import streamlit as st
from reconcile import load_data, match_patients, export_to_excel
import pandas as pd
import csv
from datetime import datetime
import os

st.set_page_config(layout="wide", page_title="Patient Reconciliation Tool", page_icon=None)

# Custom CSS styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%) !important;
    }
    html, body, .css-1v0mbdj, .css-1d391kg {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%) !important;
        color: #333333;
    }
    .stButton > button {
        border-radius: 10px;
        background-color: #6a11cb;
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        transition: 0.3s;
        border: none;
    }
    .stButton > button:hover {
        background-color: #2575fc;
        cursor: pointer;
    }
    .stTextInput > div > div > input {
        background-color: #ffffffcc;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ccc;
    }
    .stDataFrame {
        background-color: #ffffffcc;
        border-radius: 8px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Patient Record Reconciliation")

file1 = st.file_uploader("Upload Patient File 1 (Excel)", type=["xlsx"])
file2 = st.file_uploader("Upload Patient File 2 (Excel)", type=["xlsx"])

if file1 and file2:
    df1, df2 = load_data(file1, file2)

    st.subheader("Search Patients")
    search_query = st.text_input("Enter Name or ID:")
    if search_query:
        filtered_df1 = df1[df1.apply(lambda row: search_query.lower() in str(row['Name']).lower() or search_query.lower() in str(row['PatientID']).lower(), axis=1)]
        filtered_df2 = df2[df2.apply(lambda row: search_query.lower() in str(row['Name']).lower() or search_query.lower() in str(row['PatientID']).lower(), axis=1)]
        st.write("Results from File 1")
        st.dataframe(filtered_df1)
        st.write("Results from File 2")
        st.dataframe(filtered_df2)

    matches = match_patients(df1, df2)
    st.success(f"Found {len(matches)} potential duplicate records.")

    if matches:
        match_df = pd.DataFrame(matches, columns=["File1_PatientID", "File2_PatientID", "MatchScore"])
        st.subheader("Match Scores")
        score_range = st.slider("Filter by Score", 0, 100, (85, 100))
        filtered_matches = match_df[(match_df["MatchScore"] >= score_range[0]) & (match_df["MatchScore"] <= score_range[1])]

        def highlight_score(val):
            if val >= 95:
                return "background-color: #c6f6d5"
            elif val >= 85:
                return "background-color: #fef3c7"
            else:
                return "background-color: #fecaca"

        styled_df = filtered_matches.style.applymap(highlight_score, subset=["MatchScore"])
        st.dataframe(styled_df, use_container_width=True)
        st.bar_chart(filtered_matches.set_index("File1_PatientID")["MatchScore"])

        st.subheader("Side-by-Side Comparison & Anomaly Flagging")
        for idx, row in filtered_matches.iterrows():
            left = df1[df1["PatientID"] == row["File1_PatientID"]].iloc[0]
            right = df2[df2["PatientID"] == row["File2_PatientID"]].iloc[0]
            with st.expander(f"{row['File1_PatientID']} vs {row['File2_PatientID']} (Score: {row['MatchScore']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**From File 1**")
                    st.json(left.to_dict())
                with col2:
                    st.markdown("**From File 2**")
                    st.json(right.to_dict())

                if st.button(f"🚨 Flag Anomaly: {row['File1_PatientID']} vs {row['File2_PatientID']}", key=f"flag_{idx}"):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_data = {
                        "Time": timestamp,
                        "File1_ID": row['File1_PatientID'],
                        "File2_ID": row['File2_PatientID'],
                        "MatchScore": row['MatchScore']
                    }
                    with open("anomaly_log.csv", "a", newline="") as logfile:
                        writer = csv.DictWriter(logfile, fieldnames=log_data.keys())
                        if logfile.tell() == 0:
                            writer.writeheader()
                        writer.writerow(log_data)
                    st.warning("Anomaly logged successfully!")

        if st.button("Export Matched Records"):
            export_rows = []
            for idx, row in filtered_matches.iterrows():
                rec1 = df1[df1["PatientID"] == row["File1_PatientID"]].iloc[0]
                rec2 = df2[df2["PatientID"] == row["File2_PatientID"]].iloc[0]
                export_rows.append({
                    "File1_ID": rec1["PatientID"],
                    "File1_Name": rec1["Name"],
                    "File2_ID": rec2["PatientID"],
                    "File2_Name": rec2["Name"],
                    "MatchScore": row["MatchScore"]
                })
            matched_df = pd.DataFrame(export_rows)
            file = export_to_excel(matched_df)
            st.download_button("Download Matched Records", data=file, file_name="matched_duplicates.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.subheader("Anomaly Log Viewer")
if os.path.exists("anomaly_log.csv"):
    log_df = pd.read_csv("anomaly_log.csv")
    st.dataframe(log_df)
    st.download_button("Download Anomaly Log", data=log_df.to_csv(index=False).encode("utf-8"), file_name="anomaly_log.csv", mime="text/csv")
else:
    st.info("No anomalies flagged yet.")
