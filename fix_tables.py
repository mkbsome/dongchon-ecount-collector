# -*- coding: utf-8 -*-
"""테이블 스키마 확인 및 수정"""
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

# 현재 테이블 스키마 확인
print("=== 현재 테이블 스키마 ===\n")

for table in ['ecount_sales', 'ecount_purchase', 'ecount_production']:
    cur.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print(f"{table}:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")
    print()

# spec 컬럼 추가
print("=== spec 컬럼 추가 ===\n")

try:
    cur.execute("ALTER TABLE core.ecount_purchase ADD COLUMN IF NOT EXISTS spec VARCHAR(100)")
    print("ecount_purchase: spec 컬럼 추가됨")
except Exception as e:
    print(f"ecount_purchase 오류: {e}")

try:
    cur.execute("ALTER TABLE core.ecount_production ADD COLUMN IF NOT EXISTS spec VARCHAR(100)")
    print("ecount_production: spec 컬럼 추가됨")
except Exception as e:
    print(f"ecount_production 오류: {e}")

conn.commit()
conn.close()

print("\n완료!")
