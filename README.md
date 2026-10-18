# KinoBot — Telegram guruhida qisqa video uzatish

Bu boshlang‘ich loyiha: Telegram bot komandalarni qabul qiladi, bitta **shaxsiy Telegram akkaunti** PyTgCalls orqali guruhdagi faol voice/video chatga video uzatadi.

## Muhim cheklovlar

- Telegram bot akkauntining o‘zi guruh video chatiga video uzata olmaydi; `SESSION_STRING` orqali avtorizatsiya qilingan **shaxsiy akkaunt** ishlatiladi.
- Guruhdagi voice/video chatni avval Telegram ilovasida qo‘lda boshlang. API orqali call yaratish har bir chatda bir xil ishlamaydi.
- Ijro API/library versiyasi, Telegram cheklovlari yoki hosting sabab ishlamasligi mumkin; deploydan so‘ng loglarni tekshiring.
- YouTube qidiruvi/yuklab olish barcha videolarda ishlashiga kafolat yo‘q. Faqat ko‘rish yoki uzatish huquqingiz bor materiallardan foydalaning va YouTube/Telegram shartlariga rioya qiling.
- Video 180 soniyagacha, 180 MB gacha cheklangan. `MAX_SECONDS` bilan o‘zgartirish mumkin.
- Render free web services 15 daqiqalik faoliyatsizlikdan so‘ng to‘xtashi mumkin; background worker odatda pulli. `render.yaml`dagi `starter` pulli worker rejasini anglatadi. Narx va mavjudlikni Render panelida tekshiring.
- Ikkinchi shaxsiy akkaunt majburiy emas. Bitta stream akkaunti video uzatishga yetadi. Ikkinchi akkauntni qo‘shish alohida sessiya va qo‘shimcha call boshqaruvi talab qiladi.

## 1. Telegram API va bot

1. `https://my.telegram.org` orqali `API_ID` va `API_HASH` oling.
2. `@BotFather` orqali bot ochib `BOT_TOKEN` oling.
3. Botni kerakli guruhga qo‘shing.
4. Shaxsiy stream akkauntini ham shu guruhga qo‘shing.
5. Guruhda voice/video chatni qo‘lda boshlang va test paytida stream akkauntiga kerakli ruxsatlarni bering.

## 2. SESSION_STRING yaratish

`session_gen.py`ni ishonchli qurilmada ishga tushiring. Termux’da:

```bash
pkg update
pkg install python
pip install pyrogram tgcrypto
python session_gen.py
```

Telegram telefon raqami, login kodi va 2 bosqichli parol so‘ralishi mumkin. Chiqadigan `SESSION_STRING`ni maxfiy saqlang. Uni hech kimga yubormang va GitHub’ga joylamang.

## 3. GitHub va Render

1. Ushbu fayllarni GitHub repository’ga yuklang.
2. Render’da **Background Worker** yarating va repository’ni ulang; Dockerfile avtomatik ishlatiladigan qilib Docker runtime tanlang.
3. Render Dockerfile orqali FFmpeg va Python kutubxonalarini o‘rnatadi.
4. Environment variables qo‘shing:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - `SESSION_STRING`
   - `ALLOWED_CHAT_ID` — guruh ID raqami
   - `MAX_SECONDS` — `180`
6. Deploy qiling va Render Logs’da xatolarni tekshiring.

**Eslatma:** Render background worker bepul rejada mavjud bo‘lmasligi mumkin. `render.yaml`dagi `starter` pulli worker planidir. Bepul web service video translyatsiyasi uchun ishonchli 24/7 yechim emas.

## 4. Ishlatish

Guruhdagi ovozli chat faol bo‘lgach:

- `/play Sintel short film` — YouTube’da birinchi natijani topib, qisqa videoni yuklaydi.
- `/play https://...` — to‘g‘ridan-to‘g‘ri media havolasi bo‘lsa, uni sinaydi.
- `Pause`, `Davom`, `To‘xtatish` tugmalari orqali boshqarish.
- `/stop` — translyatsiyani to‘xtatish.

## Xavfsizlik

- `SESSION_STRING` Telegram akkauntingizga kirish imkonini beradi. Uni token kabi himoya qiling.
- `.env` faylini GitHub’ga yuklamang.
- `ALLOWED_CHAT_ID`ni o‘zingizning guruh ID’ingizga qo‘ying.
- Agar sessiya oshkor bo‘lsa, Telegram’dagi Active Sessions bo‘limidan sessiyani bekor qiling.
