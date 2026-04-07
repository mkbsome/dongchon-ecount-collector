# E-count 자동수집 데이터베이스 스키마 문서

## 1. 개요

### 1.1 연결 정보

| 항목 | 값 |
|------|-----|
| Host | `triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com` |
| Port | `5432` |
| Database | `postgres` |
| Schema | `public` |
| User | `triflow_admin` |
| Password | `tri878993+` |
| Engine | PostgreSQL 15.x |
| Region | ap-northeast-2 (서울) |
| SSL | 지원 (선택사항) |

### 1.2 연결 예시

**Python (psycopg2)**
```python
import psycopg2

conn = psycopg2.connect(
    host='triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    port=5432,
    database='postgres',
    user='triflow_admin',
    password='tri878993+'
)
```

**Node.js (pg)**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
    host: 'triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com',
    port: 5432,
    database: 'postgres',
    user: 'triflow_admin',
    password: 'tri878993+'
});
```

**JDBC (Java)**
```
jdbc:postgresql://triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com:5432/postgres
user: triflow_admin
password: tri878993+
```

**연결 문자열 (Connection String)**
```
postgresql://triflow_admin:tri878993+@triflow-db.cn88cwwm6cgt.ap-northeast-2.rds.amazonaws.com:5432/postgres
```

### 1.2 데이터 현황 (2026-03-25 기준)

| 테이블 | 설명 | 레코드 수 | 기간 |
|--------|------|-----------|------|
| `ecount_sales` | 판매현황 | 6,736건 | 2024-01-02 ~ 2026-03-24 |
| `ecount_purchase` | 구매현황 | 945건 | 2024-01-01 ~ 2026-03-24 |
| `ecount_production` | 생산입고현황 | 465건 | 2024-01-01 ~ 2026-03-24 |
| `ecount_collection_log` | 수집 로그 | - | - |

---

## 2. 테이블 스키마

### 2.1 ecount_sales (판매현황)

E-count ERP의 **영업관리 > 판매현황** 데이터

```sql
CREATE TABLE ecount_sales (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,                    -- 판매일자
    doc_no          VARCHAR(50),                      -- 전표번호
    product_name    VARCHAR(200),                     -- 품목명
    spec            VARCHAR(100),                     -- 규격
    quantity        NUMERIC,                          -- 수량
    unit_price      NUMERIC,                          -- 단가
    supply_amount   NUMERIC,                          -- 공급가액
    vat             NUMERIC,                          -- 부가세
    total           NUMERIC,                          -- 합계
    customer_name   VARCHAR(200),                     -- 거래처명
    customer_code   VARCHAR(50),                      -- 거래처코드
    collected_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 수집 시각
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 생성 시각

    UNIQUE(date, doc_no, product_name)               -- 중복 방지
);
```

**컬럼 설명:**

| 컬럼 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `date` | DATE | 판매 일자 | 2026-03-24 |
| `doc_no` | VARCHAR(50) | 전표번호 (같은 날 여러 전표 구분) | -1, -2, -15 |
| `product_name` | VARCHAR(200) | 판매 품목명 | 청주사과 프리미엄(상) |
| `spec` | VARCHAR(100) | 규격 | 5kg, 10kg |
| `quantity` | NUMERIC | 판매 수량 | 10.00 |
| `unit_price` | NUMERIC | 단가 | 4,673 |
| `supply_amount` | NUMERIC | 공급가액 (VAT 제외) | 42,482 |
| `vat` | NUMERIC | 부가세 | 4,248 |
| `total` | NUMERIC | 합계 (공급가액 + VAT) | 46,730 |
| `customer_name` | VARCHAR(200) | 거래처(고객)명 | (주)농협유통 |
| `customer_code` | VARCHAR(50) | 거래처 코드 | C001 |

---

### 2.2 ecount_purchase (구매현황)

E-count ERP의 **구매관리 > 구매현황** 데이터

```sql
CREATE TABLE ecount_purchase (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,                    -- 구매일자
    doc_no          VARCHAR(50),                      -- 전표번호
    product_name    VARCHAR(200),                     -- 품목명
    spec            VARCHAR(100),                     -- 규격
    quantity        NUMERIC,                          -- 수량
    unit_price      NUMERIC,                          -- 단가
    supply_amount   NUMERIC,                          -- 공급가액
    vat             NUMERIC,                          -- 부가세
    total           NUMERIC,                          -- 합계
    supplier_name   VARCHAR(200),                     -- 공급업체명
    collected_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date, doc_no, product_name)
);
```

**컬럼 설명:**

| 컬럼 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `date` | DATE | 구매 일자 | 2026-03-24 |
| `doc_no` | VARCHAR(50) | 전표번호 | -1 |
| `product_name` | VARCHAR(200) | 구매 품목명 | 원재료A |
| `spec` | VARCHAR(100) | 규격 | 20kg |
| `quantity` | NUMERIC | 구매 수량 | 1000.00 |
| `unit_price` | NUMERIC | 단가 | 5,200 |
| `supply_amount` | NUMERIC | 공급가액 | 5,200,000 |
| `vat` | NUMERIC | 부가세 | 520,000 |
| `total` | NUMERIC | 합계 | 5,720,000 |
| `supplier_name` | VARCHAR(200) | 공급업체명 | (주)원재료공급 |

---

### 2.3 ecount_production (생산입고현황)

E-count ERP의 **생산/외주 > 생산입고현황** 데이터

```sql
CREATE TABLE ecount_production (
    id                SERIAL PRIMARY KEY,
    date              DATE NOT NULL,                  -- 생산일자
    doc_no            VARCHAR(50),                    -- 전표번호
    product_name      VARCHAR(200),                   -- 품목명
    spec              VARCHAR(100),                   -- 규격
    quantity          NUMERIC,                        -- 수량
    from_warehouse    VARCHAR(100),                   -- 출고창고
    to_warehouse      VARCHAR(100),                   -- 입고창고
    production_amount NUMERIC,                        -- 생산금액
    memo              TEXT,                           -- 비고
    collected_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date, doc_no, product_name)
);
```

**컬럼 설명:**

| 컬럼 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `date` | DATE | 생산 일자 | 2026-03-19 |
| `doc_no` | VARCHAR(50) | 전표번호 | -1 |
| `product_name` | VARCHAR(200) | 생산 품목명 | 청주사과 선물세트 |
| `spec` | VARCHAR(100) | 규격 | 3kg |
| `quantity` | NUMERIC | 생산 수량 | 8000.00 |
| `from_warehouse` | VARCHAR(100) | 원재료 출고 창고 | 원재료창고 |
| `to_warehouse` | VARCHAR(100) | 완제품 입고 창고 | 제품창고 |
| `production_amount` | NUMERIC | 생산 금액 | 0 |
| `memo` | TEXT | 비고 | |

---

### 2.4 ecount_collection_log (수집 로그)

자동 수집 실행 기록

```sql
CREATE TABLE ecount_collection_log (
    id              SERIAL PRIMARY KEY,
    data_type       VARCHAR(50) NOT NULL,            -- 데이터 유형 (sales/purchase/production)
    target_date     DATE NOT NULL,                   -- 수집 대상 월 (1일 기준)
    records_count   INTEGER DEFAULT 0,               -- 수집 건수
    status          VARCHAR(20) DEFAULT 'pending',   -- 상태 (pending/running/completed/error)
    error_message   TEXT,                            -- 오류 메시지
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP,

    UNIQUE(data_type, target_date)
);
```

**status 값:**
- `pending`: 대기 중
- `running`: 수집 진행 중
- `completed`: 수집 완료
- `error`: 오류 발생

---

## 3. 데이터 흐름

### 3.1 수집 프로세스

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   E-count ERP   │────▶│  auto_collector  │────▶│  PostgreSQL RDS │
│  (웹 브라우저)   │     │    (Python)      │     │   (AWS 서울)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
   로그인/검색              Excel 다운로드            UPSERT
   날짜 선택               데이터 파싱              중복 처리
```

