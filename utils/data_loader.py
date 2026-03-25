import pandas as pd
import msoffcrypto
import io
import streamlit as st
import sys

def decrypt_excel(file_buffer, password):
    """Decrypts a password-protected Excel file."""
    try:
        file_buffer.seek(0)
        office_file = msoffcrypto.OfficeFile(file_buffer)
        office_file.load_key(password=password)
        decrypted_workbook = io.BytesIO()
        office_file.decrypt(decrypted_workbook)
        return decrypted_workbook
    except Exception as e:
        # Check if the file is actually encrypted
        file_buffer.seek(0)
        try:
            # Try specific check or just let the caller handle fallback
            raise ValueError(f"비밀번호가 올바르지 않습니다. 토스: 4자리 숫자, 네이버: 네이버 아이디를 확인해주세요. (상세: {str(e)})")
        except:
            raise e

def find_header_row(df, keywords):
    """
    Searches for the header row index by looking for keywords in the first 50 rows.
    Returns the index and the row content if found, else None.
    """
    # Helper to clean string for comparison
    def clean(val):
        return str(val).replace(" ", "").strip()

    clean_keywords = [clean(k) for k in keywords]

    # Check the currently parsed columns first
    current_cols = [clean(c) for c in df.columns]
    if any(k in current_cols for k in clean_keywords):
        return -1 
        
    for i, row in df.head(50).iterrows():
        # Convert row values to string and clean
        row_values = [clean(val) for val in row.values]
        
        # Check if enough keywords are present in this row
        match_count = sum(1 for val in row_values if any(k in val for k in clean_keywords))
        
        # If we find at least one strong keyword match, assume it's the header
        if match_count >= 1: 
            return i
            
    return None

def parse_korean_datetime(date_str):
    """
    Parses datetime strings like:
    - Toss: '2026-01-28' (Date) + '14:30:00' (Time) -> Handled by pandas to_datetime directly usually
    - Naver: '2026-01-02 (금) 오전 11:35:22'
    """
    if pd.isna(date_str):
        return pd.NaT
    
    date_str = str(date_str).strip()
    
    # Naver Format: '2026-01-02 (금) 오전 11:35:22'
    # Remove day of week (금)
    import re
    date_str = re.sub(r'\([가-힣]\)', '', date_str) # Remove (금)
    
    # Handle AM/PM (오전/오후)
    is_pm = '오후' in date_str
    date_str = date_str.replace('오전', '').replace('오후', '').strip()
    
    # Fix for 'YY. M. D.' format (e.g., '26. 1. 2.')
    # If the string starts with a 2-digit number followed by a dot, assume it's Year (20xx)
    # Regex to match '26. ' at start
    match = re.match(r'^(\d{2})\.', date_str)
    if match:
        year_prefix = match.group(1)
        # Prepend '20' to make it '2026'
        date_str = '20' + date_str
    
    try:
        dt = pd.to_datetime(date_str)
        if is_pm and dt.hour < 12:
            dt = dt + pd.Timedelta(hours=12)
        elif not is_pm and dt.hour == 12: # 12 AM case
            dt = dt - pd.Timedelta(hours=12)
        return dt
    except:
        return pd.to_datetime(date_str, errors='coerce')


