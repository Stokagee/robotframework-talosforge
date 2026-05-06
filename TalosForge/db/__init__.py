"""
Database schema readers for TalosForge.

Tento modul poskytuje registr čteček schémat pro různé databázové backendy.
Každý backend je registrován pod svým module name (např. 'psycopg2' pro PostgreSQL).
"""

from typing import Dict, Type

from .base_schema_reader import BaseSchemaReader

# Registr dostupných čteček schémat
# Klíč je název Python DB modulu (např. 'psycopg2', 'pymysql')
# Hodnota je třída čtečky schémat
DB_READERS: Dict[str, Type[BaseSchemaReader]] = {}

# Import a registrace PostgreSQL čtečky (pokud je psycopg2 k dispozici)
try:
    from .postgres_schema_reader import PostgresSchemaReader

    DB_READERS["psycopg2"] = PostgresSchemaReader
except ImportError:
    pass

# Budoucí MySQL support (odkomentovat po implementaci)
# try:
#     from .mysql_schema_reader import MySQLSchemaReader
#     DB_READERS['pymysql'] = MySQLSchemaReader
# except ImportError:
#     pass

# Budoucí Oracle support (odkomentovat po implementaci)
# try:
#     from .oracle_schema_reader import OracleSchemaReader
#     DB_READERS['oracledb'] = OracleSchemaReader
#     DB_READERS['cx_Oracle'] = OracleSchemaReader
# except ImportError:
#     pass

# Budoucí SQL Server support (odkomentovat po implementaci)
# try:
#     from .mssql_schema_reader import MSSQLSchemaReader
#     DB_READERS['pymssql'] = MSSQLSchemaReader
#     DB_READERS['pyodbc'] = MSSQLSchemaReader
# except ImportError:
#     pass


__all__ = ["BaseSchemaReader", "DB_READERS"]
