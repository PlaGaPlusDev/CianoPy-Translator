from abc import ABC, abstractmethod
import deepl
import googletrans
from yandex import Translater as YandexTranslate

class BaseTranslator(ABC):
    """Abstract base class for all translation services."""
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def translate(self, text, source_lang, target_lang):
        """
        Translates a single string of text.
        Should return a tuple: (success: bool, result: str)
        """
        pass

class GoogleTranslator(BaseTranslator):
    def __init__(self):
        super().__init__("Google Translate")
        self.translator = googletrans.Translator()

    def translate(self, text, source_lang, target_lang):
        # googletrans uses 'auto' for auto-detection
        source = source_lang.lower() if source_lang != "Auto" else 'auto'
        try:
            translated = self.translator.translate(
                text,
                src=source,
                dest=target_lang.lower()
            )
            return True, translated.text
        except Exception as e:
            return False, f"Google Translate Error: {e}"

class DeepLTranslator(BaseTranslator):
    def __init__(self, api_key):
        super().__init__("DeepL")
        if not api_key:
            raise ValueError("DeepL API key is required.")
        try:
            self.translator = deepl.Translator(api_key)
            # Verify authentication by checking account usage
            self.translator.get_usage()
        except Exception as e:
            raise ConnectionError(f"Failed to authenticate with DeepL: {e}")

    def translate(self, text, source_lang, target_lang):
        # DeepL uses None for auto-detection
        source = source_lang.upper() if source_lang != "Auto" else None
        try:
            result = self.translator.translate_text(
                text,
                source_lang=source,
                target_lang=target_lang.upper()
            )
            return True, result.text
        except deepl.DeepLException as e:
            return False, f"DeepL Error: {e}"

class YandexTranslator(BaseTranslator):
    def __init__(self, api_key):
        super().__init__("Yandex Translate")
        if not api_key:
            raise ValueError("Yandex API key is required.")
        self.translator = YandexTranslate(key=api_key)

    def translate(self, text, source_lang, target_lang):
        try:
            self.translator.set_text(text)
            # The library detects language if from_lang is not set
            if source_lang.lower() != 'auto':
                self.translator.set_from_lang(source_lang.lower())

            self.translator.set_to_lang(target_lang.lower())

            translated_text = self.translator.translate()
            return True, translated_text
        except Exception as e:
            # The library raises custom exceptions, but catching Exception is safer
            return False, f"Yandex Translate Error: {e}"
