import streamlit as st
import pandas as pd
import zipfile
import io
from datetime import datetime

# Define column mappings
EXPERIENCED_MAPPING = {
    'Tags': 'Application Date',
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

# Utility: Convert date string to datetime object for sorting
def parse_date(date_str):
    if not isinstance(date_str, str) or not date_str.strip():
        return pd.NaT  # Return Not-a-Time for empty or non-string values
    
    try:
        # Handle the format DD/MM/YYYY HH:MM AM/PM
        if '/' in date_str and ':' in date_str:
            date_part = date_str.split()[0]
            day, month, year = map(int, date_part.split('/'))
            return datetime(year, month, day)
        # Handle other possible date formats
        elif '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                return datetime(year, month, day)
        return pd.to_datetime(date_str, errors='coerce')
    except Exception:
        return pd.NaT  # Return Not-a-Time if parsing fails

# Format date to MM/DD/YYYY
def format_date(date_obj):
    if pd.isna(date_obj):
        return ''
    try:
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%m/%d/%Y')
        else:
            return pd.to_datetime(date_obj).strftime('%m/%d/%Y')
    except Exception:
        return ''

# Process a single dataframe
def process_dataframe(df, mapping, order=None):
    new_df = pd.DataFrame()
    
    # Map the columns according to the provided mapping
    for old, new in mapping.items():
        if old in df.columns:
            new_df[new] = df[old]
        else:
            new_df[new] = ''
    
    # Parse dates for sorting
    if 'Application Date' in new_df.columns:
        # Create a temporary column for sorting
        new_df['_temp_sort_date'] = new_df['Application Date'].apply(parse_date)
        # Sort by this temporary column
        new_df = new_df.sort_values(by='_temp_sort_date', ascending=True, na_position='last')
        # Format dates back to MM/DD/YYYY
        new_df['Application Date'] = new_df['_temp_sort_date'].apply(format_date)
        # Drop the temporary column
        new_df = new_df.drop('_temp_sort_date', axis=1)
    
    if 'Updation Date' in new_df.columns:
        new_df['Updation Date'] = new_df['Updation Date'].apply(lambda x: format_date(parse_date(x)) if isinstance(x, str) else '')
    
    if order:
        new_df = new_df[[col for col in order if col in new_df.columns]]
    
    return new_df

# Process uploaded file
def process_file(file, format_choice):
    mapping = FRESHER_MAPPING if format_choice == 'Fresher' else EXPERIENCED_MAPPING
    order = FRESHER_ORDER if format_choice == 'Fresher' else None
    file_ext = file.name.split('.')[-1].lower()

    if file_ext == 'csv':
        df = pd.read_csv(file)
        return process_dataframe(df, mapping, order)
    elif file_ext == 'xlsx':
        df = pd.read_excel(file)
        return process_dataframe(df, mapping, order)
    elif file_ext == 'zip':
        with zipfile.ZipFile(file) as z:
            processed_files = []
            for name in z.namelist():
                ext = name.split('.')[-1].lower()
                if ext in ['csv', 'xlsx']:
                    with z.open(name) as f:
                        if ext == 'csv':
                            df = pd.read_csv(f)
                        else:  # xlsx
                            # Need to use BytesIO for Excel files from ZIP
                            content = z.read(name)
                            df = pd.read_excel(io.BytesIO(content))
                        processed = process_dataframe(df, mapping, order)
                        processed_files.append((name, processed))
            return processed_files
    return None

# --- Streamlit UI ---
st.title("Candidate File Formatter")

format_choice = st.radio("Select Candidate Format:", ["Experienced", "Fresher"])
uploaded_files = st.file_uploader("Upload .csv, .xlsx, or .zip file(s)", type=["csv", "xlsx", "zip"], accept_multiple_files=True)

if uploaded_files:
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zf:
        for file in uploaded_files:
            result = process_file(file, format_choice)
            if isinstance(result, list):  # ZIP inside
                for name, df in result:
                    csv_bytes = df.to_csv(index=False).encode('utf-8')
                    zf.writestr(f"processed_{name.replace(' ', '_')}.csv", csv_bytes)
            else:
                csv_bytes = result.to_csv(index=False).encode('utf-8')
                zf.writestr(f"processed_{file.name.replace(' ', '_')}.csv", csv_bytes)

    st.success("Files processed successfully.")
    st.download_button("Download Processed ZIP", data=output_zip.getvalue(), file_name="processed_files.zip", mime="application/zip")