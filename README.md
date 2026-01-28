# Toss & Naver Smart Place Sales Analysis Dashboard

This is a local Streamlit web application that analyzes sales data from Toss POS and Naver Smart Place.

## Features
- **Secure File Loading**: Supports password-protected Excel files.
- **Data Merging**: Combines Field sales (Toss) and Reservation sales (Naver).
- **Interactive Dashboard**:
    - Total Sales & Platform Breakdown
    - Daily Sales Trends
    - **30-Minute Sales Heatmap** (to identify peak hours)

## Installation

1.  Open your terminal.
2.  Navigate to the project folder:
    ```bash
    cd toss_naver_analysis
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  Run the application:
    ```bash
    streamlit run app.py
    ```
2.  A new tab will open in your browser (usually at `http://localhost:8501`).
3.  Upload your **Toss Excel File** and **Naver Excel File**.
4.  Enter the password for the Toss file and your Naver ID for the Naver file.
5.  Click **Analyze Sales Data**.

## Troubleshooting
- **Decryption Failed**: Ensure you entered the correct 4-digit password for Toss and your Naver ID for Naver.
- **Column Not Found**: The app expects standard Korean column names (e.g., `결제일시`, `결제금액`). If your Excel file layout is different, let me know.
