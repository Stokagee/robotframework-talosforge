"""
AI generátor testovacích dat.

Tento modul poskytuje AIGenerator třídu pro generování testovacích dat
pomocí AI modelů (OpenAI, Zhipu AI).
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from .config import get_config, get_active_ai_provider, is_ai_available
from .exceptions import TalosForgeException
from ..utils.logger import log_error, log_warning

logger = logging.getLogger(__name__)


class AIGenerator:
    """
    Generuje data pomocí AI modelů.

    Tato třída poskytuje generování dat pomocí AI modelů jako doplněk
    k Faker generátoru. Používá se pro složité případy, kde nestačí
    jednoduchá pravidla.

    Example:
        >>> generator = AIGenerator()
        >>> schema = {"type": "string", "description": "Generate a realistic Czech name"}
        >>> result = generator.generate(schema)
        >>> print(result)
        'Jan Novák'
    """

    def __init__(self):
        """Inicializuje AIGenerator a nastaví AI klienty."""
        self.config = get_config()
        self.openai_client = None
        self.zhipu_client = None
        self.active_provider = get_active_ai_provider()

        # Inicializace OpenAI klienta
        if self.config.openai_api_key:
            try:
                from openai import OpenAI

                self.openai_client = OpenAI(api_key=self.config.openai_api_key)
            except ImportError:
                log_warning(
                    "Balíček 'openai' není nainstalován. AI generování přes OpenAI nebude dostupné."
                )
            except Exception as e:
                log_warning(f"Nepodařilo se inicializovat OpenAI klienta: {e}")

        # Inicializace Zhipu AI klienta
        if self.config.zhipu_api_key:
            try:
                # Zhipu AI SDK - ověřit název balíčku
                try:
                    from zhipuai import ZhipuAI

                    self.zhipu_client = ZhipuAI(api_key=self.config.zhipu_api_key)
                except ImportError:
                    log_warning(
                        "Balíček 'zhipuai' není nainstalován. AI generování přes Zhipu AI nebude dostupné."
                    )
            except Exception as e:
                log_warning(f"Nepodařilo se inicializovat Zhipu AI klienta: {e}")

        if not is_ai_available():
            log_warning("Žádný AI provider není k dispozici")

    def generate(
        self,
        schema_fragment: Dict[str, Any],
        target: str = "api",
        context_description: Optional[str] = None,
    ) -> Any:
        """
        Generuje data pomocí AI.

        Args:
            schema_fragment: Část JSON Schema pro generování.
            target: "api" nebo "ui" - formát výstupu.
            context_description: Volitelný popis kontextu (např. z description ve schématu).

        Returns:
            Vygenerovaná data (naparsovaná z JSON odpovědi).

        Raises:
            TalosForgeException: Pokud AI není k dispozici nebo volání selže.

        Example:
            >>> generator = AIGenerator()
            >>> schema = {"type": "string", "description": "A realistic Czech full name"}
            >>> result = generator.generate(schema)
            >>> print(result)
            'Jan Novák'
        """
        if not is_ai_available():
            raise TalosForgeException(
                "AI generování není k dispozici. "
                "Nastavte OPENAI_API_KEY nebo ZHIPU_API_KEY environment proměnnou."
            )

        # Sestavit prompt
        prompt = self._build_prompt(schema_fragment, target, context_description)

        # Volat AI API
        response = self._call_ai_api(prompt)

        # Parsovat odpověď
        result = self._parse_ai_response(response)

        return result

    def _build_prompt(
        self,
        schema: Dict[str, Any],
        target: str,
        context_description: Optional[str],
    ) -> str:
        """
        Sestaví prompt pro AI model.

        Args:
            schema: JSON Schema fragment.
            target: "api" nebo "ui".
            context_description: Volitelný kontext.

        Returns:
            Prompt řetězec pro AI.

        Example:
            >>> generator = AIGenerator()
            >>> schema = {"type": "string", "minLength": 5}
            >>> prompt = generator._build_prompt(schema, "api", None)
            >>> "Generate a single data value" in prompt
            True
        """
        # Základní instrukce
        instructions = []
        instructions.append("Generate a single data value for a property in a test data structure.")

        # Informace o locale - generovat ve správném jazyce
        locale = self.config.locale
        if locale.startswith("en_"):
            instructions.append("Generate data in English (en_US locale).")
        elif locale.startswith("cs_"):
            instructions.append("Generate data in Czech (cs_CZ locale).")
        else:
            instructions.append(f"Generate data in {locale} locale.")

        # Informace o target
        if target == "ui":
            instructions.append(
                "The target is for UI testing - keys will be used as form field identifiers."
            )
        else:
            instructions.append("The target is for API testing - generate JSON-compatible data.")

        # JSON Schema jako JSON
        schema_json = json.dumps(schema, ensure_ascii=False)
        instructions.append(f"The property schema is: {schema_json}")

        # Kontext
        if context_description:
            instructions.append(f"Additional context: {context_description}")

        # Instrukce pro formát výstupu
        instructions.append(
            "Please return only the generated value as a valid JSON string "
            '(e.g., "string", 123, true, {"key": "value"}, [1,2,3]). '
            "Do not include any explanations or markdown formatting."
        )

        return " ".join(instructions)

    def _call_ai_api(self, prompt: str) -> str:
        """
        Volá AI API podle aktivního providera.

        Args:
            prompt: Prompt pro AI.

        Returns:
            Odpověď od AI jako řetězec.

        Raises:
            TalosForgeException: Pokud volání selže.

        Example:
            >>> generator = AIGenerator()
            >>> response = generator._call_ai_api("Generate a random name")
            >>> isinstance(response, str)
            True
        """
        if self.active_provider == "openai" and self.openai_client:
            return self._call_openai_api(prompt)
        elif self.active_provider == "zhipu" and self.zhipu_client:
            return self._call_zhipu_api(prompt)
        else:
            raise TalosForgeException("Žádný aktivní AI provider není k dispozici")

    def _call_openai_api(self, prompt: str) -> str:
        """
        Volá OpenAI API.

        Args:
            prompt: Prompt pro OpenAI.

        Returns:
            Odpověď od OpenAI.

        Raises:
            TalosForgeException: Pokud volání selže.
        """
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test data generator. Generate realistic data according to the given JSON Schema.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Chyba při volání OpenAI API: {e}")
            raise TalosForgeException(f"Chyba při volání OpenAI API: {e}")

    def _call_zhipu_api(self, prompt: str) -> str:
        """
        Volá Zhipu AI API.

        Args:
            prompt: Prompt pro Zhipu AI.

        Returns:
            Odpověď od Zhipu AI.

        Raises:
            TalosForgeException: Pokud volání selže.
        """
        try:
            # Zhipu AI API volání - ověřit správné API
            response = self.zhipu_client.chat.completions.create(
                model=self.config.zhipu_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test data generator. Generate realistic data according to the given JSON Schema.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Chyba při volání Zhipu AI API: {e}")
            raise TalosForgeException(f"Chyba při volání Zhipu AI API: {e}")

    def _parse_ai_response(self, response: str) -> Any:
        """
        Parsuje JSON odpověď od AI.

        Args:
            response: Odpověď od AI (řetězec).

        Returns:
            Naparsovaná data.

        Example:
            >>> generator = AIGenerator()
            >>> result = generator._parse_ai_response('\"Hello World\"')
            >>> result
            'Hello World'
        """
        if not response:
            return None

        # Odstranit markdown code blocks
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        # Zkusit naparsovat jako JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Zkusit extrahovat JSON z textu pomocí regex
            json_pattern = r"\{.*\}|\[.*\]|\"[^\"]*\"|\d+\.?\d*|true|false|null"
            matches = re.findall(json_pattern, response, re.DOTALL)
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass

            # Pokud parsování selže, vrátíme raw response
            logger.warning(f"Nepodařilo se naparsovat AI odpověď jako JSON: {response}")
            return response

    def is_available(self) -> bool:
        """
        Zkontroluje, zda je AI generátor k dispozici.

        Returns:
            True pokud je k dispozici alespoň jeden AI provider.

        Example:
            >>> generator = AIGenerator()
            >>> available = generator.is_available()
        """
        return is_ai_available()

    def get_provider(self) -> Optional[str]:
        """
        Vrátí název aktivního AI providera.

        Returns:
            Název providera ("openai", "zhipu") nebo None.

        Example:
            >>> generator = AIGenerator()
            >>> provider = generator.get_provider()
        """
        return self.active_provider
