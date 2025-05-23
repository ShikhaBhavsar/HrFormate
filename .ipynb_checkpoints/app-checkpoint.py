import streamlit as st
import pandas as pd
import zipfile
import io
import tempfile
from datetime import datetime

# Define column mappings
EXPERIENCED_MAPPING = {
    'Tags': 'Applicaiton Date',
    'CREATED_DATE': 'Updation Date',
    'Candidate ID': 'Candidate ID',
    'Name': 'Candidate Name',
    'E-mail': 'Email',
    'Mobile No': 'Contact No.',
    'Location': 'Location',
    'How Did You Hear About This Job Opportunity?': 'Source',
    'Total Experience (in Years)': 'Total Experience',
    'Relevant Experience (in Years)': 'Relevant Experience',
    'What is your current annual salary? (Please specify in Lacs such as 4,00,000)': 'Current Salary (Annual)',
    'What is your expected annual salary? (Please specify in Lacs such as 6,00,000)': 'Expected Salary (Annual)',
    'Notice Period (in days)': 'Notice Period (in days)',
    'Status': 'Status',
    'Comments': 'Comments'
}

FRESHER_MAPPING = {
    'Candidate ID': 'Candidate ID',
    'Name': 'Candidate Name',
    'E-mail': 'Email',
    'Mobile No': 'Contact No.',
    'Location': 'Location',
    'How Did You Hear About This Job Opportunity?': 'Source',
    'Name of the Institute': 'Name of Instiute',
    'Total Experience (in Years)': 'Experience',
    'Tags': 'Application Date',
    'CREATED_DATE': 'Updation Date',
    'Status': 'Status',
    'Comments': 'Comments'
}

FRESHER_ORDER = [
    'Application Date', 'Updation Date', 'Candidate ID', 'Candidate Name',
    'Email', 'Contact No.', 'Location', 'Source', 'Name of Instiute',
    'Experience', 'Status', 'Comments'
]

# Utility: Convert date string to Excel numeric date
def format_date(date_str):
    try:
        day, month, year = map(int, date_str.split()[0].split('/'))
        date = datetime(year, month, day)
        excel_date = (date - datetime(1899, 12, 30)).days
        return excel_date
    except:
        return date_str

# Caching data loading to prevent repeated reads
@st.cache_data
def load_file(file):
    file_ext = file.name.split('.')[-1].lower()
    if file_ext == 'csv':
        return pd.read_csv(file)
    elif file_ext == 'xlsx':
        return pd.read_excel(file)
    return None

# Process a single dataframe
def process_dataframe(df, mapping, order=None):
    new_df = pd.DataFrame()
    for old, new in mapping.items():
        if old in df.columns:
            new_df[new] = df[old].apply(format_date) if 'Date' in new else df[old]
        else:
            new_df[new] = ''
    if order:
        new_df = new_df[[col for col in order if col in new_df.columns]]
    return new_df
   
    # Optional: sort by Application Date if it exists
    if 'Application Date' in new_df.columns:
        new_df = new_df.sort_values(by='Application Date', ascending=True)

    return new_df


# Process uploaded file
def process_file(file, format_choice,sort=False):
    mapping = FRESHER_MAPPING if format_choice == 'Fresher' else EXPERIENCED_MAPPING
    order = FRESHER_ORDER if format_choice == 'Fresher' else None
    df = load_file(file)  # Using cached load_file to avoid multiple reads
    if df is not None:
        return process_dataframe(df, mapping, order, sort)
    return None

# --- Streamlit UI ---
st.title("Candidate File Formatter")

format_choice = st.radio("Select Candidate Format:", ["Experienced", "Fresher"])
sort_checkbox = st.checkbox("Sort by Application Date (if available)")
uploaded_files = st.file_uploader("Upload .csv, .xlsx, or .zip file(s)", type=["csv", "xlsx", "zip"], accept_multiple_files=True)

if uploaded_files:
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zf:
        for file in uploaded_files:
            result = process_file(file, format_choice, sort_checkbox)
            if isinstance(result, list):  # ZIP inside
                for name, df in result:
                    csv_bytes = df.to_csv(index=False).encode('utf-8')
                    zf.writestr(f"processed_{name.replace(' ', '_')}.csv", csv_bytes)
            else:
                csv_bytes = result.to_csv(index=False).encode('utf-8')
                zf.writestr(f"processed_{file.name.replace(' ', '_')}.csv", csv_bytes)

    st.success("Files processed successfully.")
    st.download_button("Download Processed ZIP", data=output_zip.getvalue(), file_name="processed_files.zip", mime="application/zip")
