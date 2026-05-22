"""
OODA AI Office — Telegram Bot (Google Gemini)
===============================================
O'rnatish:
  pip install python-telegram-bot google-generativeai

Railway Variables:
  TELEGRAM_TOKEN  — @BotFather dan
  GEMINI_KEY      — aistudio.google.com dan
"""

import os
import asyncio
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GEMINI_KEY     = os.getenv("GEMINI_KEY", "")

genai.configure(api_key=GEMINI_KEY)

AGENTS = {
    "rex": {
        "emoji": "🧠", "name": "Rex", "role": "Kuzat",
        "sys": (
            "Sen Rex — OODA tsiklining 'Kuzat' bosqichi strategisti. "
            "O'zbek tilida 2-3 gap, manga uslubida, energik javob ber. "
            "Muammoning asosiy jihatlarini kuzat."
        ),
    },
    "nova": {
        "emoji": "🔬", "name": "Nova", "role": "Tahlil",
        "sys": (
            "Sen Nova — OODA tsiklining 'Tahlil' bosqichi mutaxassisi. "
            "O'zbek tilida 2-3 gap, mantiqiy, manga uslubida tahlil qil."
        ),
    },
    "axel": {
        "emoji": "⚙️", "name": "Axel", "role": "Qaror",
        "sys": (
            "Sen Axel — OODA tsiklining 'Qaror' bosqichi ijrochisi. "
            "O'zbek tilida 2-3 gap, qat'iy, manga uslubida. "
            "Konkret harakat rejasi ber."
        ),
    },
    "lyra": {
        "emoji": "🎯", "name": "Lyra", "role": "Xulosa",
        "sys": (
            "Sen Lyra — OODA tsiklining 'Harakat' bosqichi xulosachisi. "
            "O'zbek tilida 2-3 gap, ilhomlantiruvchi, manga uslubida. "
            "Barcha agentlar fikrlarini birlashtirib eng zo'r yakuniy yechim taklif qil."
        ),
    },
}


def ask_agent(agent_id: str, question: str) -> str:
    a = AGENTS[agent_id]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=a["sys"]
    )
    resp = model.generate_content(question)
    return resp.text


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 *OODA AI Office — Manga Super AI*\n\n"
        "4 ta AI agentdan iborat komandasiman:\n"
        "🧠 *Rex* — Kuzatuvchi\n"
        "🔬 *Nova* — Tahlilchi\n"
        "⚙️ *Axel* — Qaror qabul qiluvchi\n"
        "🎯 *Lyra* — Xulosa chiqaruvchi\n\n"
        "Savol yoki taklifingizni yuboring!",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return

    status_msg = await update.message.reply_text(
        "⚡ OODA jarayoni boshlandi...\n"
        "🔍 Rex, Nova, Axel parallel tahlil qilmoqda..."
    )

    loop = asyncio.get_event_loop()

    rex_r, nova_r, axel_r = await asyncio.gather(
        loop.run_in_executor(None, ask_agent, "rex",  question),
        loop.run_in_executor(None, ask_agent, "nova", question),
        loop.run_in_executor(None, ask_agent, "axel", question),
    )

    await ctx.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
        text="🎯 Lyra yakuniy xulosani tayyorlamoqda...",
    )

    lyra_r = await loop.run_in_executor(
        None, ask_agent, "lyra",
        f"Savol: {question}\n\nRex: {rex_r}\n\nNova: {nova_r}\n\nAxel: {axel_r}"
    )

    await ctx.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
    )

    result = (
        f"📬 *Savol:* {question}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🧠 *Rex* _(Kuzat)_\n{rex_r}\n\n"
        f"🔬 *Nova* _(Tahlil)_\n{nova_r}\n\n"
        f"⚙️ *Axel* _(Qaror)_\n{axel_r}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 *Lyra — Yakuniy Xulosa*\n{lyra_r}"
    )

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
