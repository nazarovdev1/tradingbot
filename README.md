# Forex Signal Telegram Boti

Node.js, Telegraf va TwelveData API-dan foydalanuvchi XAUUSD savdo signallarini beruvchi Forex signal Telegram boti.

## Xususiyatlar

- XAU/USD (Oltin) uchun SOTIB OLISH/SOTISH/NEYTRAL signallarini taqdim etadi
- RSI(14) va EMA(200) ko'rsatkichlaridan foydalanadi
- Toza va formatlangan signal chiqishi
- XAU/USD tugmasi bilan maxsus klaviatura (XAUUSD 🟡 OLTIN sifatida ko'rsatiladi)

## Talablalar

- Node.js (v14 yoki undan yuqori versiya)
- npm (v6 yoki undan yuqori versiya)
- Telegram Bot Token
- TwelveData API Kaliti (bepul tarif)

## O'rnatish

1. Bu repositoryni kompyuteringizga klon qiling yoki yuklab oling
2. Terminalda loyihaning papkasiga kiring
3. Quyidagi buyruq bilan kerakli modullarni o'rnating:

```bash
npm install
```

4. Ilovaga kirish uchun `.env` faylini ildiz papkada yarating va ma'lumotlaringizni kiriting:

```env
BOT_TOKEN=telegram_bot_tokeni_sizniki
TWELVEDATA_KEY=twelvedata_api_kalitingiz
```

## Kerakli Kalitlarni Olish

### Telegram Bot Token
1. Telegram-ni oching va `@BotFather` qidiring
2. Suhbat boshlang va `/newbot` buyrug'ini ishlating
3. Bot yaratish bo'yicha ko'rsatmalarga amal qiling
4. BotFather tomonidan berilgan token-ni ko'chiring

### TwelveData API Kaliti
1. https://twelvedata.com/ manziliga o'ting
2. Bepul hisob yarating
3. Panel bo'limidan API kalitingizni oling

## Foydalanish

1. Botni ishga tushiring:

```bash
npm start
```

2. Telegram-ni oching va botni toping
3. Botni ishga tushirish uchun `/start` yuboring
4. Savdo signallarini olish uchun "XAUUSD 🟡 OLTIN" tugmasini bosing

## Savdo Strategiyasi

Bot endi quyidagi mantiq bilan ishlovchi kengaytirilgan 3X tasdiqlash strategiyasidan foydalanadi:

### SOTIB OLISH SHARTLARI (Barcha 4 ta shart bajarilishi kerak):
- **O'suvchi Trend**: EMA50 > EMA200
- **RSI Sotuvga Qiyson**: RSI < 35 (o'suvchi trendda)
- **Shovqinli Qamrov Patterni**: Oxirgi 2 shamda aniqlangan
- **EMA50 Dan Yuqori Narx**: Joriy narx EMA50 dan yuqorida (oqim davomi)

Barcha shartlar bajarilsa:
**Signal** = SOTIB OLISH
**Ehtimollik** = 90–95%
**Sabab**: 4/4 shartlar bajarildi

### SOTISH SHARTLARI (Barcha 4 ta shart bajarilishi kerak):
- **Tushuvchi Trend**: EMA50 < EMA200
- **RSI Sotuvga Qiyson**: RSI > 65 (tushuvchi trendda)
- **To'qimli Qamrov Patterni**: Oxirgi 2 shamda aniqlangan
- **EMA50 Dan Past Narx**: Joriy narx EMA50 dan pastda (oqim davomi)

Barcha shartlar bajarilsa:
**Signal** = SOTISH
**Ehtimollik** = 90–95%
**Sabab**: 4/4 shartlar bajarildi

### EHTIMOLLIK HISOBLASH
Qanoatlantirilgan shartlar soni asosida:
- **4/4**: 90–95% (Kuchli signal)
- **3/4**: 75–85% (Yaxshi signal)
- **2/4**: 55–65% (O'rtacha signal)
- **1/4**: 20–40% (Slab signal)
- **0/4**: 0–40% (Neytral)

### SHAM PATTERNI MANTIG'I
- **Shovqinli Qamrov**: Oldingi qizil shamni joriy yashil sham to'liq qamrab oladi
- **To'qimli Qamrov**: Oldingi yashil shamni joriy qizil sham to'liq qamrab oladi

## API Javob Formatlari

Bot API javoblarni tushunishga yordam beruvchi so'rovlarni kiritadi. Bot ishga tushirilganda, API javob strukturasi ko'rsatiladi, bu API xatolarini hal etishga yordam beradi.

## Namuna Chiqish

XAUUSD tugmasini bosganda, bot quyidagicha javob qaytaradi:

```
📊 *XAU/USD Kengaytirilgan Savdo Signali*

💰 *Narx:* $2025.60
📊 *RSI (14):* 32.45
📊 *EMA (50):* $2018.30
📊 *EMA (200):* $1995.20
📈 *Sham Patterni:* ✅ HA
O'suvchi Trend
🎯 *Signal:* SOTIB OLISH
🔮 *Ehtimollik:* 82%

💡 *Sabablar:*
  • 3/4 shart bajarildi
  • O'suvchi Trend (EMA50 > EMA200), RSI Sotuvga Qiyson, Shovqinli Qamrov Patterni

*Eslatma: Bular faqat axborot maqsadida. Har doim o'zingiz savdo qilishdan oldin o'zingiz tekshiruv qiling.*
```

## Fayl Strukturasi

```
├── index.js          # Asosiy bot mantiqi
├── package.json      # Loyiha modullari va konfiguratsiyasi
├── .env             # O'zgaruvchilar (repo-ga kirmaydi)
└── README.md        # Ushbu fayl
```

## Muport Sizlik Eslatmasi

Ushbu bot faqat o'quvchilik va axborot maqsadlarida. Savdoda katta xavf bor va hech qachon o'zgaruvchi pulingizni yo'qotishga tayyor bo'lmasangiz sarmoya sifatida kirmeng. Hech qanday savdo qilishdan oldin doim o'zingiz tekshiruv qiling.

## Litsenziya

MIT
