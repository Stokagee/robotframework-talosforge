# TalosForge

**Schema-driven test data generator for Robot Framework**

TalosForge je Python knihovna pro Robot Framework, která generuje testovací data na míru pomocí JSON Schema a OpenAPI specifikací. Kombinuje rychlost knihovny Faker s inteligencí AI modelů (OpenAI, Zhipu) pro komplexní případy.

## Funkce

- **Generování na míru**: Definujte strukturu dat pomocí JSON Schema nebo OpenAPI
- **Hybridní přístup**: Faker pro rychlost + AI pro složité případy
- **Univerzální výstup**: Python slovníky kompatibilní s RequestsLibrary, Browser, DatabaseLibrary
- **Jednoduché API**: Pouze dva hlavní keywords
- **Mezipaměť**: Automatické cachování URL specifikací
- **Více jazyků**: Výchozí česká lokalizace, snadná změna

## Požadavky

- Python 3.11+
- Robot Framework 7.0+

## Instalace

### Základní instalace

```bash
pip install TalosForge
```

### S podporou AI (volitelné)

```bash
# Pro OpenAI
pip install openai>=1.0
export OPENAI_API_KEY=your_key_here

# Pro Zhipu AI
pip install zhipuai
export ZHIPU_API_KEY=your_key_here
```

## Rychlý start

### 1. Vytvořte JSON schéma

**user_schema.json:**
```json
{
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 5
    },
    "email": {
      "type": "string",
      "format": "email"
    },
    "age": {
      "type": "integer",
      "minimum": 18,
      "maximum": 99
    }
  },
  "required": ["username", "email"]
}
```

### 2. Použití v Robot Framework

```robotframework
*** Settings ***
Library     talosforge.TalosForge

*** Test Cases ***
Generate User Data
    ${user}=    Generate Data From Schema    schema_path=./user_schema.json
    Log    ${user}
    # Výstup: {'username': 'Jan Novák', 'email': 'jan.novak@example.cz', 'age': 25}
```

## Keywords

### Load Schema

Načte OpenAPI soubor do paměti pro rychlejší přístup při opakovaném generování.

**Syntaxe:**
```robotframework
Load Schema    swagger_path=<path>    [force_reload=False]
```

**Parametry:**
- `swagger_path` (povinný): Cesta k lokálnímu OpenAPI (Swagger) souboru (JSON nebo YAML)
- `force_reload` (volitelný): Vynutí znovunačtení, i když je již v paměti. Default: False

**Příklad:**
```robotframework
*** Test Cases ***
Load Large API
    Load Schema    swagger_path=./petstore.yaml
    ${pet}=    Generate Data From Schema    endpoint=POST /pet
    ${order}=    Generate Data From Schema    endpoint=POST /store/order
```

### Generate Data From Schema

Generuje testovací data na základě poskytnutého schématu.

**Syntaxe:**
```robotframework
${data}=    Generate Data From Schema    [source]    [target=api|ui]    [amount=1]    [use_ai=False]
```

**Zdroje dat (musí být specifikován právě jeden):**
- `schema_path`: Cesta k lokálnímu JSON schématu
- `endpoint`: Endpoint ve formátu `METODA /cesta` (např. `POST /users`). Vyžaduje předchozí `Load Schema`
- `openapi_url`: URL k online OpenAPI specifikaci. Vyžaduje `endpoint`

**Parametry:**
- `method` (volitelný): HTTP metoda (např. `POST`, `GET`). Vyžaduje také `endpoint`. Toto je preferovaný způsob specifikace HTTP metody, protože vyhýbá problémům s parsováním mezer v Robot Frameworku.
- `target` (volitelný): Formát výstupu. Možnosti: `"api"` (default) nebo `"ui"`
- `amount` (volitelný): Počet generovaných záznamů. Default: 1
- `use_ai` (volitelný): Povolí AI generování pro složité případy. Default: False

