import pandas as pd
import msoffcrypto
import io

toss_filename = "../매출리포트-260128023045.xlsx"
toss_pw = "9999"

with open(toss_filename, "rb") as f:
    decrypted = io.BytesIO()
    office_file = msoffcrypto.OfficeFile(f)
    office_file.load_key(password=toss_pw)
    office_file.decrypt(decrypted)
    
    # Read specific sheet
    df = pd.read_excel(decrypted, sheet_name='결제 상세내역', header=None)
    print("--- 결제 상세내역 (First 10 rows) ---")
    print(df.head(10).to_string())
