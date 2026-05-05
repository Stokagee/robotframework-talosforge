"""
Generátor testovacích dat.

Tento modul poskytuje DataGenerator třídu pro generování testovacích dat
na základě JSON Schema pomocí knihovny Faker.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from faker import Faker
from rapidfuzz import fuzz, process

from .ai_generator import AIGenerator
from .config import FAKER_LOCALE

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Výsledek parsování názvu pole.

    Attributes:
        field_type: Detekovaný typ (např. 'phone', 'email').
        confidence: Confidence (0-1).
        method: Metoda detekce ('token', 'fuzzy', 'exact', 'fallback').
        is_collection: True = generovat pole.
    """
    field_type: str
    confidence: float
    method: str
    is_collection: bool


class FuzzyFieldMatcher:
    """Fuzzy matcher pro názvy polí pomocí RapidFuzz."""

    def __init__(self, known_fields: Dict[str, List[str]]):
        """Inicializuje matcher se známými poli.

        Args:
            known_fields: Slovník mapující canonical název na varianty.
                Příklad: {"email": ["email", "mail", "email_address"], ...}
        """
        self.all_variants: List[Tuple[str, str]] = []
        for canonical, variants in known_fields.items():
            for variant in variants:
                self.all_variants.append((variant, canonical))

    def match(self, field_name: str, threshold: float = 85.0) -> Tuple[Optional[str], float]:
        """Matchuje název pole na canonical název.

        Args:
            field_name: Název pole pro matchování.
            threshold: Minimální skóre (0-100).

        Returns:
            (canonical_name, score) nebo (None, 0).
        """
        if not self.all_variants:
            return None, 0.0

        results = process.extract(
            field_name,
            self.all_variants,
            scorer=fuzz.WRatio,
            limit=1
        )

        if results and results[0][1] >= threshold:
            canonical_name = results[0][0][1]
            score = results[0][1]
            return canonical_name, score

        return None, 0.0


