import pandas as pd
import io
from fuzzywuzzy import fuzz

def load_data(file1, file2):
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    return df1, df2

def match_patients(df1, df2):
    matches = []
    for _, row1 in df1.iterrows():
        for _, row2 in df2.iterrows():
            score = fuzz.token_sort_ratio(row1['Name'], row2['Name'])
            if score > 85 and row1['DOB'] == row2['DOB']:
                matches.append((row1['PatientID'], row2['PatientID'], score))
    return matches

def export_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output