def normalize_columns(df, type_):
    """
    Standardizes column names.
    """
    # Helper: Normalize column names (strip spaces)
    df.columns = [str(c).replace(" ", "").strip() for c in df.columns]
    
    # 1. Dynamic Header Detection
    if type_ == 'toss':
        # Keywords (no spaces)
        keywords = ['결제기준일자', '결제시각', '결제금액', '결제상태', '승인구분', '결제일자']
        header_idx = find_header_row(df, keywords)
        
        print(f"[DEBUG] Found Header Index: {header_idx}")
        
        if header_idx is not None and header_idx != -1:
            new_header = df.iloc[header_idx]
            df = df.iloc[header_idx + 1:]
            df.columns = new_header
            df = df.reset_index(drop=True)
            # Re-normalize columns after resetting header
            df.columns = [str(c).replace(" ", "").strip() for c in df.columns]
            
        # Toss Specific Logic
        if '결제기준일자' in df.columns and '결제시각' in df.columns:
             # Drop metadata rows
             df = df.dropna(subset=['결제기준일자'])
             
             # Check if '결제시각' is already a datetime object or full string
             # Try converting '결제시각' directly first
             try:
                 df['datetime'] = pd.to_datetime(df['결제시각'], errors='coerce')
             except:
                 df['datetime'] = pd.NaT

             # Verify if we got valid dates. If mostly NaT, then try combining.
             # Check distinct valid values count
             valid_dates = df['datetime'].dropna()
             if valid_dates.empty:
                 # Fallback to combination if direct parse failed (e.g. if '결제시각' was just time "14:00:00")
                 def combine_toss_datetime_v2(row):
                    try:
                        d = str(row['결제기준일자']).split(' ')[0]
                        t = str(row['결제시각'])
                        if d == 'nan' or t == 'nan': return pd.NaT
                        return pd.to_datetime(f"{d} {t}", errors='coerce')
                    except:
                        return pd.NaT
                 df['datetime'] = df.apply(combine_toss_datetime_v2, axis=1)
             
             df = df.dropna(subset=['datetime'])
             
             status_col = '결제상태' if '결제상태' in df.columns else '승인구분'
             if status_col in df.columns:
                 df['amount'] = pd.to_numeric(df['결제금액'], errors='coerce').fillna(0)
                 cancel_mask = df[status_col].astype(str).str.contains('취소', na=False)
                 df.loc[cancel_mask, 'amount'] *= -1
             else:
                 df['amount'] = pd.to_numeric(df['결제금액'], errors='coerce').fillna(0)
             
             order_col = next((c for c in df.columns if '주문번호' in c), None)
             df['order_id'] = df[order_col].astype(str) if order_col else df.index.astype(str)
             return df[['datetime', 'amount', 'order_id']]

        elif '결제일자' in df.columns and '결제시간' in df.columns:
            def combine_toss_datetime(row):
                d = str(row['결제일자']).split(' ')[0]
                t = str(row['결제시간'])
                return pd.to_datetime(f"{d} {t}")

            df['datetime'] = df.apply(combine_toss_datetime, axis=1)
            
            if '승인구분' in df.columns:
                 df['amount'] = pd.to_numeric(df['결제금액'], errors='coerce').fillna(0)
                 cancel_mask = df['승인구분'].astype(str).str.contains('취소', na=False)
                 df.loc[cancel_mask, 'amount'] *= -1
            else:
                 df['amount'] = pd.to_numeric(df['결제금액'], errors='coerce').fillna(0)
                 
            order_col = next((c for c in df.columns if '주문번호' in c), None)
            df['order_id'] = df[order_col].astype(str) if order_col else df.index.astype(str)
            return df[['datetime', 'amount', 'order_id']]
        
        else:
             found_cols = list(df.columns)
             raise ValueError(f"토스 파일 형식 오류: '결제 상세내역' 시트가 있는지 확인해주세요. (발견된 컬럼: {found_cols})")

    elif type_ == 'naver':
         # Keywords (no spaces)
         keywords = ['결제(입금)일시', '총결제금액', '예약번호', '이용일시', '실결제금액']
         header_idx = find_header_row(df, keywords)
         
         if header_idx is not None and header_idx != -1:
            new_header = df.iloc[header_idx]
            df = df.iloc[header_idx + 1:]
            df.columns = new_header
            df = df.reset_index(drop=True)
            # Re-normalize
            df.columns = [str(c).replace(" ", "").strip() for c in df.columns]
            
         # Naver Specific Logic
         date_col = next((c for c in df.columns if '결제(입금)일시' in c or '이용일시' in c), None)
         amt_col = next((c for c in df.columns if '총결제금액' in c or '실결제금액' in c or '결제금액' in c), None)
         
         if date_col and amt_col:
             df['datetime'] = df[date_col].apply(parse_korean_datetime)
             df['amount'] = pd.to_numeric(df[amt_col], errors='coerce').fillna(0)
             
             order_col = next((c for c in df.columns if '예약번호' in c or '주문번호' in c), None)
             df['order_id'] = df[order_col].astype(str) if order_col else df.index.astype(str)
             
             refund_col = next((c for c in df.columns if '환불금액' in c), None)
             if refund_col:
                 refund = pd.to_numeric(df[refund_col], errors='coerce').fillna(0)
                 df['amount'] = df['amount'] - refund
                 
             return df[['datetime', 'amount', 'order_id']]
         else:
             raise ValueError(f"네이버 파일 형식 오류: 날짜/금액 컬럼을 찾을 수 없습니다. (발견된 컬럼: {list(df.columns)})")

    return df