class UniversalFieldParser:
    """Univerzální parser názvů polí.

    Strategie (v pořadí priority):
    1. Token-based N-gram matching (nejrychlejší).
    2. RapidFuzz fuzzy matching (střední rychlost, řeší překlepy).
    3. Fallback (obecný string).

    Example:
        >>> parser = UniversalFieldParser()
        >>> result = parser.parse("customer_name")
        >>> result.field_type
        'full_name'
    """

    # Multi-token patterns (nejvyšší priorita - nejprve zkontrolovat)
    MULTI_PATTERNS: Dict[Tuple[str, ...], str] = {
        # 2-gram patterns
        ('first', 'name'): 'first_name',
        ('last', 'name'): 'last_name',
        ('full', 'name'): 'full_name',
        ('given', 'name'): 'first_name',
        ('family', 'name'): 'last_name',
        ('user', 'name'): 'username',
        ('phone', 'number'): 'phone',
        ('postal', 'code'): 'zip',
        ('street', 'name'): 'street',
        ('zip', 'code'): 'zip',
        ('ip', 'address'): 'ip',
        ('mac', 'address'): 'mac',
        ('host', 'name'): 'hostname',
        ('api', 'key'): 'token',
        ('account', 'number'): 'account',
    }

    # Semantic patterns - 1-gram (základní tokeny)
    PATTERNS: Dict[str, str] = {
        # Email a komunikace
        'email': 'email',
        'mail': 'email',
        'e-mail': 'email',

        # Telefon
        'phone': 'phone',
        'tel': 'phone',
        'telephone': 'phone',
        'mobile': 'phone',
        'telefon': 'phone',

        # Jméno - "name" alone means full_name, but in combination it's handled by MULTI_PATTERNS
        'name': 'full_name',
        'jmeno': 'full_name',
        'fname': 'first_name',
        'firstname': 'first_name',
        'krestni': 'first_name',
        'lname': 'last_name',
        'lastname': 'last_name',
        'surname': 'last_name',
        'prijmeni': 'last_name',

        # Adresa
        'address': 'address',
        'addr': 'address',
        'adresa': 'address',
        'street': 'street',
        'ulice': 'street',
        'city': 'city',
        'mesto': 'city',
        'zip': 'zip',
        'psc': 'zip',
        'postcode': 'zip',

        # Organizace
        'company': 'company',
        'firma': 'company',
        'organization': 'company',
        'spolecnost': 'company',
        'employer': 'company',
        'department': 'department',
        'oddeleni': 'department',

        # Čas
        'date': 'date',
        'datum': 'date',
        'time': 'time',
        'datetime': 'datetime',
        'timestamp': 'datetime',

        # Identifikátory
        'uuid': 'uuid',
        'id': 'id',
        'code': 'code',
        'kod': 'code',
        'sku': 'code',

        # WWW
        'url': 'url',
        'link': 'url',
        'website': 'url',
        'domain': 'domain',
        'hostname': 'hostname',

        # Finance
        'price': 'price',
        'cena': 'price',
        'cost': 'price',
        'currency': 'currency',
        'mena': 'currency',
        'account': 'account',

        # Stav a priority
        'status': 'status',
        'state': 'status',
        'priority': 'priority',
        'priorita': 'priority',
        'level': 'level',

        # Speciální
        'tags': 'tags',
        'tag': 'tags',
        'categories': 'categories',
        'category': 'categories',
        'kategorie': 'categories',
        'type': 'type',
        'druh': 'type',
        'kind': 'type',
    }

    # Canonical fields s variantami pro RapidFuzzy
    CANONICAL_FIELDS: Dict[str, List[str]] = {
        "email": ["email", "email_address", "e-mail", "mail", "emailadress"],
        "first_name": ["first_name", "firstname", "given_name", "fname", "krestni_jmeno"],
        "last_name": ["last_name", "lastname", "surname", "family_name", "lname", "prijmeni"],
        "full_name": ["name", "fullname", "full_name", "jmeno", "cele_jmeno"],
        "phone": ["phone", "telephone", "tel", "phone_number", "mobile", "telefon", "mobil"],
        "address": ["address", "addr", "street_address", "adresa"],
        "street": ["street", "ulice", "street_name"],
        "city": ["city", "mesto", "town"],
        "zip": ["zip", "postcode", "postal_code", "psc", "postal"],
        "state": ["state", "region", "kraj"],
        "country": ["country", "zeme", "země", "country_code", "nation"],
        "company": ["company", "organization", "employer", "firm", "firma", "spolecnost"],
        "department": ["department", "oddeleni", "dept"],
        "position": ["position", "role", "job", "pozice", "job_title"],
        "username": ["username", "user_name", "login", "uzivatelske_jmeno", "uid"],
        "date": ["date", "datum"],
        "time": ["time", "cas"],
        "datetime": ["datetime", "timestamp", "created_at", "updated_at", "deleted_at"],
        "title": ["title", "titul", "nadpis", "subject", "heading"],
        "description": ["description", "popis", "desc"],
        "content": ["content", "obsah", "message", "zprava", "text", "body"],
        "comment": ["comment", "komentar", "note", "poznamka", "remarks"],
        "id": ["id", "identifier", "pk"],
        "uuid": ["uuid", "guid", "unique_id"],
        "code": ["code", "kod", "sku", "isbn", "barcode", "isbn13"],
        "url": ["url", "link", "website", "web", "uri", "href"],
        "domain": ["domain", "domena", "host"],
        "hostname": ["hostname", "host", "server_name"],
        "ip": ["ip", "ipv4", "ip_address"],
        "ipv6": ["ipv6", "ip6", "ipv6_address"],
        "mac": ["mac", "mac_address", "hardware_address"],
        "port": ["port", "port_number"],
        "user_agent": ["user_agent", "ua", "browser", "useragent"],
        "token": ["token", "api_key", "apikey", "bearer_token", "access_token"],
        "price": ["price", "cena", "cost", "amount", "value"],
        "currency": ["currency", "mena", "curr", "ccy"],
        "account": ["account", "ucet", "iban", "bank_account"],
        "status": ["status", "state", "stav"],
        "priority": ["priority", "priorita", "prio"],
        "level": ["level", "uroven", "lvl"],
        "tags": ["tags", "tag", "labels", "label"],
        "categories": ["categories", "category", "kategorie", "kat"],
        "type": ["type", "druh", "kind", "class"],
    }

    # Fields that should always generate collections
    COLLECTION_FIELDS: List[str] = [
        'tags', 'tag', 'categories', 'category', 'kategorie',
        'items', 'list', 'array', 'set',
    ]

    # Prefixes indicating collection
    COLLECTION_PREFIXES: List[str] = [
        'required_', 'optional_', 'all_', 'allowed_',
    ]

    def __init__(self):
        """Inicializuje UniversalFieldParser."""
        self.fuzzy_matcher = FuzzyFieldMatcher(self.CANONICAL_FIELDS)
        logger.debug("UniversalFieldParser inicializován")

    def tokenize(self, field_name: str) -> List[str]:
        """Rozdělí název pole na tokeny.

        Podporuje snake_case, camelCase, PascalCase, kebab-case.

        Args:
            field_name: Název pole.

        Returns:
            Seznam tokenů.

        Example:
            >>> parser = UniversalFieldParser()
            >>> parser.tokenize("customer_name")
            ['customer', 'name']
            >>> parser.tokenize("customerHomePhone")
            ['customer', 'home', 'phone']
        """
        if not field_name:
            return []

        # Nejprve rozdělit camelCase PŘED lowercasing
        # Insert underscore between lowercase and uppercase letters
        camel_split = re.sub(r'([a-z])([A-Z])', r'\1_\2', field_name)
        # Also handle PascalCase (uppercase followed by lowercase)
        camel_split = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', camel_split)

        # Teď lowercase a split na separátorech
        normalized = camel_split.lower()
        parts = re.split(r'[_\-\.\s]+', normalized)

        return [t for t in parts if t]

    def _detect_collection(self, tokens: List[str], field_name: str) -> bool:
        """Detekuje zda jde o kolekci.

        Args:
            tokens: Tokeny z názvu pole.
            field_name: Původní název pole.

        Returns:
            True pokud jde o kolekci.
        """
        field_lower = field_name.lower()

        # Prefixy (nejsilnější indikátor)
        if any(field_lower.startswith(prefix) for prefix in self.COLLECTION_PREFIXES):
            return True

        # Plurální tokeny (konkrétní seznamy)
        plural_indicators = ['tags', 'items', 'categories', 'users', 'list', 'array',
                            'tags', 'values', 'keys', 'entries', 'elements', 'options']
        if any(token in plural_indicators for token in tokens):
            return True

        # Sufixy (ale jen konkrétní, ne obecné "s")
        if field_lower.endswith(('_list', '_array', '_set', '_items')):
            return True

        # Tokeny končící na "s" kromě výjimek (singular words ending with s)
        singular_words_ending_s = ['address', 'adresa', 'status', 'state',
                                   'news', 'series', 'species', 'class',
                                   'bus', 'gas', 'glass', 'grass']
        for token in tokens:
            if token.endswith('s') and token not in singular_words_ending_s:
                # Potenciální plurál - ověřit délku (alespoň 3 znaky)
                if len(token) >= 3:
                    return True

        return False

    def parse(self, field_name: str) -> ParseResult:
        """Main parsing method.

        Args:
            field_name: Název pole.

        Returns:
            ParseResult s detekovaným typem a confidence.
        """
        if not field_name:
            return ParseResult(
                field_type='string',
                confidence=0.0,
                method='fallback',
                is_collection=False
            )

        # 1. Token-based matching (nejrychlejší)
        tokens = self.tokenize(field_name)
        is_collection = self._detect_collection(tokens, field_name)

        # Nejprve zkusit multi-token patterns (nejvyšší priorita)
        if len(tokens) >= 2:
            tokens_tuple = tuple(tokens)
            # Zkusit 2-gram combinations
            for i in range(len(tokens_tuple) - 1):
                bigram = (tokens_tuple[i], tokens_tuple[i + 1])
                if bigram in self.MULTI_PATTERNS:
                    field_type = self.MULTI_PATTERNS[bigram]
                    return ParseResult(
                        field_type=field_type,
                        confidence=0.95,
                        method='token',
                        is_collection=is_collection
                    )

        # Pak zkusit single-token patterns
        for token in tokens:
            if token in self.PATTERNS:
                field_type = self.PATTERNS[token]
                return ParseResult(
                    field_type=field_type,
                    confidence=0.90,
                    method='token',
                    is_collection=is_collection
                )

        # 2. Fuzzy matching (pro překlepy a varianty)
        canonical, score = self.fuzzy_matcher.match(field_name.lower())
        if canonical and score >= 85:
            return ParseResult(
                field_type=canonical,
                confidence=score / 100,
                method='fuzzy',
                is_collection=is_collection
            )

        # 3. Fallback - žádná shoda
        return ParseResult(
            field_type='string',
            confidence=0.0,
            method='fallback',
            is_collection=is_collection
        )


