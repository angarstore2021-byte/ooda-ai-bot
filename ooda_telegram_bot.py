"""
OODA AI Office — Telegram Bot (Groq - optimallashtirilgan)
"""

import os
import asyncio
import logging
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

AGENTS = {
    "rex":  { "name": "Rex",  "emoji": "🧠", "role": "Kuzat",
              "sys": "Sen Rex. OODA 'Kuzat' bosqichi. O'zbek tilida FAQAT 2 gap yoz. Qisqa, aniq, manga uslubida. Boshqa hech narsa yozma." },
    "nova": { "name": "Nova", "emoji": "🔬", "role": "Tahlil",
              "sys": "Sen Nova. OODA 'Tahlil' bosqichi. O'zbek tilida FAQAT 2 gap yoz. Mantiqiy, qisqa. Boshqa hech narsa yozma." },
    "axel": { "name": "Axel", "emoji": "⚙️", "role": "Qaror",
              "sys": "Sen Axel. OODA 'Qaror' bosqichi. O'zbek tilida FAQAT 2 gap yoz. Konkret harakat taklif qil. Boshqa hech narsa yozma." },
    "lyra": { "name": "Lyra", "emoji": "🎯", "role": "Xulosa",
              "sys": "Sen Lyra. OODA yakuniy xulosa. O'zbek tilida FAQAT 3 gap yoz. Barcha fikrlarni birlashtirib eng yaxshi yechim ber. Boshqa hech narsa yozma." },
}


def ask_agent(agent_id: str, messages: list) -> str:
    a = AGENTS[agent_id]
    resp = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": a["sys"]}] + messages,
        max_tokens=150,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 *OODA AI Office* ⚡\n\n"
        "🧠 Rex · 🔬 Nova · ⚙️ Axel · 🎯 Lyra\n\n"
        "Savol yuboring — 4 agent 3 sekundda javob beradi!",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return

    status_msg = await update.message.reply_text("⚡ Tahlil qilinmoqda...")

    loop = asyncio.get_event_loop()
    user_msg = [{"role": "user", "content": question}]

    # Parallel: Rex, Nova, Axel
    rex_r, nova_r, axel_r = await asyncio.gather(
        loop.run_in_executor(None, ask_agent, "rex",  user_msg),
        loop.run_in_executor(None, ask_agent, "nova", user_msg),
        loop.run_in_executor(None, ask_agent, "axel", user_msg),
    )

    # Lyra — qisqa xulosa
    lyra_msg = [{"role": "user", "content":
        f"Savol: {question}\nRex: {rex_r}\nNova: {nova_r}\nAxel: {axel_r}\n\nYakuniy xulosa:"}]
    lyra_r = await loop.run_in_executor(None, ask_agent, "lyra", lyra_msg)

    await ctx.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
    )

    result = (
        f"❓ *{question}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🧠 *Rex:* {rex_r}\n\n"
        f"🔬 *Nova:* {nova_r}\n\n"
        f"⚙️ *Axel:* {axel_r}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 *Lyra:* {lyra_r}"
    )

    if len(result) > 4000:
        result = result[:3997] + "..."

    await update.message.reply_text(result, parse_mode="Markdown")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 OODA AI Office — Groq Turbo!")
    app.run_polling()


if __name__ == "__main__":
    main()
