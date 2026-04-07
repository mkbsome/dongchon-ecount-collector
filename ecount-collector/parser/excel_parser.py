# -*- coding: utf-8 -*-
"""
엑셀 파일 파싱
"""

import pandas as pd
from typing import Dict, List, Any
from datetime import datetime


class ExcelParser:
    """E카운트 엑셀 파일 파서"""

    @staticmethod
    def parse_sales(file_path: str) -> List[Dict[str, Any]]:
        """판매현황 엑셀 파싱"""
        df = pd.read_excel(file_path, header=1)  # 첫 번째 행이 헤더가 아닐 수 있음

        # 컬럼명 정리 (공백 제거, NaN 처리)
        df.columns = [str(col).strip() if pd.notna(col) else f"col_{i}" for i, col in enumerate(df.columns)]

        # 빈 행 제거
        df = df.dropna(how='all')

        records = []
        for _, row in df.iterrows():
            record = {
                "type": "sales",
                "date": ExcelParser._parse_date(row.get("일자-No.", row.get("일자", ""))),
                "product_name": str(row.get("품목명", "")),
                "spec": str(row.get("규격", "")),
                "quantity": ExcelParser._parse_number(row.get("수량", 0)),
                "unit_price": ExcelParser._parse_number(row.get("단가", 0)),
                "supply_amount": ExcelParser._parse_number(row.get("공급가액", 0)),
                "vat": ExcelParser._parse_number(row.get("부가세", 0)),
                "total": ExcelParser._parse_number(row.get("합계", 0)),
                "customer_name": str(row.get("거래처명", "")),
                "customer_code": str(row.get("거래처코드", "")),
                "raw_data": row.to_dict()
            }
            if record["date"]:  # 날짜가 있는 행만 추가
                records.append(record)

        return records

    @staticmethod
    def parse_purchase(file_path: str) -> List[Dict[str, Any]]:
        """구매현황 엑셀 파싱"""
        df = pd.read_excel(file_path, header=1)
        df.columns = [str(col).strip() if pd.notna(col) else f"col_{i}" for i, col in enumerate(df.columns)]
        df = df.dropna(how='all')

        records = []
        for _, row in df.iterrows():
            record = {
                "type": "purchase",
                "date": ExcelParser._parse_date(row.get("일자-No.", row.get("일자", ""))),
                "supplier_name": str(row.get("거래처명", "")),
                "product_name": str(row.get("품목명(요약)", row.get("품목명", ""))),
                "total": ExcelParser._parse_number(row.get("금액합계", 0)),
                "transaction_type": str(row.get("거래유형", "")),
                "raw_data": row.to_dict()
            }
            if record["date"]:
                records.append(record)

        return records

    @staticmethod
    def parse_production(file_path: str) -> List[Dict[str, Any]]:
        """생산입고현황 엑셀 파싱"""
        df = pd.read_excel(file_path, header=1)
        df.columns = [str(col).strip() if pd.notna(col) else f"col_{i}" for i, col in enumerate(df.columns)]
        df = df.dropna(how='all')

        records = []
        for _, row in df.iterrows():
            record = {
                "type": "production",
                "date": ExcelParser._parse_date(row.get("일자-No.", row.get("일자", ""))),
                "factory_name": str(row.get("생산된공장명", "")),
                "warehouse_name": str(row.get("받는창고명", "")),
                "product_name": str(row.get("품목명[규격]", row.get("품목명", ""))),
                "quantity": ExcelParser._parse_number(row.get("수량", 0)),
                "raw_data": row.to_dict()
            }
            if record["date"]:
                records.append(record)

        return records

    @staticmethod
    def _parse_date(value) -> str:
        """날짜 문자열 파싱"""
        if pd.isna(value):
            return None

        value_str = str(value).strip()

        # "2026/03/03 -1" 형식 처리
        if "/" in value_str:
            date_part = value_str.split()[0] if " " in value_str else value_str
            try:
                dt = datetime.strptime(date_part, "%Y/%m/%d")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # "2026-03-03" 형식
        if "-" in value_str:
            try:
                dt = datetime.strptime(value_str[:10], "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return None

    @staticmethod
    def _parse_number(value) -> float:
        """숫자 파싱"""
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        # 문자열 처리 (콤마 제거)
        value_str = str(value).replace(",", "").strip()
        try:
            return float(value_str)
        except ValueError:
            return 0.0

    @staticmethod
    def parse(file_path: str, report_type: str) -> List[Dict[str, Any]]:
        """파일 유형에 따라 적절한 파서 호출"""
        parsers = {
            "sales": ExcelParser.parse_sales,
            "purchase": ExcelParser.parse_purchase,
            "production": ExcelParser.parse_production
        }

        parser = parsers.get(report_type)
        if not parser:
            raise ValueError(f"Unknown report type: {report_type}")

        return parser(file_path)
