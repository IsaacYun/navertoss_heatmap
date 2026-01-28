import streamlit as st
import pandas as pd
from utils.data_loader import load_toss_data, load_naver_data
from utils.data_processor import process_and_merge_data
from utils.visualizer import create_kpi_metrics, create_daily_sales_chart, create_heatmap

st.set_page_config(page_title="Toss & Naver Sales Analysis", layout="wide")

st.title("📊 Toss & Naver Smart Place Sales Analysis")

with st.sidebar:
    st.header("Upload Data")
    
    st.subheader("Toss POS Data")
    toss_file = st.file_uploader("Upload Toss Excel File", type=['xlsx', 'xls'])
    toss_password = st.text_input("Toss File Password", type="password", max_chars=4)
    
    st.subheader("Naver Smart Place Data")
    naver_file = st.file_uploader("Upload Naver Excel File", type=['xlsx', 'xls'])
    naver_password = st.text_input("Naver ID (Password)", type="password")
    
    analyze_btn = st.button("Analyze Sales Data")

if analyze_btn:
    if not toss_file or not naver_file:
        st.error("Please upload both Toss and Naver Excel files.")
    elif not toss_password or not naver_password:
        st.error("Please enter passwords for both files.")
    else:
        try:
            with st.spinner("Decrypting and processing files..."):
                # Load Data
                df_toss = load_toss_data(toss_file, toss_password)
                df_naver = load_naver_data(naver_file, naver_password)
                
                # Process & Merge
                df_merged = process_and_merge_data(df_toss, df_naver)
                
                st.success("Data processed successfully!")
                
                # Visualizations
                st.markdown("---")
                create_kpi_metrics(df_merged)
                
                st.markdown("### 📈 Daily Sales Trend")
                create_daily_sales_chart(df_merged)
                
                st.markdown("### 🔥 Sales Heatmap (30-min intervals)")
                create_heatmap(df_merged)
                
                with st.expander("View Raw Data"):
                    st.dataframe(df_merged)
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
