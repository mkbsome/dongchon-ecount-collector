# -*- coding: utf-8 -*-
"""테이블 제약조건 확인"""
import psycopg2

DB_CONFIG = {
    'host': 'triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'triflow_admin',
    'password': 'tri878993+'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# 테이블별 제약조건 확인
for table in ['ecount_sales', 'ecount_purchase', 'ecount_production']:
    print(f"\n=== {table} 제약조건 ===")
    cur.execute(f"""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = '{table}'
    """)
    constraints = cur.fetchall()
    for c in constraints:
        print(f"  - {c[0]}: {c[1]}")

    # 행 수 확인
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  총 행 수: {count}")

    # 날짜 범위 확인
    cur.execute(f"SELECT MIN(date), MAX(date) FROM {table}")
    dates = cur.fetchone()
    print(f"  기간: {dates[0]} ~ {dates[1]}")

conn.close()
