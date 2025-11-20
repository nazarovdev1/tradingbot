# 🚀 Telegram Bot Ishga Tushirish Qo'llanmasi

## Tezkor Boshlash (3 qadam)

### 1️⃣ SMC Server Ishga Tushirish

**Birinchi terminal oching** va quyidagi buyruqni bajaring:

```bash
python smc_server.py
```

✅ **Muvaffaqiyatli ishga tushganini bilish uchun:**
- `INFO: Application startup complete` ko'rinishi kerak
- `INFO: Uvicorn running on http://0.0.0.0:8000` ko'rinishi kerak

⚠️ **Agar xato chiqsa:**
- Port 8000 band bo'lishi mumkin. Boshqa python process'ni to'xtating
- Yoki `.env` faylida portni o'zgartiring: `AI_SERVER_PORT=8001`

---

### 2️⃣ Telegram Bot Ishga Tushirish

**Ikkinchi terminal oching** va quyidagi buyruqni bajaring:

```bash
run_telegram_bot.bat
```

Yoki oddiy:
```bash
node index.js
```

✅ **Muvaffaqiyatli ishga tushganini bilish uchun:**
- `SMC + AI Confluence Sniper Bot started in polling mode...` ko'rinishi kerak

---

### 3️⃣ Telegram'da Test Qilish

1. **Telegram'ni oching**
2. **Botingizni toping** (BOT_TOKEN'dan olgan bot)
3. **/start** buyrug'ini yuboring

**Ko'rinishi kerak:**
```
🎯 SMC + AI Confluence Sniper Bot is ready!

The bot scans for high-probability setups using Smart Money Concepts + AI confirmation.

Signals are only sent when:
• Price is in a valid SMC zone (OB/FVG)
• AI confirms direction with >85% confidence

Use the button below for manual scan:
[🔍 Manual Sniper Scan]
```

4. **"🔍 Manual Sniper Scan"** button bosing

**Natija:**
- ✅ Signal yoki "No confluence signal detected" xabari
- ✅ **AI Confidence endi > 0 ko'rsatadi!** (masalan, 8.01%)

---

## To'liq Ishga Tushirish Jarayoni

### Terminal 1: SMC Server

```bash
cd "c:\Qwen\trading signal"
python smc_server.py
```

**Bu terminal ochiq qolishi kerak!** Server loglarini ko'rasiz.

### Terminal 2: Telegram Bot

```bash
cd "c:\Qwen\trading signal"
node index.js
```

**Bu terminal ham ochiq qolishi kerak!** Bot loglarini ko'rasiz.

---

## Tekshirish

### SMC Server Ishlayaptimi?

Yangi terminal oching va:
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/health -Method GET
```

**Natija:**
```json
{"status":"ok","smc_engine_loaded":true,"ai_model_loaded":true}
```

### AI Prediction Ishlayaptimi?

```bash
python simple_test.py
```

**Kutilgan natija:**
```
✅ SUCCESS!
Signal: NEUTRAL
Confidence: 0.0801
Raw: -0.008013
```

---

## Avto Signal Monitoring

Bot har **60 soniyada** (1 daqiqa) avtomatik ravishda market'ni tekshiradi va agar:
- ✅ Price valid SMC zone'da bo'lsa
- ✅ AI >85% confidence bilan tasdiqlasa

Signal yuboradi barcha subscribers'ga.

**Monitoring interval o'zgartirish:**

`.env` faylida:
```
AUTO_CHECK_INTERVAL_MS=60000  # 60 soniya (1 daqiqa)
```

Masalan, 5 daqiqa uchun:
```
AUTO_CHECK_INTERVAL_MS=300000  # 5 daqiqa
```

---

## Muammolarni Hal Qilish

### ❌ "AI confidence 0.00" ko'rsatmoqda

**Yechim:** SMC serverni restart qiling
```bash
# Terminal 1'da Ctrl+C bosing
python smc_server.py
```

### ❌ "No valid SMC zone detected"

**Bu normal!** Bot faqat yuqori sifatli setup'lar uchun signal beradi:
- Price Order Block yoki FVG zone'da bo'lishi kerak
- AI >85% confidence bilan tasdiqlashi kerak

Ko'p vaqt signal bo'lmaydi - bu **dizayn bo'yicha**.

### ❌ "Port 8000 already in use"

**Yechim 1:** Eski process'ni to'xtating
```powershell
netstat -ano | findstr :8000
# PID ni topib:
taskkill /PID <PID> /F
```

**Yechim 2:** Portni o'zgartiring
`.env` faylida:
```
AI_SERVER_PORT=8001
```

`index.js` da ham o'zgartiring:
```javascript
const SMC_SERVER_URL = process.env.SMC_SERVER_URL || 'http://127.0.0.1:8001/smc';
const AI_SERVER_URL = process.env.AI_SERVER_URL || 'http://127.0.0.1:8001/predict';
```

### ❌ Bot javob bermayapti

1. **Bot token to'g'rimi?** `.env` faylini tekshiring
2. **Internet bormi?** Bot Telegram API'ga ulanishi kerak
3. **Node.js o'rnatilganmi?** `node --version` tekshiring

---

## Loglarni Ko'rish

### SMC Server Loglari (Terminal 1)
```
INFO: 127.0.0.1:12345 - "POST /predict HTTP/1.1" 200 OK
INFO: 127.0.0.1:12345 - "POST /smc HTTP/1.1" 200 OK
```

### Bot Loglari (Terminal 2)
```
🔍 Running Sniper Strategy Scan...
Sending data to SMC server...
Asking AI for confirmation...
AI Prediction: Signal=NEUTRAL, Confidence=0.0801
```

---

## Keyingi Qadamlar

1. ✅ **Test qiling** - Bir necha marta "Manual Sniper Scan" bosing
2. ✅ **Monitor qiling** - 15-30 daqiqa kutib, avto signal kelishini kuting
3. ⏳ **AI modelni qayta train qiling** - Agar signallar juda kuchsiz bo'lsa
4. ⏳ **Backtest qiling** - Tarixiy ma'lumotlar bilan test qiling

---

## Qo'shimcha Ma'lumot

- **Walkthrough:** [walkthrough.md](file:///C:/Users/akbar/.gemini/antigravity/brain/49452290-8ba3-4c68-997e-834a44808f7c/walkthrough.md)
- **Implementation Plan:** [implementation_plan.md](file:///C:/Users/akbar/.gemini/antigravity/brain/49452290-8ba3-4c68-997e-834a44808f7c/implementation_plan.md)
- **Task List:** [task.md](file:///C:/Users/akbar/.gemini/antigravity/brain/49452290-8ba3-4c68-997e-834a44808f7c/task.md)

---

## Tez Yordam

| Buyruq | Maqsad |
|--------|--------|
| `python smc_server.py` | SMC server ishga tushirish |
| `node index.js` | Telegram bot ishga tushirish |
| `python simple_test.py` | AI test qilish |
| `python test_full_integration.py` | To'liq test |
| `Ctrl+C` | Server/bot to'xtatish |

**Omad! 🚀**
