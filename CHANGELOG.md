# Changelog

Všechny významné změny projektu TalosForge budou dokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.5.0] - 2026-05-06

Sloučení (port) features z dříve odděleného Artima 0.5.0 forku do hlavní
větve. Verze tedy obsahuje BOTH (a) response-code fallback / validation
keyword z 0.4.0 main, (b) DB integraci, prance, rstr, explore mode
a další parametry z 0.5.0 forku.

### Přidáno

**Database mode (`Load Schema` + `target=db`):**
- **`TalosForge/db/`** package: `BaseSchemaReader`, `PostgresSchemaReader`
  s registrem `DB_READERS` (graceful fallback pokud psycopg2 chybí)
- Nové parametry v `Load Schema`: `db_module`, `db_name`, `db_host`,
  `db_port`, `db_user`, `db_password`, `db_schema`, `db_table`,
  `db_exclude_columns` (čárkou oddělené)
- Nový mode `target="db"` v `Generate Data From Schema` — vrací SQL
  VALUES řetězec pro `DatabaseLibrary` (např. `"'Jan', 'Novák', 25"`)

**Externí $ref resolving (prance):**
- Nový parametr `allow_external_refs` v `Load Schema` a v
  `SchemaLoader.__init__()`
- `SchemaLoader.load_openapi_spec()` a `load_openapi_spec_from_url()`
  preferují `prance.ResolvingParser` při zapnutí, s graceful fallbackem
  na základní loader

**Property-based / explore mode (hypothesis-jsonschema):**
- Nový parametr `explore` v `Generate Data From Schema`
- Nová metoda `DataGenerator.generate_explore(schema, amount)` —
  generuje edge-case varianty pro fuzz testing, vždy vrací seznam
- Automatický fallback na standardní generování pokud
  `hypothesis-jsonschema` chybí

**Regex generování (rstr):**
- `_generate_by_pattern()` nyní primárně používá `rstr.xeger()` pro
  přesné generování z regulárních výrazů s podporou
  `minLength`/`maxLength` omezení; fallback na heuristiky pokud rstr
  není k dispozici
- Změna priority generování stringů: Examples > Format > **Pattern** >
  Kontext > Obecný text (pattern má teď přednost před kontextovou
  logikou — pole jako `code` se schématem `^[A-Z]{2}\d{4}$` bude
  korektně odpovídat patternu)

**Konfigurace:**
- Refactor `core/config.py` na YAML-based `Config` třídu s
  singletonem (`init_config`, `get_config`, `_update_globals`)
- Hledání configu v `talosforge.yml` nebo `~/.talosforge/config.yml`,
  fallback na env vars a defaults
- Striktní AI provider mode (`provider: openai|zhipu|auto`)
- Nové konfigurovatelné: `gps_region` (CZ/EU/US/global), `cache.ttl`,
  `cache.enabled`
- `TalosForge.__init__()` přijímá volitelný `config_path`

**Další parametry v `Generate Data From Schema`:**
- `convert_decimals: bool = True` — automatický převod `Decimal` →
  `float` pro JSON kompatibilitu (Faker.latitude/longitude vrací
  `Decimal`)
- `exclude_dictionary: Optional[str]` — čárkou oddělený seznam JSON
  cest k vyloučení z výstupu, podporuje tečkovou notaci pro vnořená
  pole (např. `"id,created_at,user.id"`)

**Drobnosti v generátoru:**
- `_generate_bounded_coordinate()` — generování GPS souřadnic v rámci
  vybrané regionální obálky
- `_get_examples_value()` nyní vrací tuple `(has_value, value)` pro
  rozlišení "žádný example" vs. "example je `None`/`False`/`[]`"
- AI prompty obsahují locale instrukci (cs_CZ/en_US/jiné) podle
  configu — generovaná data odpovídají požadovanému jazyku

**Loader rozšíření:**
- `_is_flat_endpoint_format()` + `_extract_flat_endpoint_schemas()` —
  podpora vlastního flat formátu specifikace s klíči jako
  `"POST /api/v1/users"` přímo na root úrovni