### 3.2 자동 수집 스케줄

- **실행 시간**: 매일 오후 12:30
- **수집 방식**: 증분 수집 (마지막 수집일 이후 데이터만)
- **중복 처리**: UPSERT (INSERT ON CONFLICT DO UPDATE)

### 3.3 데이터 키 (중복 방지)

각 테이블은 다음 조합으로 유니크 제약:
- `(date, doc_no, product_name)`

같은 날짜, 같은 전표, 같은 품목이 이미 있으면 UPDATE, 없으면 INSERT

---

## 4. 활용 예시 쿼리

### 4.1 일별 판매 합계

```sql
SELECT
    date,
    COUNT(*) as 건수,
    SUM(quantity) as 총수량,
    SUM(total) as 총매출
FROM ecount_sales
WHERE date >= '2026-03-01'
GROUP BY date
ORDER BY date;
```

### 4.2 품목별 판매 현황

```sql
SELECT
    product_name,
    SUM(quantity) as 총수량,
    SUM(total) as 총매출,
    COUNT(DISTINCT date) as 판매일수
FROM ecount_sales
WHERE date >= '2026-01-01'
GROUP BY product_name
ORDER BY 총매출 DESC
LIMIT 10;
```

### 4.3 월별 매출 추이

```sql
SELECT
    TO_CHAR(date, 'YYYY-MM') as 월,
    SUM(total) as 매출
FROM ecount_sales
GROUP BY TO_CHAR(date, 'YYYY-MM')
ORDER BY 월;
```

