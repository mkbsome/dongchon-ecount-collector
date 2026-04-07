# -*- coding: utf-8 -*-
"""Excel 파일 날짜 확인"""
import pandas as pd
import os
import glob

download_dir = "C:/Users/mkbso/ecount_downloads"

# 가장 최근 production 파일
files = glob.glob(os.path.join(download_dir, "*.xlsx"))
files.sort(key=os.path.getmtime, reverse=True)

print("=== 최근 다운로드된 파일 ===")
for f in files[:5]:
    print(f"  {os.path.basename(f)} - {os.path.getsize(f)} bytes")

# 최근 파일의 내용 확인
if files:
    print(f"\n=== {os.path.basename(files[0])} 내용 ===")
    df = pd.read_excel(files[0], header=1)
    print(f"행 수: {len(df)}")
    if '일자-No.' in df.columns:
        print(f"날짜 범위: {df['일자-No.'].iloc[0]} ~ {df['일자-No.'].iloc[-1]}")
    print(df.head(3))
