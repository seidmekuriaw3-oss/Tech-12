---
name: Translation system
description: How UI translations work — no external API, static dict only.
---

googletrans was removed (unreliable due to frequent Google API changes).
utils/translation_cache.py is now a pure static dictionary for am/en/ar.
Product content uses multilingual DB columns: name_am, name_ar, description_am, description_ar.
translate_text() looks up key in FALLBACK_TEXTS dict, returns original text if not found.

**Why:** googletrans breaks silently; DB already stores multilingual content per-field.
**How to apply:** Add new UI strings to FALLBACK_TEXTS in all three languages (am/en/ar).
