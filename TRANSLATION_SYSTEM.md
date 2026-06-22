# Backend Translation System - Implementation Guide

## Overview
The translation system has been implemented with the following features:
- **Dynamic Translation**: Uses googletrans library to translate content on-the-fly
- **Intelligent Caching**: LRU cache prevents repeated API calls (1000 entry cache)
- **Fallback Strategy**: Manual TEXTS dictionary + fallback translations ensure service availability
- **Error Handling**: Gracefully degrades if translation fails
- **Admin Management**: Routes to clear cache and monitor translation statistics

## Features Implemented

### 1. Translation Function (`utils/translation_cache.py`)
```python
translate_text(text, target_lang='en')  # Translates text with caching
batch_translate(texts, target_lang='en')  # Translates multiple texts
clear_translation_cache()  # Admin function to clear cache
get_translation_stats()  # Get cache hit/miss statistics
```

### 2. Language Support
- **Amharic** (am) - ስብጥር
- **English** (en) - Default source language
- **Arabic** (ar) - العربية

### 3. Caching Strategy
- **LRU Cache**: Up to 1000 translations cached in memory
- **Hybrid Approach**: 
  - Static UI elements use manual TEXTS dictionary (fast)
  - Dynamic content uses googletrans with caching (accurate)
  - Fallback to original text if translation fails

### 4. Error Handling
- Missing dependencies: Falls back to FALLBACK_TEXTS
- Network issues: Returns original English text
- Invalid language codes: Returns original text with warning

## API Endpoints

### Translation Status (Admin)
```
GET /admin/translations/status
- Returns: Cache statistics and supported languages
- Requires: Admin authentication
```

### Clear Translation Cache (Admin)
```
POST /admin/translations/clear
- Effect: Clears LRU cache
- Requires: Admin authentication
- Returns: Success message
```

### Translate Text (Public API)
```
POST /api/translate
Request: {
    "text": "Hello World",
    "target_lang": "am"
}
Response: {
    "status": "success",
    "original": "Hello World",
    "translated": "ሰላም ዓለም",
    "language": "am"
}
```

### Batch Translate (Public API)
```
POST /api/translate-batch
Request: {
    "texts": ["Hello", "World", "Furniture"],
    "target_lang": "ar"
}
Response: {
    "status": "success",
    "translations": {
        "Hello": "مرحبا",
        "World": "العالم",
        "Furniture": "الأثاث"
    },
    "language": "ar",
    "count": 3
}
```

## Integration with Existing System

### Updated Functions in app.py

#### `get_text(key, lang=None)`
Now uses a hybrid approach:
1. Checks manual TEXTS dictionary first (fast, for static UI)
2. Falls back to dynamic translation for missing keys
3. Returns original text if all else fails

```python
# Usage in templates
{{ t['home'] }}  # Gets "Home" (or translated version)
{{ get_text('Any dynamic text', lang) }}  # Translates on demand
```

### Configuration
- Supported languages: `['am', 'en', 'ar']`
- Default language: `'am'` (Amharic)
- Cache size: 1000 entries
- Timeout: No timeout (LRU based on hits)

## Performance Considerations

### Cache Statistics
The system tracks:
- **Hits**: Translations retrieved from cache
- **Misses**: New translations computed
- **Hit Rate**: Percentage of cache hits
- **Max Size**: 1000 translations in memory
- **Current Size**: Active translations

Example stats:
```json
{
    "hits": 450,
    "misses": 50,
    "maxsize": 1000,
    "currsize": 50,
    "hit_rate": 0.9
}
```

## Dependencies

### Required
- `googletrans==4.0.0rc1` - For dynamic translation
- `Flask==2.3.3` - Web framework
- `Flask-Caching` - For cache management

### Optional (Already Installed)
- `requests` - HTTP library
- `python-dotenv` - Environment variables

## Troubleshooting

### Translation Falls Back to English
**Cause**: googletrans import failed (Python version compatibility)
**Solution**: System automatically uses manual TEXTS + fallback translations

### Slow Translations on First Load
**Expected Behavior**: First translation hits googletrans API
**Optimization**: Subsequent requests are cached - subsequent calls are instant

### Cache Growing Too Large
**Monitor**: Use `/admin/translations/status` endpoint
**Action**: Clear cache with `/admin/translations/clear` endpoint

## Future Enhancements

1. **Persistent Cache**: Store translations in database for faster startup
2. **Pre-translation**: Cache common product names and categories at startup
3. **User Corrections**: Allow admins to override translations
4. **Lazy Loading**: Load translations only when language is changed
5. **Offline Mode**: Use pre-translated fallback for all content when offline

## Migration Notes

### From Old System
- Old TEXTS dictionary still works as primary fallback
- No changes needed to existing template code
- New features are automatically available

### For Developers
```python
# Old way (still works)
text = TEXTS['am']['home']  # 'መነሻ'

# New way (recommended)
text = get_text('home', 'am')  # Uses cache + fallback
text = translate_text('Any text', 'am')  # Force dynamic translation
```

## Testing

```bash
# Test import
python -c "from utils.translation_cache import translate_text"

# Test translation function
python -c "
from utils.translation_cache import translate_text, get_translation_stats
result = translate_text('Hello', 'am')
stats = get_translation_stats()
print(f'Translation: {result}')
print(f'Cache stats: {stats}')
"
```

## Monitoring

### Health Check
Include translation cache stats in `/health/details`:
```json
{
    "cache": {
        "type": "SimpleCache",
        "default_timeout": 300
    },
    "translations": {
        "hits": 1200,
        "misses": 150,
        "hit_rate": 0.889
    }
}
```

## Support

For issues:
1. Check `/admin/translations/status` for cache health
2. Review logs for translation errors
3. Clear cache if needed: POST `/admin/translations/clear`
4. Fallback to manual TEXTS updates if needed

---
**Last Updated**: May 6, 2026
**Version**: 1.0
**Status**: Production Ready (with fallback support)
