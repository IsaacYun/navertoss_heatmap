import pandas as pd
import msoffcrypto
import io
import os

toss_filename = "../매출리포트-260128023045.xlsx"
naver_filename = "../레드런천안점_예약자관리_20260128_0232.xlsx"

toss_pw = "9999"
naver_pw = "yunisaac"

def inspect_file(path, password, name):
    print(f"--- Inspecting {name} ---")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        with open(path, "rb") as f:
            file_buffer = f
            try:
                decrypted = io.BytesIO()
                office_file = msoffcrypto.OfficeFile(file_buffer)
                office_file.load_key(password=password)
                office_file.decrypt(decrypted)
                
                # Load all sheets
                xls = pd.ExcelFile(decrypted)
                print(f"Sheet Names: {xls.sheet_names}")
                
                for sheet in xls.sheet_names:
                    print(f"\n[Sheet: {sheet}]")
                    df = pd.read_excel(xls, sheet_name=sheet)
                    print("Columns:", list(df.columns))
                    print("Head (First 15 rows):")
                    print(df.head(15).to_string())
                    
            except Exception as e:
                print(f"Decryption/Read Error: {e}")
                
    except Exception as e:
        print(f"File Open Error: {e}")

inspect_file(toss_filename, toss_pw, "Toss File")
inspect_file(naver_filename, naver_pw, "Naver File")
