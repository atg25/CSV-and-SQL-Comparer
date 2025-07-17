import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font

st.set_page_config(
    page_title="Data Comparison Tool",
    page_icon="📄"
)
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDecoration {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def strip_leading_zeros(df):
    return df.map(lambda x: x.lstrip('0') if isinstance(x, str) and x.isdigit() else x)

def get_composite_key(df, key_columns):
    return df[key_columns].astype(str).apply(lambda x: x.str.strip()).fillna('NA').agg('-'.join, axis=1)

def compare_data(df1, df2, key_columns):
    df1 = strip_leading_zeros(df1).astype(str)
    df2 = strip_leading_zeros(df2).astype(str)
    df1['composite_key'] = get_composite_key(df1, key_columns)
    df2['composite_key'] = get_composite_key(df2, key_columns)
    if df1['composite_key'].duplicated().any():
        st.error("Duplicate composite keys found in first file.")
        return None, None, None
    if df2['composite_key'].duplicated().any():
        st.error("Duplicate composite keys found in second file.")
        return None, None, None
    df1.set_index('composite_key', inplace=True)
    df2.set_index('composite_key', inplace=True)
    added = df2.loc[~df2.index.isin(df1.index)]
    removed = df1.loc[~df1.index.isin(df2.index)]
    changed = [pd.concat([df1.loc[[key]], df2.loc[[key]]], keys=['file1', 'file2'])
               for key in df1.index.intersection(df2.index)
               if not df1.loc[key].equals(df2.loc[key])]
    changed_df = pd.concat(changed) if changed else pd.DataFrame()
    return added, removed, changed_df

def compare_sql_files(sql1, sql2):
    import difflib
    sql1_lines = [line.rstrip('\n') for line in sql1.getvalue().decode().splitlines()]
    sql2_lines = [line.rstrip('\n') for line in sql2.getvalue().decode().splitlines()]
    diff = list(difflib.ndiff(sql1_lines, sql2_lines))
    overlay_rows = []
    line_num1 = 1
    line_num2 = 1
    for line in diff:
        if line.startswith('+ '):
            overlay_rows.append({'Line': line[2:], 'Status': 'Added', 'LineNum1': '', 'LineNum2': line_num2})
            line_num2 += 1
        elif line.startswith('- '):
            overlay_rows.append({'Line': line[2:], 'Status': 'Removed', 'LineNum1': line_num1, 'LineNum2': ''})
            line_num1 += 1
        elif line.startswith('  '):
            overlay_rows.append({'Line': line[2:], 'Status': 'Unchanged', 'LineNum1': line_num1, 'LineNum2': line_num2})
            line_num1 += 1
            line_num2 += 1
    return pd.DataFrame(overlay_rows)

# --- Streamlit UI ---
st.title("CSV & SQL Comparison Tool")

st.subheader("1. Upload CSV Files")
csv1 = st.file_uploader("Upload first CSV file", type="csv", key="csv1")
csv2 = st.file_uploader("Upload second CSV file", type="csv", key="csv2")

st.subheader("2. Specify columns for a unique key (if any)")
key_columns = st.text_input("Enter comma-separated key columns (leave blank to use all columns):")

st.subheader("3. Upload SQL Files (optional)")
sql1 = st.file_uploader("Upload first SQL file", type="sql", key="sql1")
sql2 = st.file_uploader("Upload second SQL file", type="sql", key="sql2")

if st.button("Compare"):
    if csv1 and csv2:
        progress = st.progress(0, text="Starting comparison...")
        df1 = pd.read_csv(csv1)
        progress.progress(10, text="Loaded first CSV file.")
        df2 = pd.read_csv(csv2)
        progress.progress(20, text="Loaded second CSV file.")
        keys = [k.strip() for k in key_columns.split(",")] if key_columns else df1.columns.tolist()
        added, removed, changed = compare_data(df1, df2, keys)
        progress.progress(40, text="Compared CSV data.")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if added is not None:
                added.to_excel(writer, sheet_name='Added')
                removed.to_excel(writer, sheet_name='Removed')
                if not changed.empty:
                    changed.to_excel(writer, sheet_name='Changed')
            sql_overlay_df = None
            if sql1 and sql2:
                sql_overlay_df = compare_sql_files(sql1, sql2)
                if not sql_overlay_df.empty:
                    sql_overlay_df.to_excel(writer, sheet_name='SQL_Overlay', index=False)
        progress.progress(70, text="Wrote results to Excel.")
        # Apply coloring to SQL overlay if present
        if sql1 and sql2 and sql_overlay_df is not None and not sql_overlay_df.empty:
            wb = load_workbook(output)
            ws = wb['SQL_Overlay']
            green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
            red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=2):
                status = row[1].value
                if status == 'Added':
                    row[0].font = Font(color='006100')
                    row[0].fill = green_fill
                elif status == 'Removed':
                    row[0].font = Font(color='9C0006')
                    row[0].fill = red_fill
            wb.save(output)
        progress.progress(90, text="Finalizing...")
        st.success("Comparison complete!")
        progress.progress(100, text="Done!")
        st.download_button("Download comparison_results.xlsx", data=output.getvalue(), file_name="comparison_results.xlsx")
        if added is not None:
            st.write(f"### Added Rows ({len(added)})", added)
            st.write(f"### Removed Rows ({len(removed)})", removed)
            if not changed.empty:
                st.write("### Changed Rows", changed)
        if sql1 and sql2 and sql_overlay_df is not None and not sql_overlay_df.empty:
            tab1, tab2 = st.tabs(["SQL Changes Table", "SQL Overlay View"])
            with tab1:
                st.write("### SQL Changes Table")
                # Filter only added/removed lines
                changes_only = sql_overlay_df[sql_overlay_df['Status'].isin(['Added', 'Removed'])]
                if not changes_only.empty:
                    for _, row in changes_only.iterrows():
                        if row['Status'] == 'Added':
                            st.markdown(f"<span style='color: #006100; background-color: #C6EFCE;'>+ (Line {row['LineNum2']}) {row['Line']}</span>", unsafe_allow_html=True)
                        elif row['Status'] == 'Removed':
                            st.markdown(f"<span style='color: #9C0006; background-color: #FFC7CE;'>- (Line {row['LineNum1']}) {row['Line']}</span>", unsafe_allow_html=True)
                else:
                    st.info("No added or removed lines.")
            with tab2:
                st.write("### SQL Overlay")
                html_lines = []
                for _, row in sql_overlay_df.iterrows():
                    prefix = ''
                    if row['Status'] == 'Added':
                        prefix = f"+ (Line {row['LineNum2']}) "
                        html_lines.append(f"<span style='color: #006100; background-color: #C6EFCE;'>{prefix}{row['Line']}</span>")
                    elif row['Status'] == 'Removed':
                        prefix = f"- (Line {row['LineNum1']}) "
                        html_lines.append(f"<span style='color: #9C0006; background-color: #FFC7CE;'>{prefix}{row['Line']}</span>")
                    else:
                        prefix = f"  (Line {row['LineNum1']}) "
                        html_lines.append(f"<span>{prefix}{row['Line']}</span>")
                st.markdown("<br>".join(html_lines), unsafe_allow_html=True)
    else:
        st.warning("Please upload both CSV files.")