def load_toss_data(file, password):
    """
    Loads Toss POS Excel data with decryption.
    Checks all sheets for transaction data.
    """
    # Reset pointer
    file.seek(0)
    
    decrypted_file = None
    try:
        decrypted_file = decrypt_excel(file, password)
    except:
        file.seek(0) # Try reading directly if not encrypted
        
    source_file = decrypted_file if decrypted_file else file

    # Read all sheets with HEADER=NONE to treat everything as data
    try:
        # header=None is critical to prevent Pandas from picking the 'Summary' row as header
        sheets_dict = pd.read_excel(source_file, sheet_name=None, header=None)
    except Exception as e:
        raise ValueError("토스 파일을 읽을 수 없습니다. 비밀번호(4자리 숫자)를 확인해주세요.")

    # Iterate through sheets to find one with valid headers
    # User requested to ONLY look at '결제 상세내역' if possible
    target_sheet = '결제 상세내역'
    
    if target_sheet in sheets_dict:
        # If the specific sheet exists, only try that one
        try:
            return normalize_columns(sheets_dict[target_sheet], 'toss')
        except ValueError as e:
            raise ValueError(f"Found sheet '{target_sheet}' but failed to parse: {e}")
            
    # Fallback: iterate others if target not found (or maybe strict fail?)
    # Given the request "refer only to...", failing if missing might be safer, 
    # but let's keep iteration as a backup for slightly different versions, 
    # while explicitly skipping known summary sheets if needed.
    
    for sheet_name, df in sheets_dict.items():
        # Skip summary sheets explicitly
        if any(keyword in sheet_name for keyword in ['기준', '합계', '요약']):
            continue
            
        try:
             normalized_df = normalize_columns(df, 'toss')
             return normalized_df
        except ValueError:
            continue # Try next sheet

    # Error Messaging
    first_df = list(sheets_dict.values())[0]
    preview_str = first_df.head(5).to_string() 
    
    raise ValueError(f"토스 파일 형식 오류: '{target_sheet}' 시트를 찾을 수 없거나 유효하지 않습니다. 토스 결제 상세내역 파일인지 확인해주세요.")

def load_naver_data(file, password):
    """Loads Naver Smart Place Excel data with decryption."""
    # Similar multi-sheet logic could be applied here if needed
    file.seek(0)
    
    decrypted_file = None
    try:
         decrypted_file = decrypt_excel(file, password)
    except:
         file.seek(0)
    
    source_file = decrypted_file if decrypted_file else file
    
    try:
        # Just try first sheet for Naver for now unless reported otherwise
        df = pd.read_excel(source_file)
    except:
        raise ValueError("네이버 파일을 읽을 수 없습니다. 비밀번호(네이버 아이디)를 확인해주세요.")
            
    df = normalize_columns(df, 'naver')
    return df

def load_toss_discount_data(file, password):
    """
    Looks for Toss Product/Order detail sheet and extracts rows where category is '아이스크림' and discount > 0.
    """
    file.seek(0)
    try:
        decrypted_file = decrypt_excel(file, password)
    except:
        file.seek(0)
    source_file = decrypted_file if decrypted_file else file

    try:
        sheets_dict = pd.read_excel(source_file, sheet_name=None, header=None)
    except:
        return pd.DataFrame()

    target_sheet = None
    for k in sheets_dict.keys():
        if '상품' in str(k) or '주문' in str(k):
             if '합계' not in str(k) and '요약' not in str(k) and str(k) not in ['결제 상세내역', '결제상세내역']:
                 target_sheet = k
                 break
    
    if not target_sheet:
         return pd.DataFrame()
         
    df = sheets_dict[target_sheet]
    
    # Try finding the header
    keywords = ['카테고리', '상품명'] # More permissive keywords
    header_idx = find_header_row(df, keywords)
    
    if header_idx is not None and header_idx != -1:
         new_header = df.iloc[header_idx]
         df = df.iloc[header_idx + 1:]
         df.columns = [str(c).replace(" ", "").replace("\n", "").strip() for c in new_header]
         df = df.reset_index(drop=True)
         
         cat_col = next((c for c in df.columns if '카테고리' in c), None)
         disc_amt_col = next((c for c in df.columns if '상품할인금액' in c), None)
         if not disc_amt_col: disc_amt_col = next((c for c in df.columns if '할인금액' in c), None)
         
         disc_reason_col = next((c for c in df.columns if '상품할인' == c), None)
         
         if cat_col and disc_amt_col:
              # 숫자 처리: "원", "," 기호 제거 후 형변환
              # 예: "-3,000원", "3,000" -> -3000, 3000
              df[disc_amt_col] = df[disc_amt_col].astype(str).str.replace(r'[원,]', '', regex=True)
              df[disc_amt_col] = pd.to_numeric(df[disc_amt_col], errors='coerce').fillna(0)
              
              # 할인이 0이 아닌 경우 (마이너스 값으로 적히는 경우도 포함)
              mask = (df[cat_col].astype(str).str.contains('아이스크림', na=False)) & (df[disc_amt_col] != 0)
              
              res_df = df[mask].copy()
              
              target_cols = ['결제일자', '결제시간', '결제시각', '영수증번호', cat_col, '상품명', '단가', '수량', disc_reason_col, disc_amt_col]
              cols_to_keep = []
              for target in target_cols:
                  if target is None: continue
                  for c in res_df.columns:
                      if target in c and c not in cols_to_keep:
                          cols_to_keep.append(c)
              
              if cols_to_keep:
                  return res_df[cols_to_keep]
              return res_df
              
    return pd.DataFrame()
