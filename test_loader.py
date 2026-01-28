import pandas as pd
from utils.data_loader import load_toss_data, load_naver_data
import os

toss_filename = "../매출리포트-260128023045.xlsx"
naver_filename = "../레드런천안점_예약자관리_20260128_0232.xlsx"

toss_pw = "9999"
naver_pw = "yunisaac"

print("--- Testing Data Loader ---")

try:
    with open(toss_filename, 'rb') as f:
        print("Loading Toss...")
        df_toss = load_toss_data(f, toss_pw)
        print("Toss Loaded Successfully!")
        print(df_toss.head())
        print(df_toss.dtypes)
except Exception as e:
    print(f"Toss Load Failed: {e}")

try:
    with open(naver_filename, 'rb') as f:
        print("\nLoading Naver...")
        df_naver = load_naver_data(f, naver_pw)
        print("Naver Loaded Successfully!")
        print(df_naver.head())
        print(df_naver.dtypes)
except Exception as e:
    print(f"Naver Load Failed: {e}")
