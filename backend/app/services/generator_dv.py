"""Data Vault 2.0 代码生成引擎"""
from sqlalchemy.orm import Session
from app.models.meta import Attribute, DvHub, DvSat, DvLink, Configuration
from app.services.template_engine import TemplateEngine


class DVGenerator:
    """DV 全套代码生成器（HUB / SAT / LINK）"""

    def __init__(self, session: Session, psa_db_name: str, core_db_name: str, hash_tail: str):
        self.session = session
        self.psa_db_name = psa_db_name
        self.core_db_name = core_db_name
        self.hash_tail = hash_tail
        self.template = TemplateEngine()

    def _resolve_type(self, data_type: str, char_len: int, precision: int, scale: int) -> str:
        t = data_type.upper() if data_type else "NVARCHAR"
        if t in ("NVARCHAR", "VARCHAR", "NCHAR", "CHAR"):
            return f"{t}({char_len or 255})"
        if t == "DECIMAL":
            return f"DECIMAL({precision or 18},{scale or 2})"
        if t == "NUMERIC":
            return f"NUMERIC({precision or 18})"
        return t

    def _load_hubs(self) -> list[dict]:
        """从 META 加载所有 HUB 配置"""
        hub_rows = self.session.query(DvHub).all()
        hubs = []
        for hub in hub_rows:
            fields = self.session.query(Attribute).filter(
                Attribute.dv_hub_id == hub.id,
                Attribute.is_bk == 1,
            ).all()
            pk_fields = []
            for f in fields:
                pk_fields.append({
                    "field_name": f.dv_column_name or f.column_name,
                    "psa_field_name": f.column_name,
                    "field_type": self._resolve_type(
                        f.data_type, f.character_maximum_length,
                        f.numeric_precision, f.numeric_scale,
                    ),
                })
            if not pk_fields:
                continue
            # 取第一个关联的 PSA 表名
            psa_table = self.session.query(Attribute).filter(
                Attribute.dv_hub_id == hub.id,
            ).first()
            hubs.append({
                "table_name": hub.table_name,
                "record_source": "dbo",
                "psa_table_name": psa_table.table_name if psa_table else "",
                "psa_schema_name": "dbo",
                "pk_fields": pk_fields,
            })
        return hubs

    def _load_sats(self) -> list[dict]:
        """加载 SAT 配置"""
        sat_rows = self.session.query(DvSat).all()
        sats = []
        for sat in sat_rows:
            # SAT 的 PK 字段 = 同源表的 BK 字段（通过 SAT_{table_name} 推导源表名）
            source_table = sat.table_name
            pk_fields_data = []
            if source_table.startswith("SAT_"):
                source_table = source_table[4:]
                pk_fields_data = self.session.query(Attribute).filter(
                    Attribute.table_name == source_table,
                    Attribute.is_bk == 1,
                ).all()
            di_fields_data = self.session.query(Attribute).filter(
                Attribute.dv_sat_id == sat.id,
                Attribute.is_di == 1,
            ).all()
            pk_fields = []
            for f in pk_fields_data:
                pk_fields.append({
                    "field_name": f.dv_column_name or f.column_name,
                    "psa_field_name": f.column_name,
                    "field_type": self._resolve_type(
                        f.data_type, f.character_maximum_length,
                        f.numeric_precision, f.numeric_scale,
                    ),
                })
            di_fields = []
            for f in di_fields_data:
                di_fields.append({
                    "field_name": f.dv_column_name or f.column_name,
                    "psa_field_name": f.column_name,
                    "field_type": self._resolve_type(
                        f.data_type, f.character_maximum_length,
                        f.numeric_precision, f.numeric_scale,
                    ),
                })
            if not pk_fields and not di_fields:
                continue
            first = self.session.query(Attribute).filter(
                Attribute.dv_sat_id == sat.id,
            ).first()
            sats.append({
                "table_name": sat.table_name,
                "record_source": "dbo",
                "psa_table_name": first.table_name if first else "",
                "psa_schema_name": "dbo",
                "pk_fields": pk_fields,
                "di_fields": di_fields,
            })
        return sats

    def _load_links(self) -> list[dict]:
        """加载 LINK 配置"""
        link_rows = self.session.query(DvLink).all()
        links = []
        for link in link_rows:
            fields = self.session.query(Attribute).filter(
                Attribute.dv_link_id == link.id,
                (Attribute.is_fk == 1) | (Attribute.is_pk == 1),
            ).all()
            fk_fields = []
            for f in fields:
                fk_fields.append({
                    "field_name": f.dv_column_name or f.column_name,
                    "psa_field_name": f.column_name,
                    "field_type": self._resolve_type(
                        f.data_type, f.character_maximum_length,
                        f.numeric_precision, f.numeric_scale,
                    ),
                })
            if not fk_fields:
                continue
            first = self.session.query(Attribute).filter(
                Attribute.dv_link_id == link.id,
            ).first()
            links.append({
                "table_name": link.table_name,
                "record_source": "dbo",
                "psa_table_name": first.table_name if first else "",
                "psa_schema_name": "dbo",
                "fk_fields": fk_fields,
            })
        return links

    def generate_hub_table(self) -> str:
        return self.template.render("dv/hub_table.sql.j2", {
            "core_db_name": self.core_db_name,
            "dv_hubs": self._load_hubs(),
        })

    def generate_sat_table(self) -> str:
        return self.template.render("dv/sat_table.sql.j2", {
            "core_db_name": self.core_db_name,
            "dv_sats": self._load_sats(),
        })

    def generate_link_table(self) -> str:
        return self.template.render("dv/link_table.sql.j2", {
            "core_db_name": self.core_db_name,
            "dv_links": self._load_links(),
        })

    def generate_usp_hub(self) -> str:
        return self.template.render("dv/usp_hub.sql.j2", {
            "core_db_name": self.core_db_name,
            "psa_db_name": self.psa_db_name,
            "hash_tail": self.hash_tail,
            "dv_hubs": self._load_hubs(),
        })

    def generate_usp_sat(self) -> str:
        return self.template.render("dv/usp_sat.sql.j2", {
            "core_db_name": self.core_db_name,
            "psa_db_name": self.psa_db_name,
            "hash_tail": self.hash_tail,
            "dv_sats": self._load_sats(),
        })

    def generate_usp_link(self) -> str:
        return self.template.render("dv/usp_link.sql.j2", {
            "core_db_name": self.core_db_name,
            "psa_db_name": self.psa_db_name,
            "hash_tail": self.hash_tail,
            "dv_links": self._load_links(),
        })

    def generate_all(self) -> dict[str, str]:
        return {
            "dv_hub": self.generate_hub_table(),
            "dv_sat": self.generate_sat_table(),
            "dv_link": self.generate_link_table(),
            "dv_usp_hub": self.generate_usp_hub(),
            "dv_usp_sat": self.generate_usp_sat(),
            "dv_usp_link": self.generate_usp_link(),
        }

    def generate_combined(self) -> str:
        parts = self.generate_all()
        return "\n\n".join(parts.values())

    def generate_execute_flow(self) -> str:
        return self.template.render("dv/execute_flow.sql.j2", {
            "core_db_name": self.core_db_name,
            "dv_hubs": self._load_hubs(),
            "dv_sats": self._load_sats(),
            "dv_links": self._load_links(),
        })