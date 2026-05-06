"""
Testy pro DataGenerator.
"""

from unittest.mock import MagicMock, patch

from TalosForge.core.generator import DataGenerator


def test_generator_initialization():
    """Test inicializace DataGenerator."""
    generator = DataGenerator()
    assert generator.fake is not None
    assert generator.ai_generator is not None


def test_generate_string():
    """Test generování string."""
    generator = DataGenerator()
    schema = {"type": "string"}
    result = generator._generate_string(schema)
    assert isinstance(result, str)


def test_generate_string_with_format():
    """Test generování string s formátem."""
    generator = DataGenerator()

    # Email
    schema = {"type": "string", "format": "email"}
    result = generator._generate_string(schema)
    assert "@" in result

    # UUID
    schema = {"type": "string", "format": "uuid"}
    result = generator._generate_string(schema)
    assert len(result) == 36  # UUID format: 8-4-4-4-12


def test_generate_string_with_length():
    """Test generování string s délkou."""
    generator = DataGenerator()
    schema = {"type": "string", "minLength": 10, "maxLength": 20}
    result = generator._generate_string(schema)
    assert 10 <= len(result) <= 20


def test_generate_integer():
    """Test generování integer."""
    generator = DataGenerator()
    schema = {"type": "integer"}
    result = generator._generate_integer(schema)
    assert isinstance(result, int)


def test_generate_integer_with_bounds():
    """Test generování integer s mezemi."""
    generator = DataGenerator()
    schema = {"type": "integer", "minimum": 10, "maximum": 20}
    result = generator._generate_integer(schema)
    assert 10 <= result <= 20


def test_generate_number():
    """Test generování number."""
    generator = DataGenerator()
    schema = {"type": "number"}
    result = generator._generate_number(schema)
    assert isinstance(result, float)


def test_generate_number_with_bounds():
    """Test generování number s mezemi."""
    generator = DataGenerator()
    schema = {"type": "number", "minimum": 0.0, "maximum": 1.0}
    result = generator._generate_number(schema)
    assert 0.0 <= result <= 1.0


def test_generate_boolean():
    """Test generování boolean."""
    generator = DataGenerator()
    schema = {"type": "boolean"}
    result = generator._generate_boolean(schema)
    assert isinstance(result, bool)


def test_generate_array():
    """Test generování array."""
    generator = DataGenerator()
    schema = {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 2,
        "maxItems": 5,
    }
    result = generator._generate_array(schema)
    assert isinstance(result, list)
    assert 2 <= len(result) <= 5


def test_generate_object():
    """Test generování object."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }
    result = generator._generate_object(schema)
    assert isinstance(result, dict)
    assert "name" in result
    # age je volitelné
    assert isinstance(result.get("age"), (int, type(None)))


def test_generate_enum():
    """Test generování enum."""
    generator = DataGenerator()
    schema = {"type": "string", "enum": ["red", "green", "blue"]}
    result = generator._handle_enum(schema)
    assert result in ["red", "green", "blue"]


def test_generate_full_schema():
    """Test generování kompletního schématu."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 3},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 18, "maximum": 99},
            "active": {"type": "boolean"},
        },
        "required": ["name", "email"],
    }
    result = generator.generate(schema)

    assert isinstance(result, dict)
    assert "name" in result
    assert "email" in result
    assert isinstance(result["name"], str)
    assert len(result["name"]) >= 3
    assert "@" in result["email"]
    # age a active jsou volitelné


