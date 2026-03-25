import streamlit as st
import plotly.express as px
from streamlit_plotly_events import plotly_events
import plotly.graph_objects as go
import pandas as pd

def create_kpi_metrics(df):
    """Displays key performance indicators."""
    total_sales = df['amount'].sum()

    # Group by source
    sales_by_source = df.groupby('source')['amount'].sum()
    toss_sales = sales_by_source.get('Toss (Field)', 0)
    naver_sales = sales_by_source.get('Naver (Reservation)', 0)

    # 확장 KPI 계산
    transaction_count = len(df)
    avg_transaction = total_sales / transaction_count if transaction_count > 0 else 0
    toss_ratio = (toss_sales / total_sales * 100) if total_sales > 0 else 0
    naver_ratio = (naver_sales / total_sales * 100) if total_sales > 0 else 0

    # 1행: 매출 관련 KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 총 매출", f"{total_sales:,.0f} 원")
    col2.metric("📱 토스 매출 (현장)", f"{toss_sales:,.0f} 원")
    col3.metric("🌐 네이버 매출 (예약)", f"{naver_sales:,.0f} 원")

    # 2행: 거래 분석 KPI
    col4, col5, col6 = st.columns(3)
    col4.metric("🧾 총 거래 건수", f"{transaction_count:,} 건")
    col5.metric("💵 평균 객단가", f"{avg_transaction:,.0f} 원")
    col6.metric("📊 플랫폼 비중", f"토스 {toss_ratio:.1f}% / 네이버 {naver_ratio:.1f}%")

def create_daily_sales_chart(df):
    """Creates a line chart for daily sales."""
    # Resample to Daily
    daily_sales = df.set_index('datetime').resample('D')['amount'].sum().reset_index()
    
    fig = px.line(daily_sales, x='datetime', y='amount', 
                  title='Daily Sales Trend',
                  labels={'amount': '매출 (원)', 'datetime': 'Date'})
    
    # Update y-axis to show full numbers with commas (no 'k')
    fig.update_yaxes(tickformat=",d")
    
    st.plotly_chart(fig, use_container_width=True)

