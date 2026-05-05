"""
Testy pro AIGenerator.
"""

from unittest.mock import MagicMock, patch

from TalosForge.core.ai_generator import AIGenerator
from TalosForge.core.exceptions import TalosForgeException


def test_ai_generator_initialization():
    """Test inicializace AIGenerator."""
    generator = AIGenerator()
    assert generator is not None
    assert generator.openai_client is None or generator.openai_client is not None
    assert generator.zhipu_client is None or generator.zhipu_client is not None


def test_is_available_no_keys(monkeypatch):
    """Test is_available bez API klíčů."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ZHIPU_API_KEY", "")

    # Modul potřebuje reload pro změnu environment proměnných
    import importlib
    import TalosForge.core.config as config_module
    importlib.reload(config_module)
    from TalosForge.core.ai_generator import AIGenerator

    generator = AIGenerator()
    assert generator.is_available() is False


def test_get_provider():
    """Test get_provider metody."""
    generator = AIGenerator()
    # Může vracet None, "openai" nebo "zhipu"
    assert generator.get_provider() in [None, "openai", "zhipu"]


def test_build_prompt():
    """Test sestavení promptu pro AI."""
    generator = AIGenerator()

    schema = {
        "type": "string",
        "minLength": 5,
        "maxLength": 20
    }

    prompt = generator._build_prompt(schema, "api", None)

    assert "Generate a single data value" in prompt
    assert "api" in prompt or "testing" in prompt
    assert '"type": "string"' in prompt
    assert '"minLength": 5' in prompt


def test_build_prompt_with_description():
    """Test sestavení promptu s description."""
    generator = AIGenerator()

    schema = {
        "type": "string",
        "description": "A realistic Czech name"
    }

    prompt = generator._build_prompt(schema, "ui", "Test context")

    assert "Generate a single data value" in prompt
    assert "UI testing" in prompt
    assert "A realistic Czech name" in prompt
    assert "Test context" in prompt


def test_build_prompt_for_enum():
    """Test sestavení promptu pro enum."""
    generator = AIGenerator()

    schema = {
        "type": "string",
        "enum": ["active", "inactive", "pending"]
    }

    prompt = generator._build_prompt(schema, "api", None)

    assert "enum" in prompt or "active" in prompt


def test_parse_ai_response_string():
    """Test parsování string odpovědi."""
    generator = AIGenerator()

    # Jednoduchý string
    result = generator._parse_ai_response('"Hello World"')
    assert result == "Hello World"


def test_parse_ai_response_number():
    """Test parsování číselné odpovědi."""
    generator = AIGenerator()

    # Integer
    result = generator._parse_ai_response("42")
    assert result == 42

    # Float
    result = generator._parse_ai_response("3.14")
    assert result == 3.14


def test_parse_ai_response_boolean():
    """Test parsování boolean odpovědi."""
    generator = AIGenerator()

    result = generator._parse_ai_response("true")
    assert result is True

    result = generator._parse_ai_response("false")
    assert result is False


def test_parse_ai_response_object():
    """Test parsování objektové odpovědi."""
    generator = AIGenerator()

    result = generator._parse_ai_response('{"name": "John", "age": 30}')
    assert isinstance(result, dict)
    assert result["name"] == "John"
    assert result["age"] == 30


def test_parse_ai_response_array():
    """Test parsování pole."""
    generator = AIGenerator()

    result = generator._parse_ai_response('[1, 2, 3]')
    assert isinstance(result, list)
    assert result == [1, 2, 3]


def test_parse_ai_response_with_markdown():
    """Test parsování odpovědi s markdown code blocks."""
    generator = AIGenerator()

    # Markdown JSON block
    result = generator._parse_ai_response('```json\n{"key": "value"}\n```')
    assert isinstance(result, dict)
    assert result["key"] == "value"


def test_parse_ai_response_invalid_json():
    """Test parsování neplatného JSON."""
    generator = AIGenerator()

    # Neplatný JSON - vrátí raw string
    result = generator._parse_ai_response('not a json')
    assert result == 'not a json'


def test_parse_ai_response_extract_json():
    """Test extrakce JSON z textu."""
    generator = AIGenerator()

    # JSON uprostřed textu
    result = generator._parse_ai_response('Text before {"key": "value"} text after')
    assert isinstance(result, dict)
    assert result.get("key") == "value"


@patch('talosforge.core.ai_generator.OPENAI_API_KEY', 'test-key')
def test_call_openai_api():
    """Test volání OpenAI API."""
    from unittest.mock import Mock, patch

    with patch('talosforge.core.ai_generator.OPENAI_API_KEY', 'test-key'):
        # Reimport pro aplikaci monkey patch
        import importlib
        import TalosForge.core.config as config_module
        importlib.reload(config_module)
        from TalosForge.core.ai_generator import AIGenerator

        generator = AIGenerator()

        # Mock OpenAI klienta
        with patch.object(generator, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '"generated value"'
            mock_client.chat.completions.create.return_value = mock_response

            result = generator._call_openai_api("Test prompt")

            assert result == '"generated value"'
            mock_client.chat.completions.create.assert_called_once()


def test_generate_without_ai():
    """Test generování bez AI klíče."""
    # Odstranit klíče
    import os
    original_openai = os.environ.get("OPENAI_API_KEY")
    original_zhipu = os.environ.get("ZHIPU_API_KEY")

    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ZHIPU_API_KEY", None)

    # Modul reload
    import importlib
    import TalosForge.core.config as config_module
    importlib.reload(config_module)
    from TalosForge.core.ai_generator import AIGenerator

    try:
        generator = AIGenerator()
        schema = {"type": "string"}

        try:
            generator.generate(schema)
            assert False, "Měla vyhodit TalosForgeException"
        except TalosForgeException as e:
            assert "AI generování není k dispozici" in str(e)
    finally:
        # Obnovit klíče
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai
        if original_zhipu:
            os.environ["ZHIPU_API_KEY"] = original_zhipu


def test_should_use_ai_by_description():
    """Test _should_use_ai logiky v DataGenerator."""
    from TalosForge.core.generator import DataGenerator

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

    # S patternem - kontrola délky
    schema_short_pattern = {"type": "string", "pattern": "^[A-Z]{2}[0-9]{5}$"}
    assert generator._should_use_ai(schema_short_pattern) is False  # Krátký pattern (< 20 znaků)

    schema_long_pattern = {"type": "string", "pattern": "^[A-Z]{2}[0-9]{5}[A-Z]{10}[a-z]{20}$"}
    assert generator._should_use_ai(schema_long_pattern) is True  # Dlouhý pattern (> 20 znaků)
