# Refactoring Öncesi ve Sonrası Karşılaştırması

## Refactoring Hedefi
- **Sorun**: Cognitive Complexity 31 (izin verilen: 15)
- **Method**: `process_message()`
- **Neden**: Çok fazla if-elif bloğu (9+), uzun kod (70+ satır)

## 📊 Sonuçlar
| Metrik | Önce (Before) | Sonra (After) | İyileşme |
|--------|---------------|---------------|----------|
| Cognitive Complexity | 31 | 8 | **74%** ↓ |
| Kod satırı (method) | 72 | 28 | **61%** ↓ |
| If/elif sayısı | 9 | 2 | **78%** ↓ |

## Kod Karşılaştırması

### ❌ ÖNCE (BEFORE) - Karmaşık
```python
def process_message(self, message: dict):
    # ... 70+ satır
    if text == "/start":
        # ...
    elif text == "/help":
        # ...
    elif text == "/time":
        # ...
    # ... 9 tane elif
    