def test_generate_nested_object():
    """Test generování vnořeného objektu."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name"],
            },
        },
        "required": ["user"],
    }
    result = generator.generate(schema)

    assert isinstance(result, dict)
    assert "user" in result
    assert isinstance(result["user"], dict)
    assert "name" in result["user"]


def test_generate_array_of_objects():
    """Test generování pole objektů."""
    generator = DataGenerator()
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["id"],
        },
        "minItems": 1,
        "maxItems": 3,
    }
    result = generator.generate(schema)

    assert isinstance(result, list)
    assert 1 <= len(result) <= 3
    for item in result:
        assert isinstance(item, dict)
        assert "id" in item


def test_generate_with_use_ai_false():
    """Test generování s use_ai=False."""
    generator = DataGenerator()
    schema = {"type": "string"}
    result = generator.generate(schema, use_ai=False)
    assert isinstance(result, str)


def test_should_use_ai():
    """Test metody _should_use_ai."""
    generator = DataGenerator()

    # S description - mělo by použít AI
    schema_with_desc = {"type": "string", "description": "A realistic name"}
    assert generator._should_use_ai(schema_with_desc) is True

    # Bez description - nemělo by použít AI
    schema_simple = {"type": "string"}
    assert generator._should_use_ai(schema_simple) is False

    # S oneOf - mělo by použít AI
    schema_oneof = {"type": "string", "oneOf": [{"type": "string"}, {"type": "number"}]}
    assert generator._should_use_ai(schema_oneof) is True


def test_ai_triggered_with_db_description():
    """Test že AI se použije když schema má description z DB komentáře."""
    generator = DataGenerator()

    # Schema jako by přišlo z DB s COMMENT ON COLUMN
    db_schema = {
        "type": "string",
        "description": "User email address with Czech domain"
    }
    assert generator._should_use_ai(db_schema) is True

    # Schema s description a maxLength (společné z DB)
    db_schema_with_length = {
        "type": "string",
        "description": "Czech full name with diacritics",
        "maxLength": 100
    }
    assert generator._should_use_ai(db_schema_with_length) is True

    # Schema bez description (např. sloupec bez COMMENT)
    plain_schema = {"type": "string", "maxLength": 100}
    assert generator._should_use_ai(plain_schema) is False


# Tests pro examples podporu


def test_examples_string():
    """Test examples pro string."""
    generator = DataGenerator()
    schema = {"type": "string", "examples": ["hodnota1", "hodnota2"]}
    result = generator.generate(schema)
    assert result in ["hodnota1", "hodnota2"]


def test_examples_integer():
    """Test examples pro integer."""
    generator = DataGenerator()
    schema = {"type": "integer", "examples": [1, 2, 3]}
    result = generator.generate(schema)
    assert result in [1, 2, 3]


def test_example_singular_string_ignored_for_variety():
    """Singular 'example' pro string by měl být ignorován pro variabilitu."""
    generator = DataGenerator()
    schema = {"type": "string", "example": "static_value"}

    results = [generator.generate(schema) for _ in range(10)]

    # Měli bychom dostat různé hodnoty od Fakeru
    unique = set(results)
    assert len(unique) > 1, f"Očekáváno více hodnot pro variabilitu, dostáno: {unique}"
    # static_value by se nemělo opakovat
    assert results.count("static_value") <= 1, "Example by neměl být použit pro string"


def test_example_singular_boolean():
    """Singular 'example' by měl fungovat pro boolean typ."""
    generator = DataGenerator()
    schema = {"type": "boolean", "example": False}

    result = generator.generate(schema)

    # Hodnota by měla být přesně False
    assert result is False, f"Očekáváno False, dostáno: {result}"


def test_example_singular_integer():
    """Singular 'example' by měl fungovat pro integer typ."""
    generator = DataGenerator()
    schema = {"type": "integer", "example": 42}

    result = generator.generate(schema)

    # Hodnota by měla být přesně 42
    assert result == 42, f"Očekáváno 42, dostáno: {result}"


def test_example_over_description():
    """Example by měl mít přednost před description pro boolean."""
    generator = DataGenerator()
    schema = {
        "type": "boolean",
        "example": True,
        "description": "nějaký text pro dokumentaci"
    }

    result = generator.generate(schema)

    # Example by měl mít přednost
    assert result is True, f"Očekáváno True, dostáno: {result}"


def test_examples_plural_still_works():
    """Plural 'examples' by měl stále fungovat s random výběrem."""
    generator = DataGenerator()
    schema = {"type": "string", "examples": ["A", "B", "C"]}

    results = [generator.generate(schema) for _ in range(20)]

    # Všechny hodnoty by měly být z examples
    assert all(r in ["A", "B", "C"] for r in results)
    # Alespoň 2 různé hodnoty
    assert len(set(results)) >= 2


def test_example_with_format_ignored_for_string():
    """Example pro string s format by měl být ignorován - Faker generuje validní hodnoty."""
    generator = DataGenerator()
    schema = {
        "type": "string",
        "format": "email",
        "example": "test@example.com"
    }

    results = [generator.generate(schema) for _ in range(10)]

    # Měli bychom dostat různé validní emaily od Fakeru
    assert all("@" in r for r in results), "Všechny by měly být validní emaily"
    # Pro variabilitu by nemělo být pořád stejné
    unique = set(results)
    assert len(unique) >= 2, f"Očekávána variabilita emailů, dostáno: {unique}"


def test_example_with_description_no_enum_extraction():
    """Description by neměl být parsován jako enum - Faker generuje data."""
    generator = DataGenerator()
    schema = {
        "type": "string",
        "description": "Status: active, inactive, pending"
    }

    results = [generator.generate(schema) for _ in range(10)]

    # Description by neměl být parsován jako enum
    # Faker by měl generovat různé stringy
    assert all(isinstance(r, str) for r in results), "Všechny by měly být stringy"


def test_examples_in_nested_object():
    """Test examples ve vnořeném objektu."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "examples": ["active", "inactive"]},
            "priority": {"type": "string", "examples": ["low", "high"]}
        },
        "required": ["status", "priority"]
    }
    result = generator.generate(schema)
    assert result["status"] in ["active", "inactive"]
    assert result["priority"] in ["low", "high"]


