# -*- coding: utf-8 -*-
"""모든 Excel 파일 날짜 확인"""
import pandas as pd
import os
import glob

download_dir = "C:/Users/mkbso/ecount_downloads"

files = glob.glob(os.path.join(download_dir, "*.xlsx"))
files.sort(key=os.path.getmtime)

print("=== 다운로드된 파일별 날짜 범위 ===\n")
for f in files:
    try:
        df = pd.read_excel(f, header=1)
        if len(df) > 0 and '일자-No.' in df.columns:
            first_date = str(df['일자-No.'].iloc[0]).split()[0]
            last_date = str(df['일자-No.'].iloc[-1]).split()[0]
            print(f"{os.path.basename(f)}: {first_date} ~ {last_date} ({len(df)}건)")
    except Exception as e:
        print(f"{os.path.basename(f)}: 오류 - {e}")