def create_heatmap(df, focus_day=None, focus_time=None):
    """Creates a heatmap for 30-min intervals."""
    # Ensure all days are present for correct sorting
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # 1. Prepare Data for Total Sales (Sum)
    heatmap_data = df.groupby(['day_of_week', 'time_str'])['amount'].sum().reset_index()
    pivot_total = heatmap_data.pivot(index='day_of_week', columns='time_str', values='amount')
    pivot_total = pivot_total.reindex(days_order) # Ensure row order

    # 2. Prepare Data for Average Sales
    # Calculate unique dates per day of week to get "N Mondays", "N Tuesdays" etc.
    df['date'] = df['datetime'].dt.date
    day_counts = df.groupby('day_of_week')['date'].nunique()

    # Create a matching pivot table for Averages
    pivot_avg = pivot_total.copy()
    for day in days_order:
        if day in pivot_total.index and day in day_counts.index:
            count = day_counts[day]
            if count > 0:
                pivot_avg.loc[day] = pivot_total.loc[day] / count
            else:
                pivot_avg.loc[day] = 0

    # 2b. Prepare Data for Median Sales (all dates x all time_strs)
    all_dates = df['date'].unique()
    all_times = df['time_str'].unique()
    grid = pd.MultiIndex.from_product([all_dates, all_times], names=['date', 'time_str']).to_frame(index=False)
    
    daily_sum = df.groupby(['date', 'time_str'])['amount'].sum().reset_index()
    full_daily = grid.merge(daily_sum, on=['date', 'time_str'], how='left').fillna({'amount': 0})
    
    # date -> day_of_week 매핑
    date_to_dow = df[['date', 'day_of_week']].drop_duplicates()
    full_daily = full_daily.merge(date_to_dow, on='date', how='left')

    heatmap_median = full_daily.groupby(['day_of_week', 'time_str'])['amount'].median().reset_index()
    pivot_median = heatmap_median.pivot(index='day_of_week', columns='time_str', values='amount')
    pivot_median = pivot_median.reindex(days_order)
    pivot_median = pivot_median.reindex(columns=pivot_total.columns)  # align columns
    
    # 3. Handle Zeros (Transparent) and NaNs
    pivot_total = pivot_total.replace(0, pd.NA)
    
    # 4. Create Custom Y-axis Labels with Stats (Days)
    day_totals = df.groupby('day_of_week')['amount'].sum()
    # 일별 총매출의 중간값: 날짜별 합산 후 요일 그룹의 중간값
    daily_by_day = df.groupby(['day_of_week', 'date'])['amount'].sum().reset_index()
    day_medians = daily_by_day.groupby('day_of_week')['amount'].median()
    y_labels = []
    for day in pivot_total.index:
        if day in day_totals.index and day in day_counts.index:
            total = day_totals[day]
            count = day_counts[day]
            avg = total / count if count > 0 else 0
            med = day_medians.get(day, 0)
            label = f"{day}<br><span style='font-size:10px'>(T:{total:,.0f}/A:{avg:,.0f}/M:{med:,.0f})</span>"
        else:
            label = day
        y_labels.append(label)

    # 5. Create Custom X-axis Labels with Stats (Times)
    time_totals = df.groupby('time_str')['amount'].sum()
    # 전체 일자(full_daily) 기준 시간대별 중간값 계산 (매출 0원인 날 포함)
    time_medians = full_daily.groupby('time_str')['amount'].median()
    # For time average: Total Sales at Time T / Total Unique Dates in dataset
    total_days = len(all_dates)

    x_labels = []
    for t in pivot_total.columns:
        if t in time_totals.index:
            total = time_totals[t]
            avg = total / total_days if total_days > 0 else 0
            med = time_medians[t]
            # Label format: "12:00 (T:... / A:... / M:...)" - Single line for better vertical rotation
            label = f"{t} (T:{total:,.0f} / A:{avg:,.0f} / M:{med:,.0f})"
        else:
            label = t
        x_labels.append(label)

    # 6. Build Heatmap — stack avg + median as customdata
    import numpy as np
    # NaN → 0 으로 채워서 customdata 포맷 오류 방지
    avg_vals = pivot_avg.fillna(0).values
    med_vals = pivot_median.fillna(0).values
    # customdata shape: (rows, cols, 2)  → [avg, median]
    custom = np.stack([avg_vals, med_vals], axis=-1)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_total.values,
        x=x_labels,
        y=y_labels,
        customdata=custom,
        colorscale='Greens',
        xgap=1,
        ygap=1,
        hovertemplate=(
            "<b>%{y}</b><br>Time: %{x}<br><br>" +
            "시간대 총 매출: %{z:,.0f} 원<br>" +
            "일평균 매출: %{customdata[0]:,.0f} 원<br>" +
            "중간값:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; %{customdata[1]:,.0f} 원<br>" +
            "<extra></extra>"
        ),
        hoverongaps=False,
    ))

    fig.update_layout(
        xaxis_side="top",
        height=700,
        margin=dict(t=300, b=50, l=50, r=50),
        xaxis=dict(
            tickangle=-90,
            tickfont=dict(size=10),
            fixedrange=True,   # 줌/패닝 비활성화
        ),
        yaxis=dict(
            fixedrange=True,   # 줌/패닝 비활성화
        ),
        coloraxis_colorbar=dict(
            title="매출 (원)",
            tickformat=",d"
        ),
        dragmode=False,        # 드래그로 줌 선택 비활성화
    )

    # Update colorbar format manually since we are using go.Heatmap not px
    fig.update_traces(colorbar_tickformat=",d")

    # 포커스된 셀이 있다면 빨간색 테두리를 그립니다.
    if focus_day and focus_time:
        # y_labels 중 focus_day로 시작하는 것 찾기 (예: 'Mon'으로 시작하는 라벨)
        y_idx = next((i for i, l in enumerate(y_labels) if l.startswith(focus_day)), None)
        # x_labels 중 focus_time으로 시작하는 것 찾기 (예: '12:00'로 시작하는 라벨)
        x_idx = next((i for i, l in enumerate(x_labels) if str(l).startswith(focus_time)), None)
        
        if y_idx is not None and x_idx is not None:
            fig.add_shape(
                type="rect",
                x0=x_idx - 0.5,
                x1=x_idx + 0.5,
                y0=y_idx - 0.5,
                y1=y_idx + 0.5,
                line={"color": "red", "width": 3},
                fillcolor="rgba(0,0,0,0)",
                layer="above"
            )

    # plotly_events로 클릭 이벤트 감지
    clicked = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_width="100%",
        override_height=720,
        key="heatmap_click",
    )

    # 클릭 된 셀 디코딩
    selected_day, selected_time = None, None
    if clicked:
        pt = clicked[0]
        raw_y = str(pt.get("y", ""))
        raw_x = str(pt.get("x", ""))
        # y_label: "Mon<br><span style='font-size:10px'>..." → "Mon"
        selected_day = raw_y.split("<")[0].strip()
        # x_label: "12:00 (T:... / A:... / M:...)" → "12:00"
        selected_time = raw_x.split(" ")[0].strip()

    return selected_day, selected_time


