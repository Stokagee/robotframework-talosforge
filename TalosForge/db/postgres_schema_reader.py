"""
PostgreSQL schema reader for TalosForge.

Tento modul poskytuje čtečku schémat pro PostgreSQL databáze.
Používá information_schema k získání metadat o tabulkách a mapuje
PostgreSQL typy na JSON Schema.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_schema_reader import BaseSchemaReader

logger = logging.getLogger(__name__)

# Zkusíme importovat psycopg2, pokud není k dispozici, nastavíme příznak
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# Import výjimek pro logování chyb
try:
    from TalosForge.core.exceptions import TalosForgeException
except ImportError:
    # Fallback pro testování
    class TalosForgeException(Exception):
        pass

try:
    from TalosForge.utils.logger import log_error, log_warning
except ImportError:
    # Fallback pro testování
    def log_error(msg: str) -> None:
        logger.error(msg)

    def log_warning(msg: str) -> None:
        logger.warning(msg)


# Mapování PostgreSQL datových typů na JSON Schema
# None znamená, že typ je auto-generated a neměl by být v generated data
TYPE_MAP: Dict[str, Optional[Dict[str, Any]]] = {
    # Integer types
    'integer': {'type': 'integer'},
    'bigint': {'type': 'integer'},
    'smallint': {'type': 'integer'},
    'int2': {'type': 'integer'},
    'int4': {'type': 'integer'},
    'int8': {'type': 'integer'},
    # Auto-generated - vrátí None pro označení jako system-generated
    'serial': None,
    'bigserial': None,
    # Numeric types
    'numeric': {'type': 'number'},
    'decimal': {'type': 'number'},
    'real': {'type': 'number'},
    'double precision': {'type': 'number'},
    'float4': {'type': 'number'},
    'float8': {'type': 'number'},
    # String types
    'character varying': {'type': 'string'},
    'varchar': {'type': 'string'},
    'text': {'type': 'string'},
    'bpchar': {'type': 'string'},
    'char': {'type': 'string'},
    'character': {'type': 'string'},
    # Boolean
    'boolean': {'type': 'boolean'},
    'bool': {'type': 'boolean'},
    # Date/Time
    'date': {'type': 'string', 'format': 'date'},
    'timestamp': {'type': 'string', 'format': 'date-time'},
    'timestamp without time zone': {'type': 'string', 'format': 'date-time'},
    'timestamp with time zone': {'type': 'string', 'format': 'date-time'},
    'timestamptz': {'type': 'string', 'format': 'date-time'},
    'time': {'type': 'string', 'format': 'time'},
    'time without time zone': {'type': 'string', 'format': 'time'},
    'time with time zone': {'type': 'string', 'format': 'time'},
    'timetz': {'type': 'string', 'format': 'time'},
    # UUID
    'uuid': {'type': 'string', 'format': 'uuid'},
    # JSON
    'json': {'type': 'object'},
    'jsonb': {'type': 'object'},
    # Binary
    'bytea': {'type': 'string', 'contentEncoding': 'base64'},
    # Array types (jednoduchá reprezentace)
    'array': {'type': 'array'},
    '_text': {'type': 'array', 'items': {'type': 'string'}},
    '_int4': {'type': 'array', 'items': {'type': 'integer'}},
    # Custom enum types (uživatelské typy)
    'orderstatus': {'type': 'string'},
}


class PostgresSchemaReader(BaseSchemaReader):
    """
    Čtečka schémat pro PostgreSQL databáze.

    Tato třída načítá strukturu tabulky z PostgreSQL databáze
    a konvertuje ji na JSON Schema formát.

    Attributes:
        dsn: Connection string pro PostgreSQL.
        schema: Název schématu (default: "public").
        table: Název tabulky.
        exclude_columns: Seznam názvů sloupců, které mají být vyloučeny.
        conn: Aktivní databázové připojení.

    Example:
        >>> reader = PostgresSchemaReader(
        ...     dsn="host=localhost port=5432 dbname=test user=postgres password=postgres",
        ...     schema="public",
        ...     table="users"
        ... )
        >>> schema = reader.load_schema()
        >>> reader.close()
    """

    def __init__(
        self,
        dsn: str,
        schema: str = "public",
        table: str = "",
        exclude_columns: Optional[List[str]] = None,
    ) -> None:
        """
        Inicializuje PostgreSQL čtečku schémat.

        Args:
            dsn: PostgreSQL connection string (např. "host=localhost port=5432...").
            schema: Název schématu v databázi (default: "public").
            table: Název tabulky pro čtení schématu.
            exclude_columns: Volitelný seznam sloupců, které mají být vyloučeny.

        Raises:
            TalosForgeException: Pokud není nainstalován psycopg2.
        """
        if not PSYCOPG2_AVAILABLE:
            log_error(
                "psycopg2 is not installed. "
                "Install with: pip install psycopg2-binary"
            )
            raise TalosForgeException(
                "psycopg2 is required for PostgreSQL support. "
                "Install with: pip install psycopg2-binary"
            )

        self.dsn = dsn
        self.schema = schema
        self.table = table
        self.exclude_columns = exclude_columns or []
        self._conn: Optional[Any] = None

    def _get_connection(self) -> Any:
        """
        Vytvoří nebo vrátí existující databázové připojení.

        Returns:
            psycopg2 connection objekt.

        Raises:
            TalosForgeException: Pokud se nepodaří připojit k databázi.
        """
        if self._conn is None:
            try:
                self._conn = psycopg2.connect(self.dsn)
                logger.info(f"Connected to PostgreSQL database for schema {self.schema}.{self.table}")
            except Exception as e:
                log_error(f"Failed to connect to PostgreSQL: {e}")
                raise TalosForgeException(f"Failed to connect to PostgreSQL: {e}")
        return self._conn

    @staticmethod
    def _is_auto_generated(column_default: Optional[str], is_identity: str) -> bool:
        """
        Detekuje, zda je sloupec auto-generated (SERIAL nebo IDENTITY).

        Args:
            column_default: Hodnota z column_default (např. "nextval('users_id_seq')").
            is_identity: Hodnota z is_identity ('YES' nebo 'NO').

        Returns:
            True pokud je sloupec auto-generated, jinak False.

        Example:
            >>> PostgresSchemaReader._is_auto_generated("nextval('seq')", 'NO')
            True
            >>> PostgresSchemaReader._is_auto_generated(None, 'YES')
            True
            >>> PostgresSchemaReader._is_auto_generated(None, 'NO')
            False
        """
        if is_identity == 'YES':
            return True
        if column_default and 'nextval(' in column_default:
            return True
        return False

    def _get_column_metadata(self) -> List[Dict[str, Any]]:
        """
        Získá metadata o sloupcích z information_schema.

        Returns:
            Seznam slovníků s metadaty o každém sloupci.

        Raises:
            TalosForgeException: Pokud se nepodaří načíst metadata.
        """
        query = """
            SELECT
                c.column_name,
                c.udt_name,
                c.is_nullable,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.column_default,
                c.is_identity,
                pgd.description AS column_description
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_class pc
                ON pc.relname = c.table_name
                AND pc.relnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = c.table_schema)
            LEFT JOIN pg_catalog.pg_attribute pa
                ON pa.attrelid = pc.oid AND pa.attname = c.column_name
            LEFT JOIN pg_catalog.pg_description pgd
                ON pgd.objoid = pa.attrelid AND pgd.objsubid = pa.attnum
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(query, (self.schema, self.table))
                columns = []
                for row in cur.fetchall():
                    columns.append({
                        'column_name': row[0],
                        'udt_name': row[1],
                        'is_nullable': row[2],
                        'character_maximum_length': row[3],
                        'numeric_precision': row[4],
                        'numeric_scale': row[5],
                        'column_default': row[6],
                        'is_identity': row[7],
                        'column_description': row[8],
                    })
                logger.info(f"Loaded metadata for {len(columns)} columns from {self.schema}.{self.table}")
                return columns
        except Exception as e:
            log_error(f"Failed to load column metadata: {e}")
            raise TalosForgeException(f"Failed to load column metadata: {e}")

    def _map_type_to_json_schema(
        self,
        udt_name: str,
        column_name: str,
        is_nullable: str,
        column_default: Optional[str],
        is_identity: str,
        column_description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mapuje PostgreSQL typ na JSON Schema.

        Args:
            udt_name: Název PostgreSQL typu (např. 'varchar', 'integer').
            column_name: Název sloupce.
            is_nullable: 'YES' nebo 'NO'.
            column_default: Výchozí hodnota sloupce.
            is_identity: 'YES' nebo 'NO'.
            column_description: Komentář sloupce z pg_description (volitelné).

        Returns:
            JSON Schema pro sloupec nebo None pro auto-generated sloupce.
        """
        # Detekce auto-generated sloupců
        if self._is_auto_generated(column_default, is_identity):
            logger.debug(f"Column '{column_name}' is auto-generated, marking as readOnly")
            return {
                "type": "integer",
                "readOnly": True,
                "x-system-generated": True
            }

        # Získání mapování typu
        json_schema = TYPE_MAP.get(udt_name.lower())

        if json_schema is None:
            log_warning(
                f"Unknown PostgreSQL type '{udt_name}' for column '{column_name}'. "
                f"Using fallback type 'string'."
            )
            result = {"type": "string"}
        else:
            result = json_schema.copy() if isinstance(json_schema, dict) else None

        # Přidat description pokud existuje (pro AI generování)
        if result and column_description:
            result["description"] = column_description

        return result

    def load_schema(self) -> Dict[str, Any]:
        """
        Načte schéma databázové tabulky a vrátí JSON Schema strukturu.

        Returns:
            Slovník reprezentující JSON Schema pro tabulku.

        Raises:
            TalosForgeException: Pokud se nepodaří načíst schéma.
        """
        if not self.table:
            log_error("Table name is required for loading schema")
            raise TalosForgeException("Table name is required for loading schema")

        # Získání metadat sloupců
        columns_metadata = self._get_column_metadata()

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for col_meta in columns_metadata:
            col_name = col_meta['column_name']

            # Vyloučení sloupců
            if col_name in self.exclude_columns:
                logger.info(f"Excluding column '{col_name}' from schema")
                continue

            # Mapování typu na JSON Schema
            json_schema = self._map_type_to_json_schema(
                udt_name=col_meta['udt_name'],
                column_name=col_name,
                is_nullable=col_meta['is_nullable'],
                column_default=col_meta['column_default'],
                is_identity=col_meta['is_identity'],
                column_description=col_meta.get('column_description'),
            )

            # Auto-generated sloupce (SERIAL, IDENTITY) - přeskočíme ve výstupu
            if json_schema is None:
                logger.info(f"Skipping auto-generated column '{col_name}' in schema")
                continue

            # Přidání maxLength pro string typy s omezenou délkou
            if json_schema.get('type') == 'string' and col_meta['character_maximum_length']:
                json_schema['maxLength'] = col_meta['character_maximum_length']

            properties[col_name] = json_schema

            # Required pole (NOT NULL bez DEFAULT)
            if col_meta['is_nullable'] == 'NO' and col_meta['column_default'] is None:
                required.append(col_name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        logger.info(
            f"Generated JSON Schema for {self.schema}.{self.table} "
            f"with {len(properties)} properties and {len(required)} required fields"
        )

        return schema

    def close(self) -> None:
        """Zavře databázové připojení, pokud je otevřené."""
        if self._conn is not None:
            try:
                self._conn.close()
                logger.info(f"Closed PostgreSQL connection for {self.schema}.{self.table}")
            except Exception as e:
                log_warning(f"Error closing database connection: {e}")
            finally:
                self._conn = None


__all__ = ['PostgresSchemaReader', 'TYPE_MAP']