### 4.4 구매/판매 비교

```sql
SELECT
    TO_CHAR(date, 'YYYY-MM') as 월,
    (SELECT SUM(total) FROM ecount_sales s WHERE TO_CHAR(s.date, 'YYYY-MM') = TO_CHAR(p.date, 'YYYY-MM')) as 매출,
    SUM(total) as 구매
FROM ecount_purchase p
GROUP BY TO_CHAR(date, 'YYYY-MM')
ORDER BY 월;
```

---

## 5. 보안 고려사항

### 5.1 현재 상태

- DB 자격증명이 코드에 하드코딩되어 있음
- RDS는 퍼블릭 액세스 가능 상태

### 5.2 권장 개선사항

1. **환경변수 사용**: DB 자격증명을 환경변수로 분리
2. **VPC 보안**: RDS를 Private Subnet으로 이동
3. **IAM 인증**: RDS IAM 인증 사용 고려
4. **암호화**: SSL/TLS 연결 강제

---

## 6. 인덱스 및 제약조건

### 6.1 인덱스

| 테이블 | 인덱스명 | 타입 | 컬럼 |
|--------|----------|------|------|
| ecount_sales | ecount_sales_pkey | PRIMARY KEY | id |
| ecount_sales | ecount_sales_date_doc_no_product_name_key | UNIQUE | (date, doc_no, product_name) |
| ecount_purchase | ecount_purchase_pkey | PRIMARY KEY | id |
| ecount_purchase | ecount_purchase_date_doc_no_product_name_key | UNIQUE | (date, doc_no, product_name) |
| ecount_production | ecount_production_pkey | PRIMARY KEY | id |
| ecount_production | ecount_production_date_doc_no_product_name_key | UNIQUE | (date, doc_no, product_name) |

### 6.2 데이터 타입 상세

**숫자 컬럼 (NUMERIC)**
- 정밀도: 15자리
- 소수점: 2자리
- 범위: -9,999,999,999,999.99 ~ 9,999,999,999,999.99

**날짜/시간 컬럼**
- `date`: DATE (YYYY-MM-DD)
- `collected_at`, `created_at`: TIMESTAMP WITHOUT TIME ZONE

**문자열 컬럼**
- VARCHAR는 지정된 길이까지만 저장
- TEXT는 길이 제한 없음

---

## 7. 데이터 갱신 주기

| 항목 | 내용 |
|------|------|
| 수집 주기 | 매일 1회 (오후 12:30) |
| 수집 방식 | 증분 수집 (마지막 수집일 이후) |
| 데이터 지연 | 최대 24시간 (당일 데이터는 익일 수집) |
| 중복 처리 | UPSERT (기존 데이터 덮어쓰기) |

---

## 8. 주의사항

### 8.1 NULL 값 처리

- `doc_no`: 전표번호가 없는 경우 빈 문자열('') 또는 NULL
- `product_name`: 품목명이 없는 경우 'nan' 문자열이 들어갈 수 있음
- 숫자 컬럼: 값이 없으면 0 또는 NULL

### 8.2 데이터 정합성

- E-count 원본 Excel에서 파싱하므로 원본 데이터 형식에 따라 달라질 수 있음
- `collected_at`은 DB에 저장된 시각, E-count 실제 입력 시각과 다름

### 8.3 조회 시 권장사항

```sql
-- NULL 및 빈값 제외
SELECT * FROM ecount_sales
WHERE product_name IS NOT NULL
  AND product_name != ''
  AND product_name != 'nan';

-- 날짜 범위 조회 시 인덱스 활용
SELECT * FROM ecount_sales
WHERE date BETWEEN '2026-01-01' AND '2026-03-31';
```

---

## 9. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-24 | 최초 데이터 수집 완료 (27개월치) |
| 2026-03-24 | 자동 수집 스케줄러 설정 |
| 2026-03-25 | 스키마 문서 작성 |
