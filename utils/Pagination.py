from utils.MySQLDB import MySQLDB
class Pagination:
    @staticmethod
    def validate_params(data: dict) -> tuple[int,int]:
        """验证分页参数"""
        try:
            page = int(data.get("page"))
            per_page = int(data.get("per_page"))
            if page < 1 or per_page < 1:
                raise ValueError
            return page, per_page
        except (TypeError, ValueError):
            raise ValueError("页码参数必须是整数")
        
    
    @staticmethod
    def execute_paginated_query(
        db: MySQLDB,
        base_sql: str,
        base_params: tuple,
        page: int,
        per_page: int,
        count_field: str = "id"
    ) -> dict:
        """执行分页查询"""
        try:
            # 计算总数
            count_sql = f"SELECT COUNT({count_field}) AS total FROM ({base_sql}) AS subquery"
            count_result = db.select_db(count_sql,base_params)
            total = count_result[0]['total'] if count_result else 0

            # 计算分页参数
            offset = (page-1) * per_page
            paginated_sql = f"{base_sql} LIMIT %s OFFSET %s"
            paginated_params = base_params + (per_page, offset)

            # 执行分页查询
            results = db.select_db(paginated_sql, paginated_params)

            return {
                    "results": results,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
        except Exception as e:
            print(f"Paginated Query Error: {str(e)}")
            return {
                "results": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0
            }