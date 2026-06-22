"""Hash Key 工具 — 与 SQL Server HASHBYTES 算法保持一致"""
import hashlib


def compute_hash_key(*fields: str, hash_tail: str = "@IAMHUSKIES@") -> str:
    """
    计算 MD5 Hash Key

    算法与 SQL Server 的 HASHBYTES('MD5', ...) 保持一致：
    HK = MD5(ISNULL(TRIM(field1),'') + '@TAIL@' + ISNULL(TRIM(field2),'') + '@TAIL@')

    Returns:
        32 字符大写十六进制 MD5 字符串
    """
    raw = ""
    for field in fields:
        if field is not None:
            raw += str(field).strip() + hash_tail
        else:
            raw += hash_tail
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()