- `_unwrap_json_schema_if_wrapped()` — automatické rozbalení JSON
  Schema z REST API responses typu `{"name": "...", "schema": {...}}`,
  `{"data": {...}}`, `{"result": {...}}`

**Logování:**
- Nový modul `TalosForge/utils/logger.py` s barevným výstupem
  (colorama) — `log_warning`, `log_error` a TTY detekce

### Závislosti

Přidáno do `dependencies`:
- `colorama>=0.4.6`

Nové optional extras groups:
- `db = ["psycopg2-binary>=2.9.0"]` — `pip install -e ".[db]"`
- `extras = ["rstr>=2.0.0", "prance>=0.24.0", "hypothesis-jsonschema",
  "openapi-spec-validator>=0.7.0"]` — `pip install -e ".[extras]"`

### Tests
- 217 unit testů pass (z toho 30 nových: db, logger, config,
  decimal_conversion, exclude_dictionary, flat_format, gps_region,
  postgres_schema_reader, atd.)
- 6 nových RF testů: `test_db_integration.robot`, `test_explore_mode.robot`,
  `test_external_refs.robot`, `test_rstr_integration.robot`,
  `test_url_schema.robot`, `test_config.robot`
- `tests/conftest.py` přidán s `reset_global_state` autouse fixture
  (resetuje config singleton + odstraňuje env vars před každým testem)

### Zachováno z 0.4.0 main
- `Validate Data Against Schema` keyword (Phase 1/2/3 dispatch)
- Response-code fallback (numeric → range → default), tj.
  `extract_response_schemas` vrací `Dict[str, Dict[int|str, schema]]`
  s range bucky `1XX`–`5XX` a `default`
- `SchemaLoader.resolve_response_schema()` a `build_registry()`
- `validation/` package (SchemaValidator, error formatter)
- UniversalFieldParser (token + RapidFuzz fuzzy matching) — Artima fork
  obsahoval shodnou verzi, žádný regression

## [0.4.0] - 2026-05-05

### Přidáno

**Nové keywords:**
- **`Validate Data Against Schema`** pro validaci dat proti JSON Schema a OpenAPI 3.0
  - Tři typy zdrojů: `schema_path` (lokální JSON Schema), `endpoint`+`method` (předem načtené OpenAPI), `openapi_url` (online OpenAPI specifikace)
  - Strict mode validace (vždy zapnutá, `additionalProperties: false` se aplikuje na všechny object schémata včetně vnořených objektů a `$ref`-resolvovaných komponent)
  - Parametr `return_errors=True` pro získání chyb jako seznam místo raise
  - Round-trip workflow: `Generate Data From Schema` + `Validate Data Against Schema` sdílí schémata pro contract testing

**Nové parametry v existujících keywords:**
- **`method` v `Generate Data From Schema`**: nový samostatný parametr pro HTTP metodu. Preferovaný způsob specifikace HTTP metody (vyhýbá se problémům s parsováním mezer v Robot Frameworku). Příklad: `method=POST endpoint=/users`. Stará syntaxe `endpoint=POST /users` stále funguje pro zpětnou kompatibilitu.

**Nové moduly a API:**
- **`TalosForge/validation/`** package: `SchemaValidator`, `DataValidationError`, error formatting helpers
  - `SchemaValidator` wrapper kolem `OAS30Validator` s hardcoded strict modem, format checker (`email`, `uuid`, `int32`, ...) a podporou registry pro $ref resolution
- **`SchemaLoader.extract_response_schemas()`**: extrakce response schémat z OpenAPI 3.0 specifikace (numerické status kódy)
- **`SchemaLoader.build_registry()`**: konstrukce `referencing.Registry` pro `$ref` resolution s automatickou strict-ifikací `components.schemas` přes deepcopy
- **`UniversalFieldParser`** v `TalosForge/core/generator.py`: inteligentní parser názvů polí
  - Token-based N-gram matching pro rychlou detekci typů polí
  - RapidFuzz fuzzy matching pro řešení překlepů a variant názvů
  - Podpora snake_case, camelCase, PascalCase, kebab-case
  - Rozpozná 50+ typů polí (email, phone, name, address, tags, atd.)
  - Automatická detekce kolekcí (tags, items, list, array)
  - Automatické odstraňování duplikátů v tag/categories polích

