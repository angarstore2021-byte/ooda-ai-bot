"""
OODA AI Office — Telegram Bot
================================
Deploy qilish uchun:
  1. pip install python-telegram-bot anthropic
  2. .env faylga tokenlarni qo'ying
  3. python ooda_telegram_bot.py

Kerakli o'zgaruvchilar:
  TELEGRAM_TOKEN  — BotFather dan olingan token
  ANTHROPIC_KEY   — console.anthropic.com dan API key
"""

import os
import asyncio
import logging
from anthropic import Anthropic
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_KEY",  "YOUR_ANTHROPIC_KEY")

client = Anthropic(api_key=ANTHROPIC_KEY)

AGENTS = {
    "rex":  {
        "emoji": "🧠", "name": "Rex",  "role": "Kuzat (Observe)",
        "sys":   (
            "Sen Rex — OODA tsiklining 'Kuzat' bosqichi strategisti. "
            "O'zbek tilida 2-3 gap, manga uslubida, energik javob ber. "
            "Muammoning asosiy jihatlarini kuzat."
        ),
    },
    "nova": {
        "emoji": "🔬", "name": "Nova", "role": "Tahlil (Orient)",
        "sys":   (
            "Sen Nova — OODA tsiklining 'Tahlil' bosqichi mutaxassisi. "
            "O'zbek tilida 2-3 gap, mantiqiy, manga uslubida tahlil qil."
        ),
    },
    "axel": {
        "emoji": "⚙️", "name": "Axel", "role": "Qaror (Decide)",
        "sys":   (
            "Sen Axel — OODA tsiklining 'Qaror' bosqichi ijrochisi. "
            "O'zbek tilida 2-3 gap, qat'iy, manga uslubida. "
            "Konkret harakat rejasi ber."
        ),
    },
    "lyra": {
        "emoji": "🎯", "name": "Lyra", "role": "Xulosa (Act)",
        "sys":   (
            "Sen Lyra — OODA tsiklining 'Harakat' bosqichi xulosachisi. "
            "O'zbek tilida 2-3 gap, ilhomlantiruvchi, manga uslubida. "
            "Barcha agentlar fikrlarini birlashtirib eng zo'r yakuniy yechim taklif qil."
        ),
    },
}


def ask_agent(agent_id: str, question: str) -> str:
    """Bitta agentga sinxron so'rov yuboradi."""
    a = AGENTS[agent_id]
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=a["sys"],
        messages=[{"role": "user", "content": question}],
    )
    return resp.content[0].text


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 *OODA AI Office — Manga Super AI*\n\n"
        "Men 4 ta AI agentdan iborat komandasiman:\n"
        "🧠 *Rex* — Kuzatuvchi\n"
        "🔬 *Nova* — Tahlilchi\n"
        "⚙️ *Axel* — Qaror qabul qiluvchi\n"
        "🎯 *Lyra* — Xulosa chiqaruvchi\n\n"
        "Savol yoki taklifingizni yuboring, komanda maslahat qilib yechim topadi!",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return

    # Foydalanuvchiga jarayon boshlanganligi haqida xabar
    status_msg = await update.message.reply_text(
        "⚡ OODA jarayoni boshlandi...\n"
        "🔍 Rex, Nova, Axel parallel tahlil qilmoqda..."
    )

    loop = asyncio.get_event_loop()

    # 1-3 bosqich: Rex, Nova, Axel — parallel
    rex_fut  = loop.run_in_executor(None, ask_agent, "rex",  question)
    nova_fut = loop.run_in_executor(None, ask_agent, "nova", question)
    axel_fut = loop.run_in_executor(None, ask_agent, "axel", question)

    rex_r, nova_r, axel_r = await asyncio.gather(rex_fut, nova_fut, axel_fut)

    await ctx.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
        text="🎯 Lyra yakuniy xulosani tayyorlamoqda...",
    )

    # 4-bosqich: Lyra — barcha natijalarni birlashtiradi
    lyra_context = (
        f"Savol: {question}\n\n"
        f"Rex: {rex_r}\n\nNova: {nova_r}\n\nAxel: {axel_r}"
    )
    lyra_r = await loop.run_in_executor(None, ask_agent, "lyra", lyra_context)

    # Eski status xabarni o'chir
    await ctx.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
    )

    # Natijalarni guruhlarga yubor
    result = (
        f"*📬 Savol:* {question}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🧠 *Rex* _(Kuzat)_\n{rex_r}\n\n"
        f"🔬 *Nova* _(Tahlil)_\n{nova_r}\n\n"
        f"⚙️ *Axel* _(Qaror)_\n{axel_r}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 *Lyra — Yakuniy Xulosa*\n{lyra_r}"
    )

    # Telegram 4096 belgidan uzun xabarni qabul qilmaydi
    if len(result) > 4000:
        result = result[:3997] + "..."

    await update.message.reply_text(result, parse_mode="Markdown")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 OODA AI Office bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
