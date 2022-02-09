"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: lang.py
Description: Localization.
"""
from typing import Dict
import locale as _locale
import os

from framework import define, defined
define("LANG_PY")

# Default locale has a different implementation for non-windows.
import ctypes
if hasattr(ctypes, "windll"):
    # Windows dll is defined.
    def _getDefaultLocale():
        return _locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]

else:
    # Windows dll is not available (non-windows)
    del ctypes

    def _getDefaultLocale():
        return _locale.getdefaultlocale()[0]

if defined("PRIVATE_PY"):
    from private import private
else:
    def private(x): return x

# Set this to the locale to use whenever a given locale
# fails to load, of course you can use `use_fallback=False`
# to raise an error. If this fallback locale fails to load then
# the fallback to the fallback will be to use a blank locale that
# just returns any translation key it is given. e.g. translate("#text") => "#text"
# to disable the blank locale you can use `use_blank_fallback=False`
FALLBACK_LOCALE = "en_US"
BLANK_LOCALE = "__BLANK__"

def _getLocaleFile(locale: str) -> str:
    """
    Returns the filepath from a given locale.
    """
    if locale == BLANK_LOCALE:
        return BLANK_LOCALE

    lang = locale + ".lang"
    path = os.path.join(os.getcwd(), "lang", lang)

    if not os.path.exists(path):
        # The path for this lang does not exist.
        # Use the fallback
        if locale == FALLBACK_LOCALE:
            return _getLocaleFile(BLANK_LOCALE)

        else:
            return _getLocaleFile(FALLBACK_LOCALE)

    return path

def _getLocaleFromFile(filepath: str) -> str:
    """
    Returns the locale name from its filepath.
    """
    return os.path.splitext(os.path.basename(filepath))[0]

def _getTranslationsFromFile(filepath: str) -> Dict[str, str]:
    """
    Returns translations from a file
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

    with open(filepath) as f:
        content = f.read()

    rawLines = content.splitlines()
    lines = []
    for line in rawLines:
        if line.startswith("//"):
            continue
        elif "//" in line:
            line = line[:line.find("//")]
        lines.append(line)

    translations = {}
    for line in lines:
        split = line.split("=")
        if len(split) != 2:
            continue
        translations[split[0].strip()] = split[1].strip()
    return translations

import string
_KEY_CHARACTERS_ = string.ascii_letters + string.digits
del string

class Lang:
    @classmethod
    def from_locale(cls, locale: str) -> "Lang":
        if not isinstance(locale, str):
            raise TypeError("locale must be a string")

        return cls.from_file(_getLocaleFile(locale))

    @classmethod
    def from_file(cls, filepath: str) -> "Lang":
        if not isinstance(filepath, str):
            raise TypeError("filepath must be a string")

        if filepath == BLANK_LOCALE:
            return cls(BLANK_LOCALE, {})

        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        locale = _getLocaleFromFile(filepath)
        translations = _getTranslationsFromFile(filepath)
        return cls(locale, translations)


    @private
    def __init__(self, locale: str, translations: Dict[str, str]):
        # For blank locale.
        self.locale = locale
        self.translations = translations

    def translateKey(self, string: str) -> str:
        """
        Translates a single key.
        """
        if len(string) == 0:
            return ""
        elif string[0] != "#":
            string = "#" + string
            key = string[1:]
        else:
            key = string

        return self.translations.get(key, string)

    def translate(self, string: str) -> str:
        # Iterate through the string translating as we come across "#"
        translated = ""
        key = ""
        keyFound = False

        for c in string:
            if c == "#" and not keyFound:
                keyFound = True
                continue
            elif keyFound:
                if c not in _KEY_CHARACTERS_:
                    keyFound = False
                    translated += self.translateKey(key)
                    key = ""
                else:
                    key += c
                    continue

            translated += c

        if keyFound:
            # String ended in the middle of a key so try to translate it.
            translated += self.translateKey(key)
        return translated

if __name__ == "__main__":
    l = Lang.from_locale("en_US")

    print(l.translate("#test"))
    print()
    print(l.translate("#test world!"))
    print()
    print(l.translate("#test test #test #test #t world!"))