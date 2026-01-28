import pandas as pd
from utils.data_loader import parse_korean_datetime

# Test cases from the file inspection
test_dates = [
    "26. 1. 2.(금) 오후 1:00",
    "26. 1. 3.(토) 오전 11:20"
]

print("--- Testing Date Parsing (Fixed) ---")
for d in test_dates:
    parsed = parse_korean_datetime(d)
    print(f"Original: {d} -> Parsed: {parsed}\n")