# Tests pro kontextové generování


def test_context_name_field():
    """Test kontextového generování pro name."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
    result = generator.generate(schema)
    # celé jméno by mělo obsahovat mezeru (jméno + příjmení)
    assert " " in result["name"]


def test_context_first_name_field():
    """Test kontextového generování pro first_name."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"first_name": {"type": "string"}}, "required": ["first_name"]}
    result = generator.generate(schema)
    assert isinstance(result["first_name"], str)
    # first_name by nemělo obsahovat mezeru
    assert " " not in result["first_name"]


def test_context_phone_field():
    """Test kontextového generování pro phone."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"phone": {"type": "string"}}, "required": ["phone"]}
    result = generator.generate(schema)
    # telefon by měl obsahovat číslice
    assert any(c.isdigit() for c in result["phone"])


def test_context_email_field():
    """Test kontextového generování pro email."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]}
    result = generator.generate(schema)
    # email by měl obsahovat @
    assert "@" in result["email"]


def test_context_address_field():
    """Test kontextového generování pro address."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]}
    result = generator.generate(schema)
    assert isinstance(result["address"], str)
    assert len(result["address"]) > 0


def test_context_company_field():
    """Test kontextového generování pro company."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"company": {"type": "string"}}, "required": ["company"]}
    result = generator.generate(schema)
    assert isinstance(result["company"], str)
    assert len(result["company"]) > 0


def test_context_date_field():
    """Test kontextového generování pro date."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"date": {"type": "string"}}, "required": ["date"]}
    result = generator.generate(schema)
    assert isinstance(result["date"], str)


def test_context_datetime_field():
    """Test kontextového generování pro created_at."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"created_at": {"type": "string"}}, "required": ["created_at"]}
    result = generator.generate(schema)
    assert isinstance(result["created_at"], str)
    # ISO formát datetime obsahuje "T"
    assert "T" in result["created_at"]


def test_context_id_field():
    """Test kontextového generování pro id."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}
    result = generator.generate(schema)
    assert isinstance(result["id"], int)
    assert 1 <= result["id"] <= 999999


def test_context_uuid_field():
    """Test kontextového generování pro uuid."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"uuid": {"type": "string"}}, "required": ["uuid"]}
    result = generator.generate(schema)
    assert isinstance(result["uuid"], str)
    # UUID formát: 8-4-4-4-12 = 36 znaků
    assert len(result["uuid"]) == 36


def test_context_url_field():
    """Test kontextového generování pro url."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
    result = generator.generate(schema)
    assert isinstance(result["url"], str)
    # URL by měla obsahovat http
    assert "http" in result["url"]


def test_context_price_field():
    """Test kontextového generování pro price."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"price": {"type": "number"}}, "required": ["price"]}
    result = generator.generate(schema)
    assert isinstance(result["price"], (int, float))
    assert 0 <= result["price"] <= 10000


def test_context_ip_field():
    """Test kontextového generování pro ip."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
    result = generator.generate(schema)
    assert isinstance(result["ip"], str)
    # IPv4 adresa obsahuje tečky
    assert "." in result["ip"]


def test_context_status_field():
    """Test kontextového generování pro status."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}
    result = generator.generate(schema)
    assert result["status"] in ["active", "inactive", "pending", "blocked", "online", "offline"]


def test_context_priority_field():
    """Test kontextového generování pro priority."""
    generator = DataGenerator()
    schema = {"type": "object", "properties": {"priority": {"type": "string"}}, "required": ["priority"]}
    result = generator.generate(schema)
    assert result["priority"] in ["low", "medium", "high", "urgent", "critical"]