### Závislosti
- Přidáno `openapi-schema-validator>=0.7.0` (validation feature)
- Přidáno `responses>=0.23` jako dev dependency (HTTP mocking pro integration testy)
- Přidáno `rapidfuzz>=3.0.0` (UniversalFieldParser fuzzy matching)
- `referencing>=0.30` (transitivně přes `jsonschema>=4.18`, použito pro $ref registry)

### Mimo scope (sledováno jako issues)
- Public `Clear Schema Cache` keyword pro explicit URL cache invalidation: GitHub issue (URL TBD)
- Generator: `nullable: true` se ignoruje (`_is_nullable` helper existuje, ale není zapojený v dispatchi)
- Generator: `_handle_oneof_anyof_allof` se nikdy nevolá z `generate()` dispatcheru

### Změněno
- `_get_context_value()` nyní používá UniversalFieldParser místo hardcoded shod
- `_generate_array_with_context()` automaticky odstraňuje duplicity z tag/categories polí
- Počet řádků v `core/generator.py` se zvýšil z ~511 na ~1400

### Opraveno
- **Duplikáty v tags poli**: Pole `tags` nyní vždy obsahuje unikátní hodnoty
- **Garbage data pro prefixová pole**: Pole jako `customer_name`, `customer_phone`, `pickup_address` nyní generují správné typy dat
  - `customer_name` → české jméno (např. "Renáta Pešková")
  - `customer_phone` → telefonní číslo (např. "+420 774 442 642")
  - `pickup_address` → adresa (např. "Ke Břvům 829")
- **Složené názvy polí**: Pole s prefixy (customer_, user_, pickup_, atd.) jsou nyní správně rozpoznána

## [0.3.0] - 2025-02-01

### Změněno
- Pole `"example"` (jednotné číslo) v OpenAPI schématech je nyní **ignorováno**
- Generování dat nyní vrací různorodé hodnoty od Fakeru místo statických hodnot z `"example"`
- Aktualizována dokumentace priority systému v README.md

### Opraveno
- Opraveno deterministické chování při generování z OpenAPI schémat obsahujících `"example"` pole
- Testovací data jsou nyní skutečně náhodná, což zlepšuje pokrytí testovacích scénářů

### Přidáno
- Nová sekce "Priorita zpracování schématu" v README.md
- Test `test_example_singular_ignored` ověřující ignorování `"example"`
- Test `test_examples_plural_still_works` ověřující funkčnost `"examples"`
- Test `test_example_with_format` ověřující ignorování `"example"` s formátem
- Integrační test `test_openapi_example_ignored_integration`
- MIGRATION.md s migrační příručkou pro přechod z verze 0.2.x
- Dokumentace změn chování (docs/zmeny_chovani.rst)
- Dokumentace FAQ (docs/faq.rst)

### Breaking Changes
- **Důležité:** Pokud jste se spoléhali na statické hodnoty z pole `"example"`,
  nyní dostanete náhodné hodnoty generované Fakerem.
- Použijte `"examples"` (množné číslo) pro seznam hodnot s náhodným výběrem
- Použijte `"enum"` pro validační omezení
- Nebo přijměte náhodné hodnoty od Fakeru (doporučeno pro testovací data)

## [0.2.0] - 2025-01-31

### Přidáno
- Podpora pro `examples` a `example` pole v JSON Schema (JSON Schema draft 2019-09+ a OpenAPI 3.x)
- Kontextové generování pro 50+ field variants (name, phone, email, address, company, atd.)
- Nullable podpora pro OpenAPI specification
- Speciální logika pro generování krátkých tagů
- Nové metody v DataGenerator:
  - `_get_examples_value()` - získá náhodnou hodnotu z examples/example pole
  - `_get_context_value()` - generuje hodnotu podle kontextu názvu pole
  - `_generate_with_context()` - interní dispatcher s field_name parametrem
  - `_generate_array_with_context()` - generování polí s kontextem
  - `_is_nullable()` - kontrola nullable atributu

