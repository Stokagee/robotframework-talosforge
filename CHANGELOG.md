# Changelog

Všechny významné změny projektu TalosForge budou dokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Přidáno
- **UniversalFieldParser**: Nový inteligentní parser názvů polí
  - Token-based N-gram matching pro rychlou detekci typů polí
  - RapidFuzz fuzzy matching pro řešení překlepů a variant názvů
  - Podpora snake_case, camelCase, PascalCase, kebab-case
  - Rozpozná 50+ typů polí (email, phone, name, address, tags, atd.)
  - Automatická detekce kolekcí (tags, items, list, array)
  - Automatické odstraňování duplikátů v tag/categories polích
- **Nová dependency**: `rapidfuzz>=3.0.0` pro fuzzy matching

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

### Přidáno (dříve)
- **Parametr `method`**: Nový samostatný parametr pro HTTP metodu v `Generate Data From Schema`. Toto je preferovaný způsob specifikace HTTP metody, protože vyhýbá problémům s parsováním mezer v Robot Frameworku. Příklad: `method=POST endpoint=/users`. Stará syntaxe `endpoint=POST /users` stále funguje pro zpětnou kompatibilitu.

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
