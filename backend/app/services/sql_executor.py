"""SQL 批处理执行器 — 按 GO 分割 + 事务执行"""
import re
from sqlalchemy import text
from sqlalchemy.engine import Engine
from app.database import get_engine


def split_by_go(sql: str) -> list[str]:
    """按 GO 关键字分割批处理 SQL"""
    statements = re.split(r'^\s*GO\s*$', sql, flags=re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in statements if s.strip()]


def execute_batch(conn_id: int, sql: str, engine: Engine = None) -> dict:
    """
    在指定数据库连接上执行批处理 SQL

    Args:
        conn_id: 连接 ID（当 engine 为 None 时用于查找缓存的引擎）
        sql: 要执行的 SQL
        engine: 可选，直接传入已构建的引擎（绕过缓存）

    Returns:
        {"success": bool, "message": str, "executed_count": int, "error_at": int}
    """
    if engine is None:
        engine = get_engine(conn_id)

    if not engine:
        return {"success": False, "message": f"Connection {conn_id} not found", "executed_count": 0, "error_at": -1}

    statements = split_by_go(sql)
    executed = 0

    try:
        with engine.begin() as conn:
            for i, stmt in enumerate(statements):
                conn.execute(text(stmt))
                executed += 1
        return {"success": True, "message": f"Executed {executed} statement(s)", "executed_count": executed, "error_at": -1}
    except Exception as e:
        return {
            "success": False,
            "message": f"Error at statement {executed + 1}: {str(e)}",
            "executed_count": executed,
            "error_at": executed,
        }


def check_database_status(conn_id: int) -> dict:
    """检查目标数据库中的 PSA 对象状态"""
    engine = get_engine(conn_id)
    if not engine:
        return {"success": False, "message": "Connection not found", "tables": [], "views": [], "procedures": []}

    result = {"tables": [], "views": [], "procedures": []}

    with engine.connect() as conn:
        # 表
        rows = conn.execute(text("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)).fetchall()
        result["tables"] = [f"{r[0]}.{r[1]}" for r in rows]

        # 视图
        rows = conn.execute(text("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.VIEWS
            ORDER BY TABLE_NAME
        """)).fetchall()
        result["views"] = [f"{r[0]}.{r[1]}" for r in rows]

        # 存储过程
        rows = conn.execute(text("""
            SELECT SPECIFIC_SCHEMA, SPECIFIC_NAME
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_TYPE = 'PROCEDURE'
            ORDER BY SPECIFIC_NAME
        """)).fetchall()
        result["procedures"] = [f"{r[0]}.{r[1]}" for r in rows]

    return {"success": True, **result}