### Změněno
- `_generate_string()` nyní přijímá volitelný `field_name` parametr
- Priority generování: enum > examples > ai > faker
- `_generate_object()` nyní používá `_generate_with_context()` pro kontextové generování vlastností

### Opraveno
- Pole `name`, `phone`, `email` a další nyní generují realistická data místo obecného textu
- Pole `tags` generuje krátké hodnoty místo dlouhých vět
- Offline mód nyní funguje bez AI pro běžná API pole

### Testování
- 14 nových testů pro examples a kontextové generování
- Celkem 44 testů, 100% pokrytí

## [0.1.0] - 2025-01-31

### Přidáno
- Projekt vytvořen v6 fázích
- Podpora JSON Schema a OpenAPI specifikací
- Hybridní generování (Faker + AI)
- URL podpora s cachováním
- Kompletní testovací sada (43 testů)
- **SchemaLoader**: Načítání JSON a OpenAPI schémat (JSON/YAML)
- **DataGenerator**: Generování dat pomocí Fakeru
  - Podpora všech JSON Schema typů
  - Podpora omezení (minLength, minimum, enum, atd.)
  - Rekurzivní generování objektů a polí
- **AIGenerator**: Integrace AI modelů
  - OpenAI API podpora
  - Zhipu AI API podpora
  - Inteligentní výběr AI vs Faker
- **SimpleCache**: Mezipaměť pro URL specifikace
- **URL podpora**: Stažení OpenAPI specifikací z URL
- **target="ui"**: Speciální formát pro UI testování
- **Dva keywords**: `Load Schema` a `Generate Data From Schema`

### Typy podporované v JSON Schema
- `string` - s format (email, date, uri, uuid, password, atd.)
- `integer` - s minimum/maximum
- `number` - s minimum/maximum
- `boolean`
- `array` - s items, minItems, maxItems
- `object` - s properties, required, default
- `enum` - výčet hodnot
- `oneOf`, `anyOf`, `allOf` - základní podpora

### Testování
- 30 jednotkových testů (pytest)
- 8 integračních testů
- 5 Robot Framework testů
- Celkem 43 testů, 100% pokrytí

### Dokumentace
- README.md s kompletní dokumentací
- CHANGELOG.md
- Docstrings pro všechny veřejné metody

### Závislosti
- robotframework>=7.0
- faker
- PyYAML
- requests
- openai>=1.0 (volitelné)
- pytest, pytest-mock, flake8, black (dev)

## [0.2.0] - Plánováno

### Plánované funkce
- Flattening vnořených objektů pro target="ui"
- Více AI providerů
- Generování relací mezi daty
- Podpora pro XML Schema
- Rozšířené validace generovaných dat

## Roadmap

### Krátkodobé (Fáze 7-8)
- [ ] Flattening pro UI target
- [ ] Podpora pro více AI providerů
- [ ] Generování souvisejících dat
- [ ] Rozšířené testy s reálnými API

### Střednědobé (Fáze 9-12)
- [ ] XML Schema podpora
- [ ] GraphQL Schema podpora
- [ ] Validace generovaných dat
- [ ] Export generovaných dat do souborů

### Dlouhodobé
- [ ] GUI pro návrh schémat
- [ ] Sdílení schémat mezi týmem
- [ ] Plugin systém
- [ ] Cloud verze

[Unreleased]: https://github.com/yourusername/TalosForge/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/yourusername/TalosForge/releases/tag/v0.3.0
[0.2.0]: https://github.com/yourusername/TalosForge/releases/tag/v0.2.0
[0.1.0]: https://github.com/yourusername/TalosForge/releases/tag/v0.1.0