def create_heatmap_drilldown(df, selected_day, selected_time):
    """Drilldown: 선택된 (요일 x 30분 시간대)의 일별 매출 바 차트"""
    days_korean = {'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일'}
    day_kr = days_korean.get(selected_day, selected_day)

    st.markdown(f"#### 📍 `{day_kr}요일 {selected_time}` 시간대 — 일별 매출")

    mask = (df['day_of_week'] == selected_day) & (df['time_str'] == selected_time)
    df_cell = df[mask].copy()

    # 전체 데이터에서 해당 요일에 속하는 모든 날짜 리스트 확보
    all_dates_for_day = df[df['day_of_week'] == selected_day]['date'].unique()

    if len(all_dates_for_day) == 0:
        st.info("해당 기간 내에 이 요일의 데이터가 존재하지 않습니다.")
        return

    # 해당 셀(시간대)의 일별 매출 합산
    daily = df_cell.groupby('date')['amount'].sum().reset_index()

    # 모든 해당 요일의 날짜와 병합하여 매출이 없는 날은 0으로 처리
    all_dates_df = pd.DataFrame({'date': all_dates_for_day})
    daily = all_dates_df.merge(daily, on='date', how='left').fillna({'amount': 0}).sort_values('date')
    daily['date_str'] = daily['date'].astype(str)

    # 요약 지표 (st.metric 대신 작게 표시하여 좁은 공간에서도 깨짐 방지)
    total = daily['amount'].sum()
    avg   = daily['amount'].mean()
    med   = daily['amount'].median()
    
    html_metrics = f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <div style="flex: 1; padding: 10px; background-color: rgba(128,128,128,0.1); border-radius: 8px;">
            <div style="font-size: 12px; color: gray;">합계</div>
            <div style="font-size: 16px; font-weight: bold;">{total:,.0f}원</div>
        </div>
        <div style="flex: 1; padding: 10px; background-color: rgba(128,128,128,0.1); border-radius: 8px;">
            <div style="font-size: 12px; color: gray;">평균</div>
            <div style="font-size: 16px; font-weight: bold;">{avg:,.0f}원</div>
        </div>
        <div style="flex: 1; padding: 10px; background-color: rgba(128,128,128,0.1); border-radius: 8px;">
            <div style="font-size: 12px; color: gray;">중간값</div>
            <div style="font-size: 16px; font-weight: bold;">{med:,.0f}원</div>
        </div>
    </div>
    """
    st.markdown(html_metrics, unsafe_allow_html=True)

    fig = px.bar(
        daily,
        x='date_str',
        y='amount',
        text='amount',
        labels={'date_str': '날짜', 'amount': '매출 (원)'},
        title=f"{day_kr}요일 {selected_time} 시간대 일별 매출",
        color_discrete_sequence=['#4CAF50']
    )
    fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside',
        cliponaxis=False
    )
    # y축 상단에 여백을 조금 더 줍니다 (텍스트 잘림 방지)
    fig.update_yaxes(tickformat=",d", fixedrange=True, rangemode='tozero', range=[0, daily['amount'].max() * 1.25] if daily['amount'].max() > 0 else [0, 1])
    fig.update_xaxes(type='category', tickangle=-45, fixedrange=True)  # 연속된 날짜 공백 방지
    fig.update_layout(showlegend=False, margin=dict(t=80, b=80), dragmode=False, height=350)
    
    st.caption("👉 막대를 클릭하면 개별 거래내역(시간/분)이 하단에 표시됩니다.")

    clicked = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_width="100%",
        override_height=300,
        key=f"drilldown_click_{selected_day}_{selected_time}"
    )

    if clicked:
        selected_date = str(clicked[0].get("x"))
        st.markdown(f"##### 🕒 {selected_date} 개별 거래 내역")
        
        mask_date = df_cell['date'].astype(str) == selected_date
        detail_df = df_cell[mask_date].copy()
        
        if not detail_df.empty:
            if 'order_id' in detail_df.columns:
                # 토스와 네이버의 주문번호가 우연히 겹치는 것을 방지
                detail_df['uid'] = detail_df['source'] + "_" + detail_df['order_id'].astype(str)
                grouped = detail_df.groupby('uid', as_index=False).agg({
                    'datetime': 'first',
                    'source': 'first',
                    'amount': 'sum'
                })
                detail_df = grouped
                
            detail_df = detail_df.sort_values('datetime')
            detail_df['time_display'] = detail_df['datetime'].dt.strftime('%H:%M:%S')
            detail_df['amount_display'] = detail_df['amount'].apply(lambda x: f"{x:,.0f}원")
            show_df = detail_df[['time_display', 'source', 'amount_display']].rename(columns={
                'time_display': '결제 시간',
                'source': '출처 (결제수단)',
                'amount_display': '합계 금액'
            })
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.info("결제(매출) 내역이 없습니다. (0원)")


def create_peak_hours_analysis(df):
    """피크 시간대 Top 10 (요일+시간) 및 시간대별 평균 객단가 분석"""
    df = df.copy()
    df['hour'] = df['datetime'].dt.hour
    days_korean = {'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일'}

    # 요일+시간대별 매출 합계
    day_hour_sales = df.groupby(['day_of_week', 'hour']).agg(
        매출=('amount', 'sum'),
        건수=('amount', 'count'),
        객단가=('amount', 'mean')
    ).reset_index()
    day_hour_sales = day_hour_sales.sort_values('매출', ascending=False)
    top10 = day_hour_sales.head(10)

    # 시간대별 평균 객단가 (요일 무관)
    hourly_avg = df.groupby('hour')['amount'].mean()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏆 피크 시간대 Top 10 (요일+시간)")
        for rank, (_, row) in enumerate(top10.iterrows(), 1):
            day_kr = days_korean.get(row['day_of_week'], row['day_of_week'])
            hour = int(row['hour'])
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}위**"
            st.markdown(
                f"{emoji} **{day_kr}요일 {hour:02d}:00~{hour+1:02d}:00** | "
                f"**{row['매출']:,.0f}원** ({int(row['건수'])}건, 객단가 {row['객단가']:,.0f}원)"
            )

    with col2:
        # 시간대별 평균 객단가 차트
        fig = px.bar(
            x=hourly_avg.index,
            y=hourly_avg.values,
            title="시간대별 평균 객단가",
            labels={'x': '시간', 'y': '평균 객단가 (원)'}
        )
        fig.update_xaxes(tickmode='linear', dtick=1)
        fig.update_yaxes(tickformat=",d")
        fig.update_traces(marker_color='#FF6B6B')
        st.plotly_chart(fig, use_container_width=True)


def create_day_of_week_analysis(df):
    """요일별 매출 분석 및 주중/주말 비교"""
    df = df.copy()
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    days_korean = {'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일'}

    # 요일별 집계
    daily_stats = df.groupby('day_of_week').agg(
        매출=('amount', 'sum'),
        건수=('amount', 'count'),
        객단가=('amount', 'mean')
    ).reindex(days_order)

    daily_stats['요일'] = [days_korean[d] for d in daily_stats.index]

    col1, col2 = st.columns(2)

    with col1:
        # 요일별 매출 바 차트
        colors = ['#4ECDC4' if d in ['Sat', 'Sun'] else '#45B7D1' for d in days_order]
        fig = px.bar(
            x=[days_korean[d] for d in days_order],
            y=daily_stats['매출'].values,
            title="요일별 총 매출",
            labels={'x': '요일', 'y': '매출 (원)'}
        )
        fig.update_traces(marker_color=colors)
        fig.update_yaxes(tickformat=",d")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 주중 vs 주말 비교
        weekday_mask = df['day_of_week'].isin(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
        weekend_mask = df['day_of_week'].isin(['Sat', 'Sun'])

        weekday_sales = df[weekday_mask]['amount'].sum()
        weekend_sales = df[weekend_mask]['amount'].sum()
        weekday_count = len(df[weekday_mask])
        weekend_count = len(df[weekend_mask])
        weekday_avg = df[weekday_mask]['amount'].mean() if weekday_count > 0 else 0
        weekend_avg = df[weekend_mask]['amount'].mean() if weekend_count > 0 else 0

        st.markdown("#### 📊 주중 vs 주말 비교")

        comparison_data = pd.DataFrame({
            '구분': ['주중 (월~금)', '주말 (토~일)'],
            '총 매출': [weekday_sales, weekend_sales],
            '거래 건수': [weekday_count, weekend_count],
            '평균 객단가': [weekday_avg, weekend_avg]
        })

        for _, row in comparison_data.iterrows():
            st.markdown(f"**{row['구분']}**")
            st.markdown(f"- 매출: **{row['총 매출']:,.0f}원** | 건수: **{row['거래 건수']:,}건** | 객단가: **{row['평균 객단가']:,.0f}원**")


def create_platform_comparison(df):
    """플랫폼별 시간대/요일 비교 분석"""
    df = df.copy()
    df['hour'] = df['datetime'].dt.hour
    days_korean = {'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일'}
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    col1, col2 = st.columns(2)

    with col1:
        # 시간대별 플랫폼 비중
        hourly_platform = df.groupby(['hour', 'source'])['amount'].sum().unstack(fill_value=0)
        hourly_platform_pct = hourly_platform.div(hourly_platform.sum(axis=1), axis=0) * 100

        fig = go.Figure()
        colors = {'Toss (Field)': '#1E88E5', 'Naver (Reservation)': '#43A047'}

        for source in hourly_platform_pct.columns:
            fig.add_trace(go.Bar(
                name=source.replace('Toss (Field)', '토스 (현장)').replace('Naver (Reservation)', '네이버 (예약)'),
                x=hourly_platform_pct.index,
                y=hourly_platform_pct[source],
                marker_color=colors.get(source, '#888')
            ))

        fig.update_layout(
            barmode='stack',
            title="시간대별 플랫폼 비중",
            xaxis_title="시간",
            yaxis_title="비중 (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        fig.update_xaxes(tickmode='linear', dtick=2)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 요일별 플랫폼 비중
        daily_platform = df.groupby(['day_of_week', 'source'])['amount'].sum().unstack(fill_value=0)
        daily_platform = daily_platform.reindex(days_order)
        daily_platform_pct = daily_platform.div(daily_platform.sum(axis=1), axis=0) * 100

        fig = go.Figure()

        for source in daily_platform_pct.columns:
            fig.add_trace(go.Bar(
                name=source.replace('Toss (Field)', '토스 (현장)').replace('Naver (Reservation)', '네이버 (예약)'),
                x=[days_korean[d] for d in daily_platform_pct.index],
                y=daily_platform_pct[source],
                marker_color=colors.get(source, '#888')
            ))

        fig.update_layout(
            barmode='stack',
            title="요일별 플랫폼 비중",
            xaxis_title="요일",
            yaxis_title="비중 (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)


def create_transaction_distribution(df):
    """거래 금액 분포 분석"""
    df = df.copy()

    col1, col2 = st.columns(2)

    with col1:
        # 객단가 분포 히스토그램
        fig = px.histogram(
            df,
            x='amount',
            nbins=30,
            title="거래 금액 분포",
            labels={'amount': '거래 금액 (원)', 'count': '건수'}
        )
        fig.update_traces(marker_color='#9C27B0')
        fig.update_xaxes(tickformat=",d")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 거래 금액 구간별 비중
        bins = [0, 10000, 30000, 50000, 100000, float('inf')]
        labels = ['1만원 미만', '1~3만원', '3~5만원', '5~10만원', '10만원 이상']

        df['price_range'] = pd.cut(df['amount'], bins=bins, labels=labels, right=False)
        range_stats = df.groupby('price_range', observed=True).agg(
            건수=('amount', 'count'),
            매출=('amount', 'sum')
        )
        range_stats['비중'] = range_stats['건수'] / range_stats['건수'].sum() * 100

        fig = px.pie(
            values=range_stats['건수'].values,
            names=range_stats.index,
            title="거래 금액 구간별 비중",
            color_discrete_sequence=px.colors.sequential.Purples_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        # 구간별 상세 테이블
        st.markdown("**구간별 상세**")
        for idx, row in range_stats.iterrows():
            st.markdown(f"- {idx}: **{row['건수']:,}건** ({row['비중']:.1f}%) | 매출 {row['매출']:,.0f}원")


def create_trend_analysis(df):
    """트렌드 분석 (추세선 + 이동평균)"""
    df = df.copy()

    # 일별 매출 집계
    daily_sales = df.set_index('datetime').resample('D')['amount'].sum().reset_index()
    daily_sales.columns = ['date', 'sales']

    # 7일 이동평균 계산
    daily_sales['ma7'] = daily_sales['sales'].rolling(window=7, min_periods=1).mean()

    # 추세선 계산 (선형 회귀)
    import numpy as np
    x = np.arange(len(daily_sales))
    y = daily_sales['sales'].values
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    daily_sales['trend'] = p(x)

    # 추세 방향 판단
    trend_direction = "상승 📈" if z[0] > 0 else "하락 📉"
    daily_change = z[0]  # 일일 변화량

    fig = go.Figure()

    # 실제 매출
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['sales'],
        mode='lines+markers',
        name='일별 매출',
        line=dict(color='#2196F3', width=2),
        marker=dict(size=6)
    ))

    # 7일 이동평균
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['ma7'],
        mode='lines',
        name='7일 이동평균',
        line=dict(color='#FF9800', width=3, dash='solid')
    ))

    # 추세선
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['trend'],
        mode='lines',
        name=f'추세선 ({trend_direction})',
        line=dict(color='#E91E63', width=2, dash='dash')
    ))

    fig.update_layout(
        title=f"매출 트렌드 분석 (추세: {trend_direction}, 일 평균 {abs(daily_change):,.0f}원 {'증가' if daily_change > 0 else '감소'})",
        xaxis_title="날짜",
        yaxis_title="매출 (원)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode='x unified'
    )
    fig.update_yaxes(tickformat=",d")

    st.plotly_chart(fig, use_container_width=True)
