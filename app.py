import streamlit as st
import pandas as pd
from utils.data_loader import load_toss_data, load_naver_data
from utils.data_processor import process_and_merge_data
from utils.visualizer import (
    create_kpi_metrics, create_daily_sales_chart, create_heatmap,
    create_peak_hours_analysis, create_day_of_week_analysis,
    create_platform_comparison, create_transaction_distribution,
    create_trend_analysis
)

st.set_page_config(page_title="Toss & Naver Sales Analysis", layout="wide")

st.title("📊 Toss & Naver Smart Place Sales Analysis")

with st.sidebar:
    st.header("📁 데이터 업로드")

    st.subheader("토스 POS 데이터")
    st.caption("토스에서 다운로드한 '매출리포트' 엑셀 파일을 업로드하세요.")
    toss_file = st.file_uploader("토스 엑셀 파일 업로드", type=['xlsx', 'xls'])
    toss_password = st.text_input(
        "토스 파일 비밀번호",
        type="password",
        max_chars=4,
        help="토스에서 받은 4자리 숫자 비밀번호",
        placeholder="4자리 숫자"
    )

    st.subheader("네이버 스마트플레이스 데이터")
    st.caption("네이버 예약에서 다운로드한 '예약자관리' 엑셀 파일을 업로드하세요.")
    naver_file = st.file_uploader("네이버 엑셀 파일 업로드", type=['xlsx', 'xls'])
    naver_password = st.text_input(
        "네이버 파일 비밀번호",
        type="password",
        help="네이버 아이디를 입력하세요 (비밀번호로 사용됨)",
        placeholder="네이버 아이디"
    )

    analyze_btn = st.button("📊 매출 분석 시작", type="primary")

if analyze_btn:
    if not toss_file or not naver_file:
        st.error("토스와 네이버 엑셀 파일을 모두 업로드해주세요.")
    elif not toss_password or not naver_password:
        st.error("두 파일의 비밀번호를 모두 입력해주세요.")
    else:
        try:
            with st.spinner("파일 복호화 및 처리 중..."):
                # Load Data
                df_toss = load_toss_data(toss_file, toss_password)
                df_naver = load_naver_data(naver_file, naver_password)
                
                # Process & Merge
                df_merged = process_and_merge_data(df_toss, df_naver)
                
                st.success("데이터 처리 완료!")
                
                # Visualizations
                st.markdown("---")
                create_kpi_metrics(df_merged)
                
                st.markdown("### 📈 일별 매출 추이")
                create_daily_sales_chart(df_merged)
                
                st.markdown("### 🔥 매출 히트맵 (30분 단위)")
                create_heatmap(df_merged)

                st.markdown("---")
                st.markdown("### ⏰ 시간대별 분석")
                create_peak_hours_analysis(df_merged)

                st.markdown("---")
                st.markdown("### 📅 요일별 분석")
                create_day_of_week_analysis(df_merged)

                st.markdown("---")
                st.markdown("### 🔄 플랫폼 비교 분석")
                create_platform_comparison(df_merged)

                st.markdown("---")
                st.markdown("### 💳 거래 분포 분석")
                create_transaction_distribution(df_merged)

                st.markdown("---")
                st.markdown("### 📊 트렌드 분석")
                create_trend_analysis(df_merged)

                with st.expander("원본 데이터 보기"):
                    st.dataframe(df_merged)
                    
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