**Návratová hodnota:**
- Pokud `amount=1`: Vrací jeden slovník (dict)
- Pokud `amount>1`: Vrací seznam slovníků (list)

**Příklady:**

```robotframework
# Z lokálního JSON schématu
${user}=    Generate Data From Schema    schema_path=./user.json

# Z načteného OpenAPI souboru - NOVÁ SYNTAXE (doporučeno)
Load Schema    swagger_path=./api.yaml
${data}=    Generate Data From Schema    method=POST    endpoint=/users    amount=5

# Z načteného OpenAPI souboru - STARÁ SYNTAXE (stále funguje)
Load Schema    swagger_path=./api.yaml
${data}=    Generate Data From Schema    endpoint=POST /users    amount=5

# Z online OpenAPI specifikace
${item}=    Generate Data From Schema    openapi_url=https://api.example.com/swagger.json    method=GET    endpoint=/items

# Pro UI testování
${form}=    Generate Data From Schema    schema_path=./login.json    target=ui

# S AI generováním
${content}=    Generate Data From Schema    schema_path=./article.json    use_ai=True
```

**HTTP Metody**

Pro specifikaci HTTP metody existují dva způsoby:

1. **Samostatný parametr `method=` (doporučeno)** - vyhýbá se problémům s parsováním mezer v Robot Frameworku:
   ```robotframework
   ${data}=    Generate Data From Schema    method=POST    endpoint=/api/v1/couriers/
   ```

2. **Zapsané přímo v endpointu (zpětná kompatibilita)** - funguje, ale Robot Framework může parsovat mezeru jako oddělovač:
   ```robotframework
   ${data}=    Generate Data From Schema    endpoint=POST /api/v1/couriers/
   ```

## Podporované JSON Schema typy

| Typ | Podporované vlastnosti |
|-----|----------------------|
| `string` | format, minLength, maxLength, pattern, description, examples |
| `integer` | minimum, maximum, exclusiveMinimum, exclusiveMaximum, examples |
| `number` | minimum, maximum, exclusiveMinimum, exclusiveMaximum, examples |
| `boolean` | examples |
| `array` | items, minItems, maxItems |
| `object` | properties, required, default |
| `enum` | Výčet hodnot |
| `oneOf`, `anyOf`, `allOf` | Základní podpora (s AI) |

## Podpora příkladů (examples)

TalosForge podporuje `examples` pole v JSON Schema:

```json
{
  "name": {"type": "string", "examples": ["Jan Novák", "Petr Svoboda"]},
  "age": {"type": "integer", "examples": [25, 30, 42]},
  "tags": {
    "type": "array",
    "items": {"type": "string", "examples": ["vip", "urgent"]}
  }
}
```

## Priorita zpracování schématu

TalosForge zpracovává JSON Schema v tomto pořadí:

1. **enum** - Výběr náhodné hodnoty z enum seznamu (validační constraint)
2. **examples** - Výběr náhodné hodnoty z examples seznamu
3. **example** - *Ignorováno* (pouze jedna hodnota by blokovala Faker)
4. **AI** - AI generování (pokud `use_ai=True`)
5. **Faker** - Generování podle typu/formátu

**Důležité:** Pole `example` (jednotné číslo) v OpenAPI specifikacích je ignorováno,
protože obsahuje jen jednu hodnotu. Pro testovací data různorodější použijte Faker
nebo zadejte `examples` (množné číslo) s více hodnotami.

## Kontextové generování (50+ field variants)

Pro běžná pole TalosForge automaticky používá správné Faker metody. Offline mód funguje bez AI pro:

**Osobní údaje:** name, first_name, last_name, username, email, phone
**Adresa:** address, street, city, zip, state, country, lat, lng
**Organizace:** company, department, position
**Čas:** date, time, datetime, created_at, updated_at
**Obsah:** title, description, content, message, subject
**Identifikátory:** id, uuid, code, sku
**WWW:** url, domain, hostname
**Finance:** price, cost, currency, account, iban
**Technické:** ip, port, user_agent, mac, token
**Stav:** status, priority, level
**Speciální:** tags, categories, type

