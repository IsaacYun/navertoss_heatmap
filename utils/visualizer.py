import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_kpi_metrics(df):
    """Displays key performance indicators."""
    total_sales = df['amount'].sum()
    
    # Group by source
    sales_by_source = df.groupby('source')['amount'].sum()
    toss_sales = sales_by_source.get('Toss (Field)', 0)
    naver_sales = sales_by_source.get('Naver (Reservation)', 0)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"{total_sales:,.0f} KRW")
    col2.metric("Toss Sales (Field)", f"{toss_sales:,.0f} KRW")
    col3.metric("Naver Sales (Reservation)", f"{naver_sales:,.0f} KRW")

def create_daily_sales_chart(df):
    """Creates a line chart for daily sales."""
    # Resample to Daily
    daily_sales = df.set_index('datetime').resample('D')['amount'].sum().reset_index()
    
    fig = px.line(daily_sales, x='datetime', y='amount', 
                  title='Daily Sales Trend',
                  labels={'amount': 'Sales (KRW)', 'datetime': 'Date'})
    
    # Update y-axis to show full numbers with commas (no 'k')
    fig.update_yaxes(tickformat=",d")
    
    st.plotly_chart(fig, use_container_width=True)

def create_heatmap(df):
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
    
    # 3. Handle Zeros (Transparent) and NaNs
    pivot_total = pivot_total.replace(0, pd.NA)
    
    # 4. Create Custom Y-axis Labels with Stats (Days)
    day_totals = df.groupby('day_of_week')['amount'].sum()
    y_labels = []
    for day in pivot_total.index:
        if day in day_totals.index and day in day_counts.index:
            total = day_totals[day]
            count = day_counts[day]
            avg = total / count if count > 0 else 0
            label = f"{day}<br><span style='font-size:10px'>(T:{total:,.0f}/A:{avg:,.0f})</span>"
        else:
            label = day
        y_labels.append(label)

    # 5. Create Custom X-axis Labels with Stats (Times)
    time_totals = df.groupby('time_str')['amount'].sum()
    # For time average: Total Sales at Time T / Total Unique Dates in dataset
    total_days = df['date'].nunique()
    
    x_labels = []
    for t in pivot_total.columns:
        if t in time_totals.index:
            total = time_totals[t]
            avg = total / total_days if total_days > 0 else 0
            # Label format: "12:00<br>(Tot: ... / Avg: ...)"
            # Use shorter text to avoid clutter? "T: ... / A: ..."
            label = f"{t}<br><span style='font-size:9px'>(T:{total:,.0f}<br>A:{avg:,.0f})</span>"
        else:
            label = t
        x_labels.append(label)

    # 6. Build Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_total.values,
        x=x_labels, 
        y=y_labels, 
        customdata=pivot_avg.values, 
        colorscale='Greens',
        xgap=1, 
        ygap=1,
        hovertemplate=(
            "<b>%{y}</b><br>Time: %{x}<br><br>" +
            "시간대 총 매출: %{z:,.0f} KRW<br>" +
            "일평균 매출: %{customdata:,.0f} KRW<br>" +
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        title="Sales Heatmap (30-min intervals)",
        xaxis_side="top",
        coloraxis_colorbar=dict(
            title="Sales (KRW)",
            tickformat=",d"
        )
    )
    
    # Update colorbar format manually since we are using go.Heatmap not px
    fig.update_traces(colorbar_tickformat=",d")
    
    st.plotly_chart(fig, use_container_width=True)
