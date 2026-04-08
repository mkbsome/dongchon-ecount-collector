# -*- coding: utf-8 -*-
"""DB 현황 체크"""
import psycopg2

DB_CONFIG = {
    'host': 'triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'triflow_ai',
    'user': 'triflow_admin',
    'password': 'tri878993+'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("=== E-count 데이터 현황 ===\n")

# 판매현황
cur.execute("SELECT COUNT(*) FROM core.ecount_sales")
sales_count = cur.fetchone()[0]
print(f"판매현황 (ecount_sales): {sales_count:,}건")

cur.execute("SELECT MIN(date), MAX(date) FROM core.ecount_sales")
row = cur.fetchone()
if row[0]:
    print(f"  - 기간: {row[0]} ~ {row[1]}")

# 구매현황
cur.execute("SELECT COUNT(*) FROM core.ecount_purchase")
purchase_count = cur.fetchone()[0]
print(f"\n구매현황 (ecount_purchase): {purchase_count:,}건")

cur.execute("SELECT MIN(date), MAX(date) FROM core.ecount_purchase")
row = cur.fetchone()
if row[0]:
    print(f"  - 기간: {row[0]} ~ {row[1]}")

# 생산입고현황
cur.execute("SELECT COUNT(*) FROM core.ecount_production")
production_count = cur.fetchone()[0]
print(f"\n생산입고현황 (ecount_production): {production_count:,}건")

cur.execute("SELECT MIN(date), MAX(date) FROM core.ecount_production")
row = cur.fetchone()
if row[0]:
    print(f"  - 기간: {row[0]} ~ {row[1]}")

print(f"\n총 합계: {sales_count + purchase_count + production_count:,}건")

conn.close()