**Příklad:**
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "email": {"type": "string"},
    "phone": {"type": "string"},
    "address": {"type": "string"},
    "company": {"type": "string"},
    "created_at": {"type": "string"}
  }
}
```

Vygeneruje realistická data jako:
```json
{
  "name": "Jan Novák",
  "email": "jan.novak@example.cz",
  "phone": "+420 123 456 789",
  "address": "Nová 123, Praha",
  "company": "Firma s.r.o.",
  "created_at": "2025-01-31T12:34:56"
}
```

## Nullable podpora (OpenAPI)

Pro pole s `nullable: true` existuje 20% šance na vrácení `None`:

```json
{
  "lat": {"type": "number", "nullable": true}
}
```

### Podporované formáty (string)

- `email` - Emailová adresa
- `date` - Datum (YYYY-MM-DD)
- `date-time` - Datum a čas (ISO 8601)
- `time` - Čas (HH:MM:SS)
- `uri` - URL adresa
- `uuid` - UUID verze 4
- `hostname` - Hostname
- `ipv4`, `ipv6` - IP adresy
- `password` - Heslo
- `phone` - Telefonní číslo

## AI Generování

AI se používá pro složité případy jako:
- Přítomnost `description` ve schématu
- Složité regulární výrazy (`pattern`)
- `oneOf`/`anyOf`/`allOf` konstrukce
- Specifické formáty (např. `czech-id`, `ssn`)

**Příklad s description:**
```json
{
  "type": "string",
  "description": "Generate a realistic Czech full name"
}
```

S `use_ai=True` TalosForge použije AI model k vygenerování českého jména.

## Konfigurace

### Lokalizace

```python
import os
os.environ["TAOSFORGE_LOCALE"] = "en_US"  # Anglická lokalizace
```

### AI Provider

```python
import os

# Výběr providera
os.environ["TAOSFORGE_AI_PROVIDER"] = "openai"  # nebo "zhipu"

# Specifické modely
os.environ["TAOSFORGE_OPENAI_MODEL"] = "gpt-4"
os.environ["TAOSFORGE_ZHIPU_MODEL"] = "glm-4"
```

## Vývoj

### Instalace pro vývoj

```bash
git clone https://github.com/yourusername/TalosForge.git
cd TalosForge
pip install -e ".[dev]"
```

### Spuštění testů

```bash
# Všechny pytest testy
pytest

# Jen jednotkové testy
pytest tests/unit

# Integrační testy
pytest tests/integration

# Robot Framework testy
robot --outputdir results/robot tests/robot
```

### Formátování kódu

```bash
# Flake8 linting
flake8 talosforge/ --max-line-length=100

# Black formátování
black talosforge/
```

## Projektová struktura

```
talosforge/
├── __init__.py         # Hlavní TalosForge třída
├── core/
│   ├── config.py       # Konfigurace
│   ├── generator.py    # DataGenerator (Faker + AI)
│   ├── ai_generator.py # AIGenerator
│   └── exceptions.py   # Výjimky
├── schema/
│   └── loader.py       # SchemaLoader
└── utils/
    └── cache.py        # SimpleCache
```

## Licence

Apache License 2.0

## Status

**Verze 0.2.0** - Produkčně připravená

- ✅ Schema-driven generování (JSON Schema, OpenAPI)
- ✅ Hybridní generování (Faker + AI)
- ✅ URL podpora s cachováním
- ✅ 44 testů (100% pokrytí)
- ✅ Kompletní dokumentace
- ✅ Podpora pro `examples` a `example` pole v JSON Schema
- ✅ Kontextové generování pro 50+ field variants
- ✅ Nullable podpora (OpenAPI specification)