class DataGenerator:
    """
    Generuje data podle JSON Schema pomocí Fakeru.

    Tato třída poskytuje hlavní generovací logiku pro TalosForge.
    Podporuje všechny standardní JSON Schema typy a omezení.

    Example:
        >>> generator = DataGenerator()
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> data = generator.generate(schema)
        >>> print(data)
        {'name': 'John Doe'}
    """

    def __init__(self):
        """Inicializuje DataGenerator s Faker instancí, AIGenerator a UniversalFieldParser."""
        self.fake = Faker(FAKER_LOCALE)
        self.ai_generator = AIGenerator()
        self.field_parser = UniversalFieldParser()
        logger.debug(f"DataGenerator inicializován s locale: {FAKER_LOCALE}")
        logger.debug(f"AI dostupný: {self.ai_generator.is_available()}")

    def generate(
        self, schema: Dict[str, Any], target: str = "api", use_ai: bool = False
    ) -> Any:
        """
        Generuje data podle JSON Schema.

        Toto je hlavní dispatcher, který volá příslušné metody pro generování
        podle typu dat ve schématu. Pokud je use_ai=True a AI je k dispozici,
        použije AI generování pro složité případy.

        Args:
            schema: JSON Schema slovník.
            target: "api" nebo "ui" - formát výstupu.
            use_ai: Pokud True, povolí AI generování pro složité případy.

        Returns:
            Vygenerovaná data (slovník, seznam, nebo primitivní typ).

        Raises:
            TalosForgeException: Pokud typ není podporován.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "string", "minLength": 5}
            >>> result = generator.generate(schema)
            >>> print(len(result) >= 5)
            True
        """
        # 1. ENUM priorita
        if "enum" in schema:
            return self._handle_enum(schema)

        # 2. EXAMPLES priorita
        if value := self._get_examples_value(schema):
            return value

        # 3. AI priorita (pokud je povoleno)
        if use_ai and self.ai_generator.is_available() and self._should_use_ai(schema):
            try:
                logger.debug("Používám AI generování")
                return self.ai_generator.generate(
                    schema, target, schema.get("description")
                )
            except Exception as e:
                logger.warning(f"AI generování selhalo, používám Faker: {e}")
                # Fallback na Faker

        # Získat typ ze schématu
        schema_type = schema.get("type")

        # Pokud není typ, pokusíme se odvodit z jiných vlastností
        if schema_type is None:
            if "properties" in schema:
                schema_type = "object"
            elif "items" in schema:
                schema_type = "array"
            else:
                logger.warning("Schéma nemá definovaný typ, vracím None")
                return None

        # Dispatch podle typu
        if schema_type == "string":
            return self._generate_string(schema)
        elif schema_type == "integer":
            return self._generate_integer(schema)
        elif schema_type == "number":
            return self._generate_number(schema)
        elif schema_type == "boolean":
            return self._generate_boolean(schema)
        elif schema_type == "array":
            return self._generate_array(schema, target, use_ai)
        elif schema_type == "object":
            return self._generate_object(schema, target, use_ai)
        else:
            logger.warning(f"Nepodporovaný typ: {schema_type}")
            return None

    def _get_examples_value(self, schema: Dict[str, Any]) -> Any:
        """
        Získá náhodnou hodnotu z examples pole.

        Podporuje pouze "examples" (JSON Schema draft 2019-09+).
        Pole "example" (OpenAPI 3.x) se ignoruje, protože obsahuje jen jednu
        hodnotu a blokovala by Faker generování. Místo toho se pokračuje
        do Faker, který vygeneruje různorodá data.

        Args:
            schema: JSON Schema slovník.

        Returns:
            Náhodná hodnota z examples nebo None (pokud examples neexistuje).

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "string", "examples": ["a", "b", "c"]}
            >>> result = generator._get_examples_value(schema)
            >>> result in ["a", "b", "c"]
            True
        """
        if "examples" in schema:
            examples = schema["examples"]
            if isinstance(examples, list) and examples:
                return self.fake.random_element(examples)

        # "example" (singulár) se ignoruje - necháme Faker generovat
        return None

    def _is_nullable(self, schema: Dict[str, Any]) -> bool:
        """
        Zjistí zda je pole nullable (OpenAPI specification).

        Pokud je nullable=True, vrátí s určitou pravděpodobností (20%) None
        místo generované hodnoty.

        Args:
            schema: JSON Schema slovník.

        Returns:
            True pokud je nullable, jinak False.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "string", "nullable": True}
            >>> generator._is_nullable(schema)
            True
        """
        return schema.get("nullable", False)

    def _get_context_value(self, field_name: str, prop_schema: Dict[str, Any]) -> Any:
        """
        Generuje hodnotu podle kontextu názvu pole.

        Používá UniversalFieldParser pro inteligentní rozpoznání typu pole.
        Podporované kategorie (50+ field variants):
        - Osobní údaje: name, first_name, last_name, username, email, phone
        - Adresa: address, street, city, zip, state, country, coordinates (lat, lng)
        - Organizace: company, department, position
        - Čas: date, time, datetime, created_at, updated_at
        - Obsah: title, description, content, message, subject
        - Identifikátory: id, uuid, code, sku, isbn
        - WWW: url, link, website, domain, hostname
        - Finance: price, cost, currency, account, iban
        - Technické: ip, port, user_agent, mac, token
        - Stav: status, state, priority, level, role
        - Speciální: tags, categories, type, category

        Args:
            field_name: Název pole.
            prop_schema: JSON Schema pro pole.

        Returns:
            Vygenerovaná hodnota nebo None.

        Example:
            >>> generator = DataGenerator()
            >>> result = generator._get_context_value("name", {"type": "string"})
            >>> isinstance(result, str)
            True
            >>> " " in result  # celé jméno obsahuje mezeru
            True
        """
        if not field_name:
            return None

        # 1. Univerzální parser (nové) - pro prefixy, fuzzy matching, token matching
        result = self.field_parser.parse(field_name)

        if result.confidence >= 0.75:  # Threshold pro použití parseru
            logger.debug(
                f"Smart matched '{field_name}' -> '{result.field_type}' "
                f"(conf: {result.confidence:.2f}, method: {result.method})"
            )

            # Map field type to Faker method
            faker_map: Dict[str, Any] = {
                'email': lambda: self.fake.email(),
                'phone': lambda: self.fake.phone_number(),
                'full_name': lambda: f"{self.fake.first_name()} {self.fake.last_name()}",
                'first_name': lambda: self.fake.first_name(),
                'last_name': lambda: self.fake.last_name(),
                'username': lambda: self.fake.user_name(),
                'address': lambda: self.fake.address(),
                'street': lambda: self.fake.street_name(),
                'city': lambda: self.fake.city(),
                'zip': lambda: self.fake.postcode(),
                'state': lambda: self.fake.state(),
                'country': lambda: self.fake.country(),
                'company': lambda: self.fake.company(),
                'department': lambda: self.fake.catch_phrase(),
                'position': lambda: self.fake.job(),
                'date': lambda: self.fake.date(),
                'time': lambda: self.fake.time(),
                'datetime': lambda: self.fake.date_time().isoformat(),
                'title': lambda: self.fake.sentence()[:50],
                'description': lambda: self.fake.text(max_nb_chars=200),
                'content': lambda: self.fake.text(max_nb_chars=500),
                'comment': lambda: self.fake.sentence(),
                'id': lambda: self.fake.random_int(min=1, max=999999),
                'uuid': lambda: str(self.fake.uuid4()),
                'code': lambda: self.fake.uuid4()[:8].upper(),
                'url': lambda: self.fake.url(),
                'domain': lambda: self.fake.domain_name(),
                'hostname': lambda: self.fake.hostname(),
                'price': lambda: round(self.fake.pyfloat(min_value=0, max_value=10000), 2),
                'currency': lambda: "CZK",
                'account': lambda: f"CZ{self.fake.random_int(min=100000000, max=999999999)}",
                'ip': lambda: self.fake.ipv4(),
                'ipv6': lambda: self.fake.ipv6(),
                'mac': lambda: self.fake.mac_address(),
                'port': lambda: self.fake.random_int(min=1024, max=65535),
                'user_agent': lambda: self.fake.user_agent(),
                'token': lambda: self.fake.uuid4(),
                'status': lambda: self.fake.random_element(
                    ["active", "inactive", "pending", "blocked", "online", "offline"]
                ),
                'priority': lambda: self.fake.random_element(
                    ["low", "medium", "high", "urgent", "critical"]
                ),
                'level': lambda: self.fake.random_int(min=1, max=10),
                'tags': lambda: self.fake.random_element(
                    ["vip", "urgent", "normal", "low", "bike", "car", "fragile_ok", "fast", "priority", "standard"]
                ),
                'categories': lambda: self.fake.word(),
                'type': lambda: self.fake.word(),
            }

            if result.field_type in faker_map:
                value = faker_map[result.field_type]()
                # POZNÁMKA: is_collection flag se ignoruje v _get_context_value
                # protože rozhodnutí o typu pole/objektu se dělá na úrovni schématu
                # Zde vždy vracíme jednu hodnotu
                return value

        # 2. PŮVODNÍ: Přesné shody (pro kompatibilitu a výkon)
        # Zůstává pro kompatibilitu a jako rychlá cesta pro běžné názvy polí
        field_lower = field_name.lower()

        # Osobní údaje
        if field_lower in ["name", "jmeno", "fullname", "full_name"]:
            return f"{self.fake.first_name()} {self.fake.last_name()}"
        elif field_lower in ["first_name", "krestni_jmeno", "firstname"]:
            return self.fake.first_name()
        elif field_lower in ["last_name", "prijmeni", "lastname", "surname"]:
            return self.fake.last_name()
        elif field_lower in ["phone", "telephone", "telefon", "phone_number", "mobile"]:
            return self.fake.phone_number()
        elif field_lower == "email":
            return self.fake.email()
        elif field_lower in ["username", "uzivatelske_jmeno", "user_name", "login"]:
            return self.fake.user_name()

        # Adresa
        elif field_lower in ["address", "adresa"]:
            return self.fake.address()
        elif field_lower in ["street", "ulice"]:
            return self.fake.street_name()
        elif field_lower in ["city", "mesto"]:
            return self.fake.city()
        elif field_lower in ["zip", "psc", "postcode", "postal_code"]:
            return self.fake.postcode()
        elif field_lower in ["state", "region", "kraj"]:
            return self.fake.state()
        elif field_lower in ["country", "zeme", "country_code"]:
            return self.fake.country()
        elif field_lower in ["lat", "latitude"]:
            return self.fake.latitude()
        elif field_lower in ["lng", "lon", "longitude"]:
            return self.fake.longitude()

        # Organizace
        elif field_lower in ["company", "spolecnost", "firma", "organization"]:
            return self.fake.company()
        elif field_lower in ["department", "oddeleni"]:
            return self.fake.catch_phrase()
        elif field_lower in ["position", "role", "pozice"]:
            return self.fake.job()

        # Časové údaje
        elif field_lower in ["date", "datum"]:
            return self.fake.date()
        elif field_lower == "time":
            return self.fake.time()
        elif field_lower in ["datetime", "timestamp", "created_at", "updated_at", "deleted_at"]:
            return self.fake.date_time().isoformat()

        # Obsah
        elif field_lower in ["title", "titul", "nadpis", "subject"]:
            return self.fake.sentence()[:50]
        elif field_lower in ["description", "popis", "desc"]:
            return self.fake.text(max_nb_chars=200)
        elif field_lower in ["content", "obsah", "message", "zprava", "text", "body"]:
            return self.fake.text(max_nb_chars=500)
        elif field_lower in ["comment", "komentar", "note", "poznamka"]:
            return self.fake.sentence()

        # Identifikátory
        elif field_lower == "id":
            return self.fake.random_int(min=1, max=999999)
        elif field_lower == "uuid":
            return str(self.fake.uuid4())
        elif field_lower in ["code", "kod", "sku", "isbn", "barcode"]:
            return self.fake.uuid4()[:8].upper()

        # WWW
        elif field_lower in ["url", "link", "website", "web"]:
            return self.fake.url()
        elif field_lower in ["domain", "domena"]:
            return self.fake.domain_name()
        elif field_lower == "hostname":
            return self.fake.hostname()

        # Finance
        elif field_lower in ["price", "cena", "cost"]:
            return round(self.fake.pyfloat(min_value=0, max_value=10000), 2)
        elif field_lower in ["currency", "mena"]:
            return "CZK"
        elif field_lower in ["account", "ucet", "iban"]:
            return f"CZ{self.fake.random_int(min=100000000, max=999999999)}"

        # Technické
        elif field_lower in ["ip", "ipv4"]:
            return self.fake.ipv4()
        elif field_lower == "ipv6":
            return self.fake.ipv6()
        elif field_lower in ["mac", "mac_address"]:
            return self.fake.mac_address()
        elif field_lower in ["port"]:
            return self.fake.random_int(min=1024, max=65535)
        elif field_lower in ["user_agent", "ua"]:
            return self.fake.user_agent()
        elif field_lower in ["token", "api_key", "apikey"]:
            return self.fake.uuid4()

        # Stav / priorita
        elif field_lower in ["status", "state"]:
            return self.fake.random_element(["active", "inactive", "pending", "blocked", "online", "offline"])
        elif field_lower in ["priority", "priorita"]:
            return self.fake.random_element(["low", "medium", "high", "urgent", "critical"])
        elif field_lower in ["level", "uroven"]:
            return self.fake.random_int(min=1, max=10)

        # Speciální
        elif field_lower in ["tags", "tag"]:
            return self.fake.random_element(["vip", "urgent", "normal", "low", "bike", "car", "fragile_ok", "fast", "priority", "standard"])
        elif field_lower in ["categories", "category", "kategorie"]:
            return self.fake.word()
        elif field_lower in ["type", "druh", "kind"]:
            return self.fake.word()

        return None

    def _generate_with_context(
        self, schema: Dict[str, Any], field_name: str = None, target: str = "api", use_ai: bool = False
    ) -> Any:
        """
        Generuje data podle JSON Schema s kontextovým názvem pole.

        Toto je interní dispatcher, který předává field_name do generovacích metod.

        Args:
            schema: JSON Schema slovník.
            field_name: Název pole pro kontextové generování.
            target: "api" nebo "ui" - formát výstupu.
            use_ai: Pokud True, povolí AI generování pro složité případy.

        Returns:
            Vygenerovaná data.
        """
        # 1. ENUM priorita
        if "enum" in schema:
            return self._handle_enum(schema)

        # 2. EXAMPLES priorita
        if value := self._get_examples_value(schema):
            return value

        # 3. AI priorita (pokud je povoleno)
        if use_ai and self.ai_generator.is_available() and self._should_use_ai(schema):
            try:
                logger.debug("Používám AI generování")
                return self.ai_generator.generate(
                    schema, target, schema.get("description")
                )
            except Exception as e:
                logger.warning(f"AI generování selhalo, používám Faker: {e}")
                # Fallback na Faker

        # Získat typ ze schématu
        schema_type = schema.get("type")

        # Pokud není typ, pokusíme se odvodit z jiných vlastností
        if schema_type is None:
            if "properties" in schema:
                schema_type = "object"
            elif "items" in schema:
                schema_type = "array"
            else:
                logger.warning("Schéma nemá definovaný typ, vracím None")
                return None

        # 4. KONTEXTOVÁ LOGIKA - před typovým dispatchem
        # Pro integer a number typy zkusíme kontextovou hodnotu
        if field_name and schema_type in ["integer", "number"]:
            if value := self._get_context_value(field_name, schema):
                return value

        # Dispatch podle typu s field_name
        if schema_type == "string":
            return self._generate_string(schema, field_name)
        elif schema_type == "integer":
            return self._generate_integer(schema)
        elif schema_type == "number":
            return self._generate_number(schema)
        elif schema_type == "boolean":
            return self._generate_boolean(schema)
        elif schema_type == "array":
            return self._generate_array_with_context(schema, field_name, target, use_ai)
        elif schema_type == "object":
            return self._generate_object(schema, target, use_ai)
        else:
            logger.warning(f"Nepodporovaný typ: {schema_type}")
            return None

    def _generate_string(self, prop_schema: Dict[str, Any], field_name: str = None) -> str:
        """
        Generuje řetězec podle JSON Schema.

        Podporuje format (email, date, uri, uuid, password), minLength, maxLength,
        a pattern. Pokud je field_name zadán, používá kontextové generování.

        Args:
            prop_schema: JSON Schema pro string vlastnost.
            field_name: Název pole pro kontextové generování.

        Returns:
            Vygenerovaný řetězec.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "string", "format": "email"}
            >>> result = generator._generate_string(schema)
            >>> '@' in result
            True
        """
        # 1. Examples priorita
        if value := self._get_examples_value(prop_schema):
            return value

        # 2. Kontextová logika (pokud je field_name zadán)
        if field_name and (value := self._get_context_value(field_name, prop_schema)):
            return value

        # 3. Získat formát
        string_format = prop_schema.get("format")

        # Generování podle formátu
        if string_format == "email":
            return self.fake.email()
        elif string_format == "date":
            return self.fake.date()
        elif string_format == "date-time":
            return self.fake.date_time().isoformat()
        elif string_format == "time":
            return self.fake.time()
        elif string_format == "uri":
            return self.fake.url()
        elif string_format == "uuid":
            return str(self.fake.uuid4())
        elif string_format == "hostname":
            return self.fake.hostname()
        elif string_format == "ipv4":
            return self.fake.ipv4()
        elif string_format == "ipv6":
            return self.fake.ipv6()
        elif string_format == "password":
            return self.fake.password()
        elif string_format == "byte":
            # Base64 encoded string
            return self.fake.byte()
        elif string_format == "phone":
            return self.fake.phone_number()

        # Omezení délky
        min_length = prop_schema.get("minLength", 1)
        max_length = prop_schema.get("maxLength", min_length + 50)

        # Generování obecného textu
        if min_length == 1 and max_length > 100:
            # Krátké slovo nebo krátká věta
            result = self.fake.word() if self.fake.boolean() else self.fake.sentence()[: max_length]
        else:
            # Generování textu s přesnou délkou
            if max_length <= 20:
                result = self.fake.word()
                while len(result) < min_length:
                    result += " " + self.fake.word()
            else:
                result = self.fake.text(max_nb_chars=max_length)
                while len(result) < min_length:
                    result += " " + self.fake.word()

        # Oříznout na max_length
        result = result[:max_length]

        # Zajistit min_length (doplnit mezerami pokud je moc krátké)
        if len(result) < min_length:
            result = result.ljust(min_length)

        # Pattern matching (základní podpora)
        pattern = prop_schema.get("pattern")
        if pattern:
            result = self._generate_by_pattern(pattern, min_length, max_length)

        return result

    def _generate_by_pattern(self, pattern: str, min_length: int, max_length: int) -> str:
        """
        Generuje řetězec podle regulárního výrazu.

        Toto je základní implementace - podporuje jednoduché patterny.
        Pro složité patterny vrací generovaný text odpovídající délce.

        Args:
            pattern: Regulární výraz.
            min_length: Minimální délka.
            max_length: Maximální délka.

        Returns:
            Řetězec odpovídající patternu (nebo co nejpodobnější).
        """
        # Základní patterny
        if pattern == "^\\d+$":
            # Pouze číslice
            length = self.fake.random_int(min=min_length, max=max_length)
            return self.fake.numerify("#" * length)
        elif pattern == "^[a-zA-Z]+$":
            # Pouze písmena
            return self.fake.pystr(min_chars=min_length, max_chars=max_length)
        elif pattern == "^[a-zA-Z0-9]+$":
            # Alfanumerické
            return self.fake.pystr(min_chars=min_length, max_chars=max_length)
        elif "\\d" in pattern and "\\d" in pattern:
            # Obsahuje číslice - zkusíme numerify
            length = self.fake.random_int(min=min_length, max=max_length)
            return self.fake.numerify("X" * length)
        else:
            # Pro složité patterny vracíme obecný text
            logger.warning(f"Složitý pattern, vracím obecný text: {pattern}")
            return self.fake.pystr(min_chars=min_length, max_chars=max_length)

    def _generate_integer(self, prop_schema: Dict[str, Any]) -> int:
        """
        Generuje integer podle JSON Schema.

        Podporuje minimum a maximum.

        Args:
            prop_schema: JSON Schema pro integer vlastnost.

        Returns:
            Vygenerované celé číslo.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "integer", "minimum": 10, "maximum": 20}
            >>> result = generator._generate_integer(schema)
            >>> 10 <= result <= 20
            True
        """
        # Examples priorita
        if value := self._get_examples_value(prop_schema):
            return value

        minimum = prop_schema.get("minimum", -1000000)
        maximum = prop_schema.get("maximum", 1000000)
        exclusive_minimum = prop_schema.get("exclusiveMinimum")
        exclusive_maximum = prop_schema.get("exclusiveMaximum")

        # Upravit minimum/maximum pro exclusive
        if exclusive_minimum is not None:
            minimum = max(minimum, exclusive_minimum + 1)
        if exclusive_maximum is not None:
            maximum = min(maximum, exclusive_maximum - 1)

        return self.fake.random_int(min=minimum, max=maximum)

    def _generate_number(self, prop_schema: Dict[str, Any]) -> float:
        """
        Generuje číslo (float) podle JSON Schema.

        Podporuje minimum a maximum.

        Args:
            prop_schema: JSON Schema pro number vlastnost.

        Returns:
            Vygenerované číslo.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "number", "minimum": 0.0, "maximum": 1.0}
            >>> result = generator._generate_number(schema)
            >>> 0.0 <= result <= 1.0
            True
        """
        # Examples priorita
        if value := self._get_examples_value(prop_schema):
            return value

        minimum = prop_schema.get("minimum", 0.0)
        maximum = prop_schema.get("maximum", 1000.0)

        return self.fake.pyfloat(min_value=minimum, max_value=maximum)

    def _generate_boolean(self, prop_schema: Dict[str, Any]) -> bool:
        """
        Generuje boolean hodnotu.

        Args:
            prop_schema: JSON Schema pro boolean vlastnost.

        Returns:
            True nebo False.

        Example:
            >>> generator = DataGenerator()
            >>> result = generator._generate_boolean({})
            >>> isinstance(result, bool)
            True
        """
        # Examples priorita
        if value := self._get_examples_value(prop_schema):
            return value

        return self.fake.pybool()

    def _generate_array(
        self, prop_schema: Dict[str, Any], target: str = "api", use_ai: bool = False
    ) -> list:
        """
        Generuje pole podle JSON Schema.

        Podporuje items (schéma prvků), minItems a maxItems.
        Rekurzivně volá generate() pro prvky pole.

        Args:
            prop_schema: JSON Schema pro array vlastnost.
            target: "api" nebo "ui".
            use_ai: Povolí AI generování.

        Returns:
            Vygenerované pole.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "array", "items": {"type": "string"}, "minItems": 2}
            >>> result = generator._generate_array(schema)
            >>> len(result) >= 2
            True
        """
        items_schema = prop_schema.get("items", {"type": "string"})
        min_items = prop_schema.get("minItems", 1)
        max_items = prop_schema.get("maxItems", min_items + 5)

        # Generovat počet prvků
        num_items = self.fake.random_int(min=min_items, max=max_items)

        result = []
        for _ in range(num_items):
            item = self.generate(items_schema, target, use_ai)
            result.append(item)

        return result

    def _generate_array_with_context(
        self, prop_schema: Dict[str, Any], field_name: str = None, target: str = "api", use_ai: bool = False
    ) -> list:
        """
        Generuje pole podle JSON Schema s kontextovým názvem pole.

        Podporuje items (schéma prvků), minItems a maxItems.
        Pro fields jako "tags" nebo "tag" omezí max_items na 5.
        Rekurzivně volá _generate_with_context() pro prvky pole.

        Args:
            prop_schema: JSON Schema pro array vlastnost.
            field_name: Název pole pro kontextové generování.
            target: "api" nebo "ui".
            use_ai: Povolí AI generování.

        Returns:
            Vygenerované pole.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "array", "items": {"type": "string"}, "minItems": 2}
            >>> result = generator._generate_array_with_context(schema, "tags")
            >>> len(result) >= 2
            True
        """
        items_schema = prop_schema.get("items", {"type": "string"})
        min_items = prop_schema.get("minItems", 1)
        max_items = prop_schema.get("maxItems", min_items + 5)

        # Pro testovací data zajistit alespoň 1 položku (pokud minItems=0)
        # Prázdná pole neposkytují hodnotu pro testování
        if min_items == 0:
            min_items = 1

        # Zajistit min <= max
        if min_items > max_items:
            max_items = min_items

        # Speciální logika pro tags - omezit max_items
        if field_name and field_name.lower() in ["tags", "tag"]:
            default_tags = ["vip", "urgent", "normal", "low", "bike", "car", "fragile_ok", "fast", "priority", "standard"]

            # 1. Zkusit example/examples na úrovni array (OpenAPI styl)
            array_examples = None
            if "examples" in prop_schema:
                examples = prop_schema["examples"]
                if isinstance(examples, list) and examples and isinstance(examples[0], list):
                    array_examples = examples[0]  # První pole z examples
            elif "example" in prop_schema:
                example = prop_schema["example"]
                if isinstance(example, list):
                    array_examples = example

            # 2. Použít nalezené example/examples, nebo items examples, nebo default
            if array_examples:
                items_schema = items_schema.copy()
                items_schema["examples"] = array_examples
                max_items = min(max_items, len(array_examples))
            elif "examples" in items_schema:
                tags = items_schema["examples"]
                max_items = min(max_items, len(tags))
            else:
                # Jinak omez na 5 a použij default tagy
                max_items = min(max_items, 5)
                items_schema = items_schema.copy()
                items_schema["examples"] = default_tags

        # Znovu zajistit min <= max (po examples handling, který může snížit max_items)
        if min_items > max_items:
            max_items = min_items

        # Generovat počet prvků
        num_items = self.fake.random_int(min=min_items, max=max_items)

        result = []
        for _ in range(num_items):
            item = self._generate_with_context(items_schema, field_name, target, use_ai)
            result.append(item)

        # Respektovat JSON Schema uniqueItems
        if prop_schema.get("uniqueItems", False):
            try:
                seen = set()
                unique_result = []
                for item in result:
                    if item not in seen:
                        seen.add(item)
                        unique_result.append(item)
                result = unique_result
            except TypeError:
                # Položky nejsou hashovatelné (např. dict), použít alternativní metodu
                # Pro objekty porovnávat podle JSON reprezentace
                unique_result = []
                seen_json = []
                for item in result:
                    item_json = json.dumps(item, sort_keys=True)
                    if item_json not in seen_json:
                        seen_json.append(item_json)
                        unique_result.append(item)
                result = unique_result

        # Sémantická pravidla: tags/categories vždy unikátní (prevence duplikátů)
        # Toto platí i když uniqueItems není nastaveno
        # Ale respektujeme minItems - pokud uniqueItems není True, povolíme duplicity
        # pro splnění minItems, ale jinak se je snažíme odstranit
        if field_name and not prop_schema.get("uniqueItems", False):
            field_lower = field_name.lower()
            tag_indicators = ["tags", "tag", "categories", "category", "kategorie", "required_tags",
                             "optional_tags", "all_tags", "allowed_tags"]

            if any(indicator in field_lower for indicator in tag_indicators):
                # Zkusit odstranit duplicity, ale zachovat min_items
                try:
                    unique_result = list(dict.fromkeys(result))
                    # Pokud máme stále alespoň min_items, použijeme unikátní verzi
                    if len(unique_result) >= min_items:
                        result = unique_result
                except TypeError:
                    # Pro nehashovatelné typy (dict, list)
                    unique_result = []
                    seen_json = []
                    for item in result:
                        item_json = json.dumps(item, sort_keys=True)
                        if item_json not in seen_json:
                            seen_json.append(item_json)
                            unique_result.append(item)
                    if len(unique_result) >= min_items:
                        result = unique_result

        return result

    def _generate_object(
        self, prop_schema: Dict[str, Any], target: str = "api", use_ai: bool = False
    ) -> dict:
        """
        Generuje objekt podle JSON Schema.

        Podporuje properties, required a default.
        Rekurzivně volá generate() pro vlastnosti.

        Args:
            prop_schema: JSON Schema pro object vlastnost.
            target: "api" nebo "ui".
            use_ai: Povolí AI generování.

        Returns:
            Vygenerovaný slovník.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"type": "string"},
            ...         "age": {"type": "integer"}
            ...     },
            ...     "required": ["name"]
            ... }
            >>> result = generator._generate_object(schema)
            >>> "name" in result
            True
        """
        properties = prop_schema.get("properties", {})
        required = prop_schema.get("required", [])
        result = {}

        # Projít všechny vlastnosti
        for prop_name, prop_schema in properties.items():
            # Vždy generovat všechna pole pro konzistentní testovací data
            # (Původní logika s 30% šancí na vynechání byla odstraněna)

            # Zkontrolovat, zda je default hodnota - používat rozumně
            if "default" in prop_schema and self.fake.boolean(chance_of_getting_true=50):
                default_value = prop_schema["default"]
                # Ignorovat prázdné defaulty - pro testování potřebujeme smysluplná data
                # Prázdné hodnoty: None, null, [], {}, ""
                if default_value not in [None, "null", [], {}, "", ""]:
                    result[prop_name] = default_value
                    continue

            # Generovat hodnotu s kontextem
            value = self._generate_with_context(prop_schema, prop_name, target, use_ai)
            result[prop_name] = value

        return result

    def _handle_enum(self, prop_schema: Dict[str, Any]) -> Any:
        """
        Zpracuje enum výčet hodnot.

        Args:
            prop_schema: JSON Schema s enum.

        Returns:
            Náhodná hodnota z enum seznamu.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "string", "enum": ["red", "green", "blue"]}
            >>> result = generator._handle_enum(schema)
            >>> result in ["red", "green", "blue"]
            True
        """
        enum_values = prop_schema.get("enum", [])
        if not enum_values:
            logger.warning("Enum je prázdný")
            return None

        return self.fake.random_element(enum_values)

    def _handle_oneof_anyof_allof(self, prop_schema: Dict[str, Any]) -> Any:
        """
        Zpracuje oneOf, anyOf, allOf konstrukce.

        Toto je základní implementace. Pro složité případy
        by měla být použita AI (Fáze 3).

        Args:
            prop_schema: JSON Schema s oneOf/anyOf/allOf.

        Returns:
            Vygenerovaná hodnota.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {
            ...     "oneOf": [
            ...         {"type": "string"},
            ...         {"type": "integer"}
            ...     ]
            ... }
            >>> result = generator._handle_oneof_anyof_allof(schema)
        """
        # oneOf - vybrat náhodně jedno schéma
        if "oneOf" in prop_schema:
            options = prop_schema["oneOf"]
            if options:
                selected = self.fake.random_element(options)
                return self.generate(selected)

        # anyOf - vybrat 1-N schémat
        if "anyOf" in prop_schema:
            options = prop_schema["anyOf"]
            if options:
                # Zatím vybereme jen jedno (zjednodušené)
                selected = self.fake.random_element(options)
                return self.generate(selected)

        # allOf - spojit všechna schémata (složité)
        if "allOf" in prop_schema:
            options = prop_schema["allOf"]
            if options:
                # Zatím vyberme první (zjednodušené)
                return self.generate(options[0])

        logger.warning("oneOf/anyOf/allOf: Žádná platná možnost")
        return None

    def _should_use_ai(self, schema: Dict[str, Any]) -> bool:
        """
        Rozhodne, zda je vhodné použít AI generování.

        AI se používá pro složité případy jako:
        - Přítomnost description (textový popis)
        - Složité pattern (regulární výrazy)
        - oneOf/anyOf/allOf konstrukce
        - Specifické formáty které Faker neumí

        Args:
            schema: JSON Schema.

        Returns:
            True pokud je vhodné použít AI, jinak False.

        Example:
            >>> generator = DataGenerator()
            >>> schema = {"type": "string", "description": "A realistic Czech name"}
            >>> generator._should_use_ai(schema)
            True
        """
        # Pokud je description, použij AI
        if "description" in schema:
            return True

        # Pokud je složitý pattern, použij AI
        pattern = schema.get("pattern")
        if pattern and len(pattern) > 20:
            # Složité patterny (delší než 20 znaků)
            return True

        # Pokud jsou oneOf/anyOf/allOf, použij AI
        if any(k in schema for k in ["oneOf", "anyOf", "allOf"]):
            return True

        # Specifické formáty které Faker neumí dobře
        unsupported_formats = ["complex-password", "czech-id", "ssn"]
        if schema.get("format") in unsupported_formats:
            return True

        return False
