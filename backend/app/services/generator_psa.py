"""PSA Type 2 代码生成引擎"""
from app.services.template_engine import TemplateEngine
from app.models.meta import Attribute
from sqlalchemy.orm import Session


class PSAGenerator:
    """PSA Type 2 全套代码生成器"""

    def __init__(self, session: Session, psa_db_name: str, hash_dummy: str = "@IAMHUSKIES@",
                 oltp_db_name: str = None, record_src: str = None):
        self.session = session
        self.psa_db_name = psa_db_name
        self.hash_dummy = hash_dummy
        self.oltp_db_name = oltp_db_name
        self.record_src = record_src
        self.template = TemplateEngine()

    def _load_tables(self) -> list[dict]:
        """从 META 加载需要生成的表元数据（按 record_src 过滤）"""
        query = self.session.query(Attribute).filter(
            Attribute.is_pk.is_(True) | Attribute.is_bk.is_(True) |
            Attribute.is_di.is_(True) | Attribute.is_fk.is_(True)
        )
        if self.record_src:
            query = query.filter(Attribute.record_src == self.record_src)
        rows = query.all()

        table_map: dict[str, dict] = {}
        for row in rows:
            key = row.table_name
            if key not in table_map:
                table_map[key] = {
                    "table_name": row.table_name,
                    "schema_name": row.table_schema or "dbo",
                    "record_src": row.record_src or "",
                    "pk_fields": [],
                    "bk_fields": [],
                    "fk_fields": [],
                    "di_fields": [],
                }
            field = {
                "field_name": row.column_name,
                "field_type": self._resolve_type(row.data_type, row.character_maximum_length, row.numeric_precision, row.numeric_scale),
            }
            if row.is_pk:
                table_map[key]["pk_fields"].append(field)
            elif row.is_bk:
                table_map[key]["bk_fields"].append(field)
            elif row.is_fk:
                table_map[key]["fk_fields"].append(field)
            elif row.is_di:
                table_map[key]["di_fields"].append(field)

        return list(table_map.values())

    def _resolve_type(self, data_type: str, char_len: int, precision: int, scale: int) -> str:
        """将原始数据类型转为 SQL Server 类型字符串"""
        t = data_type.upper() if data_type else "NVARCHAR"
        if t in ("NVARCHAR", "VARCHAR", "NCHAR", "CHAR"):
            return f"{t}({char_len or 255})"
        if t == "DECIMAL":
            return f"DECIMAL({precision or 18},{scale or 2})"
        if t == "NUMERIC":
            return f"NUMERIC({precision or 18})"
        return t

    def generate_stg_table(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/stg_table.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
        })

    def generate_cdc_table(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/cdc_table.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
        })

    def generate_log_table(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/log_table.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
        })

    def generate_v_mta(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/v_mta.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
            "hash_dummy": self.hash_dummy,
        })

    def generate_v_current(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/v_log_current.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
        })

    def generate_usp_stg(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/usp_stg.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
            "hash_dummy": self.hash_dummy,
            "oltp_db_name": self.oltp_db_name or self.psa_db_name,
        })

    def generate_usp_cdc(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/usp_cdc.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
            "hash_dummy": self.hash_dummy,
        })

    def generate_usp_log(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/usp_log.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
            "hash_dummy": self.hash_dummy,
        })

    def generate_all(self) -> dict[str, str]:
        return {
            "stg": self.generate_stg_table(),
            "cdc": self.generate_cdc_table(),
            "log": self.generate_log_table(),
            "v_mta": self.generate_v_mta(),
            "v_current": self.generate_v_current(),
            "usp_stg": self.generate_usp_stg(),
            "usp_cdc": self.generate_usp_cdc(),
            "usp_log": self.generate_usp_log(),
        }

    def generate_combined(self) -> str:
        parts = self.generate_all()
        return "\n\n".join(parts.values())

    def generate_execute_flow(self) -> str:
        tables = self._load_tables()
        return self.template.render("psa/execute_flow.sql.j2", {
            "psa_db_name": self.psa_db_name,
            "tables": tables,
        })