def test_tags_with_examples():
    """Test tags s examples."""
    generator = DataGenerator()
    schema = {
        "type": "array",
        "items": {"type": "string", "examples": ["vip", "urgent"]},
        "minItems": 1
    }
    result = generator.generate(schema)
    assert isinstance(result, list)
    assert all(tag in ["vip", "urgent"] for tag in result)


def test_tags_default_examples():
    """Test tags s default examples když nejsou definovány."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1}
        },
        "required": ["tags"]
    }
    result = generator.generate(schema)
    assert isinstance(result["tags"], list)
    # Všechny tagy by měly být z default setu
    default_tags = ["vip", "urgent", "normal", "low", "bike", "car", "fragile_ok", "fast", "priority", "standard"]
    assert all(tag in default_tags for tag in result["tags"])


def test_tags_with_items_enum():
    """Test že items.enum má přednost před default tags."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string", "enum": ["custom_vip", "custom_urgent"]},
                "minItems": 1
            }
        },
        "required": ["tags"]
    }
    result = generator.generate(schema)
    assert isinstance(result["tags"], list)
    # Všechny tagy by měly být z enum, ne z default
    assert all(tag in ["custom_vip", "custom_urgent"] for tag in result["tags"])


def test_tags_with_empty_example():
    """Test že prázdné example pole vygeneruje prázdné pole."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "required_tags": {
                "type": "array",
                "items": {"type": "string"},
                "example": [],
                "minItems": 0
            }
        },
        "required": ["required_tags"]
    }
    result = generator.generate(schema)
    assert result["required_tags"] == [], f"Očekáváno [], dostáno: {result['required_tags']}"


def test_array_with_empty_example_at_array_level():
    """Test že prázdné example na úrovni array vygeneruje prázdné pole."""
    generator = DataGenerator()
    schema = {
        "type": "array",
        "items": {"type": "string"},
        "example": [],
        "minItems": 0
    }
    result = generator.generate(schema)
    assert result == [], f"Očekáváno [], dostáno: {result}"


def test_tags_example_string_ignored_for_variety():
    """Test že items.example pro string je ignorován pro variabilitu."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string", "example": "custom_tag"},
                "minItems": 1
            }
        },
        "required": ["tags"]
    }
    result = generator.generate(schema)
    assert isinstance(result["tags"], list)
    # String example by měl být ignorován, použijí se default tags
    default_tags = ["vip", "urgent", "normal", "low", "bike", "car", "fragile_ok", "fast", "priority", "standard"]
    assert all(tag in default_tags for tag in result["tags"])


# Tests pro priority - enum má přednost před examples


def test_priority_enum_over_examples():
    """Test že enum má přednost před examples."""
    generator = DataGenerator()
    schema = {"type": "string", "enum": ["a", "b"], "examples": ["x", "y"]}
    result = generator.generate(schema)
    # enum vyhrál - musí být a nebo b
    assert result in ["a", "b"]


def test_get_examples_value_empty():
    """Test _get_examples_value s prázdným listem."""
    generator = DataGenerator()
    schema = {"type": "string", "examples": []}
    has_value, value = generator._get_examples_value(schema)
    assert has_value is False
    assert value is None


def test_get_examples_value_none():
    """Test _get_examples_value bez examples."""
    generator = DataGenerator()
    schema = {"type": "string"}
    has_value, value = generator._get_examples_value(schema)
    assert has_value is False
    assert value is None


def test_is_nullable_true():
    """Test _is_nullable s nullable=True."""
    generator = DataGenerator()
    schema = {"type": "string", "nullable": True}
    assert generator._is_nullable(schema) is True


def test_is_nullable_false():
    """Test _is_nullable bez nullable."""
    generator = DataGenerator()
    schema = {"type": "string"}
    assert generator._is_nullable(schema) is False


def test_context_multiple_fields():
    """Test kontextového generování pro více polí najednou."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "address": {"type": "string"},
            "company": {"type": "string"},
            "created_at": {"type": "string"}
        },
        "required": ["name", "email", "phone", "address", "company", "created_at"]
    }
    result = generator.generate(schema)
    assert " " in result["name"]  # celé jméno
    assert "@" in result["email"]  # email
    assert any(c.isdigit() for c in result["phone"])  # telefon má číslice
    assert isinstance(result["address"], str)
    assert isinstance(result["company"], str)
    assert isinstance(result["created_at"], str)


# Tests pro array field generation fix


def test_all_fields_always_generated():
    """Test že všechna pole jsou vždy generována, i když nejsou v required."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["name"]  # Jen name je required
    }

    # Otestovat více běhů pro konzistenci
    for _ in range(10):
        result = generator.generate(schema)
        # Všechna pole by měla být přítomna
        assert "name" in result
        assert "phone" in result
        assert "tags" in result


