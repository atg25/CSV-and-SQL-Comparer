# CSV & SQL Comparison Tool

This app lets you compare two CSV files (and optionally two SQL files) with a user-friendly web interface. It auto-suggests the best key columns, highlights differences, and lets you download the results as an Excel file.

## Quick Start (For Beginners)

### 1. Install Python

- Download Python 3.8 or newer from https://www.python.org/downloads/
- **IMPORTANT:** Check the box to "Add Python to PATH" during installation.

### 2. Download the Project

- Download the ZIP from GitHub and unzip it to a folder on your computer.

### 3. Open a Terminal/Command Prompt

- On Windows: Open Command Prompt or PowerShell.
- On Mac/Linux: Open Terminal.

### 4. Navigate to the Project Folder

```
cd path/to/unzipped/folder
```

### 5. (Recommended) Create and Activate a Virtual Environment

- **Windows (Command Prompt):**
  ```
  python -m venv venv
  venv\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```
  python -m venv venv
  venv\Scripts\Activate.ps1
  ```
- **Mac/Linux:**
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```

### 6. Upgrade pip

```
pip install --upgrade pip
```

### 7. Install Required Packages

```
pip install -r requirements.txt
```

If you get an error about `requirements.txt` missing, run:

```
pip install streamlit pandas openpyxl
```

### 8. Run the App

```
streamlit run data_comp_app.py
```

If you get "command not found: streamlit", try:

```
python -m streamlit run data_comp_app.py
```

### 9. Open the App

- Streamlit will print a local URL (e.g., http://localhost:8501). Open it in your web browser.

### 10. Use the App

- Upload your CSV and SQL files as prompted.
- Download the results as needed.

---

## FAQ

- **Are my files sent to the cloud?**

  - If you run the app locally, your files stay on your computer and are not uploaded anywhere.
  - If you deploy the app to Streamlit Cloud or another server, files are processed on that server.

- **Trouble with Python not found?**

  - Re-run the Python installer and check "Add Python to PATH".

- **Need help?**
  - Open an issue on GitHub or ask your team for help!
