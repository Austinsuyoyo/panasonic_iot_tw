"""Guard tests for entity translations.

Every entity the integration creates passes ``name=`` and ``translation_key=``
to a ``_create_*`` helper. The name is only the fallback shown when Home
Assistant has no translation for the active language; the translation file is
what users actually see. The two are edited separately, so they drift:
five air-conditioner switches lost their ``translation_key`` entirely (the
entities fell back to a hardcoded name), and a dryer sensor kept a stale
"bit 1" label after its mask moved to bit 3.

These tests fail when a key is missing, when a key exists in one language
file but not the other, or when a translation is left behind after its entity
is removed.
"""
import json
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).resolve().parents[2] / "custom_components" / "panasonic_iot_tw"
DEVICES_DIR = COMPONENT / "devices"
TRANSLATIONS_DIR = COMPONENT / "translations"

_LANGUAGES = ("en", "zh-Hant")

# Entities that do not go through a ``_create_*`` helper, so the source scan
# cannot see them: the climate and humidifier platforms own their own classes.
# Keep these in sync when a platform entity is added or removed.
_PLATFORM_OWNED_KEYS = {
    "air_conditioner_climate",
    "dehumidifier_control",
}

# A `self._create_xxx(` call runs until the next call at the same indent level.
_CALL_SPLIT_RE = re.compile(r"self\._create_\w+\(")
_NAME_RE = re.compile(r'\bname="([^"]+)"')
_KEY_RE = re.compile(r'\btranslation_key="([^"]+)"')


def _iter_entity_calls():
    """Yield (module, name, translation_key) for every entity factory call."""
    for path in sorted(DEVICES_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        blocks = _CALL_SPLIT_RE.split(source)[1:]
        for block in blocks:
            name = _NAME_RE.search(block)
            if not name:
                # Helper calls without a name are not entity factories.
                continue
            key = _KEY_RE.search(block)
            yield path.name, name.group(1), (key.group(1) if key else None)


def _load_translations(language):
    """Return the entity translation table for a language."""
    path = TRANSLATIONS_DIR / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))["entity"]


@pytest.fixture(scope="module")
def translations():
    return {language: _load_translations(language) for language in _LANGUAGES}


def _flatten(translations_for_language):
    """Map translation key -> platform for one language."""
    flat = {}
    for platform, entities in translations_for_language.items():
        for key, payload in entities.items():
            flat[key] = (platform, payload)
    return flat


class TestEntityTranslationCoverage:
    """Every entity factory call must reference a real translation."""

    def test_every_entity_declares_a_translation_key(self):
        missing = [
            f"{module}: {name}"
            for module, name, key in _iter_entity_calls()
            if key is None
        ]
        assert missing == [], (
            "These entities have no translation_key, so their hardcoded name is "
            f"all a user ever sees: {missing}"
        )

    def test_declared_keys_exist_in_every_language(self, translations):
        flat = {language: _flatten(table) for language, table in translations.items()}
        problems = []
        for module, name, key in _iter_entity_calls():
            if key is None:
                continue
            for language, table in flat.items():
                if key not in table:
                    problems.append(f"{module}: {key} missing from {language}.json")
        assert problems == [], problems

    def test_every_translation_has_a_name(self, translations):
        problems = []
        for language, table in translations.items():
            for key, (platform, payload) in _flatten(table).items():
                if not payload.get("name"):
                    problems.append(f"{language}.json: {platform}.{key} has no name")
        assert problems == [], problems

    def test_language_files_define_the_same_keys(self, translations):
        flat = {language: _flatten(table) for language, table in translations.items()}
        reference = set(flat[_LANGUAGES[0]])
        problems = []
        for language, table in flat.items():
            only_here = sorted(table.keys() - reference)
            missing_here = sorted(reference - table.keys())
            problems.extend(f"{language}: only here {only_here}" if only_here else [])
            problems.extend(f"{language}: missing {missing_here}" if missing_here else [])
        assert problems == [], problems

    def test_no_translation_is_orphaned(self, translations):
        """A key with no entity factory call is a leftover from a removed entity."""
        declared = {key for _, _, key in _iter_entity_calls() if key}
        declared |= _PLATFORM_OWNED_KEYS
        problems = []
        for language, table in translations.items():
            orphans = sorted(set(_flatten(table)) - declared)
            if orphans:
                problems.append(f"{language}.json: {orphans}")
        assert problems == [], problems