def test_default_empty_ignored():
    """Test že prázdné defaulty jsou ignorovány."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}, "default": []},
            "description": {"type": "string", "default": ""}
        }
    }

    # Prázdné defaulty by měly být ignorovány (generována smysluplná data)
    # Většina běhů by neměla mít prázdné defaulty
    results = [generator.generate(schema) for _ in range(20)]

    # Alespoň v některých případech by tags nemělo být prázdné
    non_empty_tags = [r for r in results if r.get("tags") not in [None, [], "null"]]
    assert len(non_empty_tags) > 0, "Empty defaults should be ignored"

    # Alespoň v některých případech by description nemělo být prázdné
    non_empty_desc = [r for r in results if r.get("description") not in [None, "", "null"]]
    assert len(non_empty_desc) > 0, "Empty defaults should be ignored"


def test_default_meaningful_used():
    """Test že smysluplné defaulty mohou být použity."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "default": "active"},
            "count": {"type": "integer", "default": 0}
        }
    }

    results = [generator.generate(schema) for _ in range(50)]

    # Některé výsledky by měly mít default hodnoty
    has_status_default = any(r.get("status") == "active" for r in results)
    has_count_default = any(r.get("count") == 0 for r in results)

    # Alespoň jeden by měl mít default (50% šance)
    assert has_status_default or has_count_default, "Meaningful defaults may be used"


def test_minitems_zero_becomes_one():
    """Test že minItems: 0 zajišťuje alespoň 1 položku."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}, "minItems": 0}
        }
    }

    # Všechny generované pole by měly mít alespoň 1 položku
    for _ in range(20):
        result = generator.generate(schema)
        tags = result.get("tags", [])
        assert len(tags) >= 1, f"minItems=0 should result in at least 1 item, got {len(tags)}"


def test_uniqueitems_true_no_duplicates():
    """Test že uniqueItems: true zabraňuje duplikátům."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 10,
                "uniqueItems": True
            }
        }
    }

    # Všechny běhy by neměly mít duplicity
    for _ in range(10):
        result = generator.generate(schema)
        tags = result.get("tags", [])

        # Ověřit že nejsou duplicity
        assert len(tags) == len(set(tags)), f"uniqueItems=true should not have duplicates, got {tags}"


def test_uniqueitems_false_allows_duplicates():
    """Test že bez uniqueItems (nebo false) jsou duplicity povoleny."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {"type": "string", "enum": ["click", "view", "purchase"]},
                "minItems": 5,
                "maxItems": 10
            }
        }
    }

    # S enum omezeným na 3 hodnoty a minItems=5 musí vzniknout duplicity
    results = [generator.generate(schema) for _ in range(10)]

    # Alespoň některé výsledky by měly mít duplicity
    has_duplicates = any(
        len(r.get("events", [])) != len(set(r.get("events", [])))
        for r in results
    )
    assert has_duplicates, "Without uniqueItems, duplicates should be possible"


def test_uniqueitems_with_objects():
    """Test že uniqueItems: true funguje i pro objekty."""
    import json

    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                },
                "minItems": 3,
                "uniqueItems": True
            }
        }
    }

    # Všechny běhy by neměly mít duplictní objekty
    for _ in range(5):
        result = generator.generate(schema)
        items = result.get("items", [])

        # Převést objekty na JSON pro porovnání
        item_jsons = [json.dumps(item, sort_keys=True) for item in items]

        # Ověřit že nejsou duplicity
        assert len(item_jsons) == len(set(item_jsons)), f"uniqueItems=true should not have duplicate objects"


def test_array_with_fewer_examples_than_minitems():
    """Test že když je examples méně než minItems, použije se minItems jako limit."""
    generator = DataGenerator()
    schema = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string", "examples": ["vip", "urgent"]},
                "minItems": 5,  # Více než dostupných examples
                "maxItems": 10
            }
        }
    }

    # Generovat vícekrát a ověřit chování
    for _ in range(10):
        result = generator.generate(schema)
        tags = result.get("tags", [])

        # Mělo by být alespoň minItems položek (5)
        assert len(tags) >= 5, f"Should have at least minItems (5), got {len(tags)}"
        # Všechny tagy by měly být z examples (mohou být duplicity při výběru s náhradou)
        assert all(tag in ["vip", "urgent"] for tag in tags), f"All tags should be from examples, got {tags}"
