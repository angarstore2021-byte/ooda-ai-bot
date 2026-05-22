"""
OODA AI Office — Professional Bot (Rasm + Matn)
Groq Vision + gemma2-9b-it
"""

import os
import asyncio
import logging
import base64
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GROQ_KEY       = os.getenv("GROQ_KEY", "")

groq_client = Groq(api_key=GROQ_KEY)

TEXT_PROMPT = """Sen OODA AI Office — 4 ta mutaxassis agentdan iborat professional maslahatchi.

Har bir savol uchun QUYIDAGI FORMATDA javob ber:

🧠 *Rex (Kuzat):*
[1-2 gap]

🔬 *Nova (Tahlil):*
[1-2 gap]

⚙️ *Axel (Qaror):*
[1-2 gap]

🎯 *Lyra (Xulosa):*
[2-3 gap]

💡 *Foydali havolalar:*
[2-3 ta real URL]

QOIDALAR: O'zbek tilida, qisqa, faqat shu format, Markdown ishlat."""

IMAGE_PROMPT = """Sen OODA AI Office — rasmlarni professional tahlil qiluvchi AI.

Rasmni ko'rib QUYIDAGI FORMATDA javob ber:

🔍 *Rasm tahlili:*
[Rasmda nima ko'rinayotgani - 2-3 gap]

🧠 *Rex (Kuzat):*
[1-2 gap: rasmning asosiy jihatlari]

🔬 *Nova (Tahlil):*
[1-2 gap: chuqur tahlil]

⚙️ *Axel (Qaror):*
[1-2 gap: tavsiya yoki harakat]

🎯 *Lyra (Xulosa):*
[2-3 gap: yakuniy xulosa]

QOIDALAR: O'zbek tilida, qisqa, faqat shu format, Markdown ishlat."""


def ask_text(question: str) -> str:
    resp = groq_client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[
            {"role": "system", "content": TEXT_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=600,
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()


def ask_image(image_bytes: bytes, caption: str = "") -> str:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    user_text = caption if caption else "Ushbu rasmni tahlil qil."
    resp = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": IMAGE_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        },
                    },
                    {
                        "type": "text",
                        "text": user_text,
                    },
                ],
            },
        ],
        max_tokens=600,
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 *OODA AI Office* — Professional AI\n\n"
        "🧠 Rex · 🔬 Nova · ⚙️ Axel · 🎯 Lyra\n\n"
        "📝 *Matn* yuboring — maslahat oling\n"
        "🖼 *Rasm* yuboring — tahlil qiling\n\n"
        "/help — yordam",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Yordam*\n\n"
        "*Matn savollari:*\n"
        "• Biznes strategiyasi\n"
        "• Marketing tavsiyalari\n"
        "• Har qanday savol\n\n"
        "*Rasm tahlili:*\n"
        "• Grafik yoki jadval rasmi\n"
        "• Mahsulot rasmi\n"
        "• Sxema yoki dizayn\n"
        "• Skrinshotlar\n\n"
        "Rasmni caption (izoh) bilan yuborsangiz, aniqroq tahlil qiladi!",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return

    status_msg = await update.message.reply_text(
        "⚡ Tahlil qilinmoqda...",
        parse_mode="Markdown",
    )

    loop = asyncio.get_event_loop()

    try:
        answer = await loop.run_in_executor(None, ask_text, question)

        await ctx.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
        )

        full = f"❓ *{question}*\n━━━━━━━━━━━━━━━\n{answer}"
        if len(full) > 4000:
            full = full[:3997] + "..."

        await update.message.reply_text(full, parse_mode="Markdown")

    except Exception as e:
        await ctx.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="❌ Xatolik. Qaytadan urinib ko'ring.",
        )
        logging.error(f"Matn xato: {e}")


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""

    status_msg = await update.message.reply_text("🔍 Rasm tahlil qilinmoqda...")

    try:
        photo = update.message.photo[-1]
        file = await ctx.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            None, ask_image, bytes(image_bytes), caption
        )

        await ctx.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
        )

        full = f"🖼 *Rasm tahlili*\n━━━━━━━━━━━━━━━\n{answer}"
        if len(full) > 4000:
            full = full[:3997] + "..."

        await update.message.reply_text(full, parse_mode="Markdown")

    except Exception as e:
        await ctx.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="❌ Rasmni tahlil qilib bo'lmadi. Qaytadan urinib ko'ring.",
        )
        logging.error(f"Rasm xato: {e}")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 OODA AI Office — Rasm + Matn versiyasi!")
    app.run_polling()


if __name__ == "__main__":
    main()
