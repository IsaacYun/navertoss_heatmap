import pandas as pd

def process_and_merge_data(df_toss, df_naver):
    """
    Merges Toss and Naver data based on strict time matching or simple concatenation.
    Standardizes columns to: 'datetime', 'amount', 'source'
    Adds features for heatmap: 'day_of_week', 'hour', 'minute_30'
    """
    # 1. Label Sources
    df_toss = df_toss.copy()
    df_naver = df_naver.copy()
    
    df_toss['source'] = 'Toss (Field)'
    df_naver['source'] = 'Naver (Reservation)'
    
    # 2. Merge
    df_merged = pd.concat([df_toss, df_naver], axis=0, ignore_index=True)
    
    # 3. Datetime Conversion
    # Attempt to convert mixed formats if necessary
    df_merged['datetime'] = pd.to_datetime(df_merged['datetime'], errors='coerce')
    
    # Drop rows with invalid dates
    df_merged = df_merged.dropna(subset=['datetime'])
    
    # 4. Feature Engineering for Heatmap
    # Day of Week (0=Monday, 6=Sunday) -> Map to names
    days = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    df_merged['day_of_week_int'] = df_merged['datetime'].dt.dayofweek
    df_merged['day_of_week'] = df_merged['day_of_week_int'].map(days)
    
    # 30-min and 60-min Intervals
    df_merged['time_30min'] = df_merged['datetime'].dt.floor('30min').dt.strftime('%H:%M')
    df_merged['time_60min'] = df_merged['datetime'].dt.floor('60min').dt.strftime('%H:%M')
    
    # Default time_str
    df_merged['time_str'] = df_merged['time_30min']

    # Sort
    df_merged = df_merged.sort_values('datetime')
    
    return df_merged
