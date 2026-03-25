import streamlit as st
import pandas as pd
from utils.data_loader import load_toss_data, load_naver_data, load_toss_discount_data
from utils.data_processor import process_and_merge_data
from utils.visualizer import (
    create_kpi_metrics, create_daily_sales_chart, create_heatmap,
    create_heatmap_drilldown, create_peak_hours_analysis, 
    create_day_of_week_analysis, create_platform_comparison, 
    create_transaction_distribution, create_trend_analysis
)

# --- 초기화 (최상단) ---
if 'heatmap_selected_day' not in st.session_state:
    st.session_state.heatmap_selected_day = None
if 'heatmap_selected_time' not in st.session_state:
    st.session_state.heatmap_selected_time = None

st.set_page_config(
    page_title="Toss & Naver Sales Analysis", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

# ── 버튼 클릭 시 데이터 로드 & session_state에 저장 ────────────────────────
if analyze_btn:
    if not toss_file or not naver_file:
        st.error("토스와 네이버 엑셀 파일을 모두 업로드해주세요.")
    elif not toss_password or not naver_password:
        st.error("두 파일의 비밀번호를 모두 입력해주세요.")
    else:
        try:
            with st.spinner("파일 복호화 및 처리 중..."):
                df_toss = load_toss_data(toss_file, toss_password)
                df_naver = load_naver_data(naver_file, naver_password)
                df_merged = process_and_merge_data(df_toss, df_naver)
                
                # 추가: 아이스크림 품목 등 할인 내역 조회
                df_discount = load_toss_discount_data(toss_file, toss_password)

            st.session_state['df_merged'] = df_merged
            st.session_state['df_discount'] = df_discount
            st.success("데이터 처리 완료!")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
            st.session_state.pop('df_merged', None)
            st.session_state.pop('df_discount', None)

# ── session_state에 데이터가 있을 때 항상 시각화 (날짜 변경 후 재실행에도 유지) ──
if 'df_merged' in st.session_state:
    df_merged = st.session_state['df_merged']
    df_discount = st.session_state.get('df_discount', pd.DataFrame())

    # 데이터 범위 배너
    toss_min = df_merged[df_merged['source'] == 'Toss (Field)']['datetime'].min()
    toss_max = df_merged[df_merged['source'] == 'Toss (Field)']['datetime'].max()
    naver_min = df_merged[df_merged['source'] == 'Naver (Reservation)']['datetime'].min()
    naver_max = df_merged[df_merged['source'] == 'Naver (Reservation)']['datetime'].max()

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info(
            f"📱 **토스 데이터 범위**\n\n"
            f"{toss_min.strftime('%Y-%m-%d')} ~ {toss_max.strftime('%Y-%m-%d')}"
        )
    with info_col2:
        st.info(
            f"🌐 **네이버 데이터 범위**\n\n"
            f"{naver_min.strftime('%Y-%m-%d')} ~ {naver_max.strftime('%Y-%m-%d')}"
        )

    # 조회 기간 필터
    import datetime
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    overall_min = df_merged['datetime'].min().date()
    overall_max = df_merged['datetime'].max().date()

    st.markdown(f"#### 📅 조회 기간 설정 (오늘: **{today_str}**)")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        start_date = st.date_input(
            "시작일",
            value=overall_min,
            min_value=overall_min,
            max_value=overall_max,
            key="start_date"
        )
    with filter_col2:
        end_date = st.date_input(
            "종료일",
            value=overall_max,
            min_value=overall_min,
            max_value=overall_max,
            key="end_date"
        )

    if start_date > end_date:
        st.warning("시작일이 종료일보다 늦을 수 없습니다.")
    else:
        mask = (df_merged['datetime'].dt.date >= start_date) & \
               (df_merged['datetime'].dt.date <= end_date)
        df = df_merged[mask].copy()

        if df.empty:
            st.warning("선택한 기간에 데이터가 없습니다.")
        else:
            st.caption(f"🔎 조회 기간: {start_date} ~ {end_date} | 총 {len(df):,}건")

            st.markdown("---")
            
            # 아이스크림 할인 상품 상단 노출
            if not df_discount.empty:
                st.markdown("### 🍦 아이스크림 상품 할인 내역")
                st.caption(f"토스 포스 시스템에 '상품할인'이 적용된 아이스크림 카테고리 내역입니다. (총 {len(df_discount)}건)")
                st.dataframe(df_discount, use_container_width=True, hide_index=True)
                st.markdown("---")
            
            create_kpi_metrics(df)

            st.markdown("### 📈 일별 매출 추이")
            create_daily_sales_chart(df)

            st.markdown("### 🔥 매출 히트맵")
            interval_choice = st.radio("조회 단위", ["30분", "1시간"], horizontal=True, key="heatmap_interval")
            
            df_heatmap = df.copy()
            if interval_choice == "1시간":
                df_heatmap['time_str'] = df_heatmap['time_60min']
            else:
                df_heatmap['time_str'] = df_heatmap['time_30min']
            
            st.caption("히트맵 셀을 클릭하면 우측에 해당 요일/시간대의 일별 매출 상세가 표시됩니다.")
            
            heatmap_col, detail_col = st.columns([7, 3])
            
            with heatmap_col:
                selected_day, selected_time = create_heatmap(
                    df_heatmap, 
                    st.session_state.heatmap_selected_day, 
                    st.session_state.heatmap_selected_time
                )

                # 새 셀이 클릭된 경우 (기존에 선택한 셀과 다르면) 상태 업데이트 후 재실행
                if selected_day and selected_time:
                    if (selected_day != st.session_state.heatmap_selected_day or 
                        selected_time != st.session_state.heatmap_selected_time):
                        st.session_state.heatmap_selected_day = selected_day
                        st.session_state.heatmap_selected_time = selected_time
                        st.rerun()

            with detail_col:
                # 선택된 셀이 있으면 드릴다운 표출
                if st.session_state.heatmap_selected_day and st.session_state.heatmap_selected_time:
                    create_heatmap_drilldown(
                        df_heatmap, 
                        st.session_state.heatmap_selected_day, 
                        st.session_state.heatmap_selected_time
                    )
                else:
                    st.info("👈 히트맵에서 특정 셀을 클릭하여 일별 매출 상세를 확인하세요.")

            st.markdown("---")
            st.markdown("### ⏰ 시간대별 분석")
            create_peak_hours_analysis(df)

            st.markdown("---")
            st.markdown("### 📅 요일별 분석")
            create_day_of_week_analysis(df)

            st.markdown("---")
            st.markdown("### 🔄 플랫폼 비교 분석")
            create_platform_comparison(df)

            st.markdown("---")
            st.markdown("### 💳 거래 분포 분석")
            create_transaction_distribution(df)

            st.markdown("---")
            st.markdown("### 📊 트렌드 분석")
            create_trend_analysis(df)

            with st.expander("원본 데이터 보기"):
                st.dataframe(df)
