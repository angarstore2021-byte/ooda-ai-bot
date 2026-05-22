"""
OODA AI Office — Full Professional Bot
llama-3.3-70b-versatile + Grafik + Rasm tahlili
"""

import os
import io
import re
import asyncio
import logging
import base64
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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

Foydalanuvchi savol beradi. Sen FAQAT quyidagi formatda javob berasan, boshqa hech narsa yozma:

🧠 *Rex (Kuzat):*
[1-2 gap, savolga oid]

🔬 *Nova (Tahlil):*
[1-2 gap, savolga oid]

⚙️ *Axel (Qaror):*
[1-2 gap, aniq harakat]

🎯 *Lyra (Xulosa):*
[2-3 gap, eng yaxshi yechim]

💡 *Foydali havolalar:*
[2-3 ta real veb-sayt URL]

MUHIM QOIDALAR:
- Har doim O'zbek tilida yoz
- Har agent faqat 1-2 gap
- Faqat yuqoridagi format, hech qanday qo'shimcha matn yo'q
- Savolga to'g'ridan-to'g'ri javob ber"""

IMAGE_PROMPT = """Sen OODA AI Office — rasmlarni professional tahlil qiluvchi AI.
Rasmni ko'rib FAQAT quyidagi formatda javob ber:

🔍 *Rasm tahlili:*
[Rasmda nima ko'rinayotgani - 2-3 gap]

🧠 *Rex (Kuzat):* [1-2 gap]
🔬 *Nova (Tahlil):* [1-2 gap]
⚙️ *Axel (Qaror):* [1-2 gap]
🎯 *Lyra (Xulosa):* [2-3 gap]

QOIDALAR: O'zbek tilida, qisqa, faqat shu format."""

CHART_DETECT_PROMPT = """Foydalanuvchi xabarida grafik chizish uchun raqamli ma'lumot bormi?

Agar bor bo'lsa:
{"draw": true, "title": "Grafik nomi", "labels": ["Jan","Feb"], "values": [100, 200], "chart_type": "bar"}

Agar yo'q bo'lsa:
{"draw": false}

Faqat JSON qaytар, boshqa hech narsa yozma."""

CHART_AUTO_PROMPT = """Bu tahlil matnidan grafik chizish mumkinmi? Agar aniq raqamlar bo'lsa:
{"draw": true, "title": "...", "labels": [...], "values": [...], "chart_type": "bar|line|pie"}

Agar mumkin bo'lmasa:
{"draw": false}

Faqat JSON, boshqa hech narsa."""


def ask_text(question: str) -> str:
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": TEXT_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=700,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()


def ask_image(image_bytes: bytes, caption: str = "") -> str:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    user_text = caption if caption else "Ushbu rasmni tahlil qil."
    resp = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": IMAGE_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                {"type": "text", "text": user_text},
            ]},
        ],
        max_tokens=600,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()


def detect_chart(text: str) -> dict:
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": CHART_DETECT_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=200,
        temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    try:
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except:
        return {"draw": False}


def auto_chart(analysis: str) -> dict:
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": CHART_AUTO_PROMPT},
            {"role": "user", "content": analysis},
        ],
        max_tokens=200,
        temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    try:
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except:
        return {"draw": False}


def draw_chart(title: str, labels: list, values: list, chart_type: str = "bar") -> bytes:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#7F77DD", "#1D9E75", "#EF9F27", "#D4537E", "#378ADD", "#639922", "#E24B4A"]

    if chart_type == "pie":
        ax.pie(values, labels=labels, colors=colors[:len(values)],
               autopct="%1.1f%%", startangle=140,
               textprops={"color": "white", "fontsize": 11})
    elif chart_type == "line":
        ax.plot(labels, values, color="#7F77DD", linewidth=2.5,
                marker="o", markersize=7, markerfacecolor="#EF9F27")
        ax.fill_between(range(len(labels)), values, alpha=0.15, color="#7F77DD")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.grid(axis="y", alpha=0.3)
    else:
        bars = ax.bar(labels, values, color=colors[:len(values)], width=0.6, edgecolor="none")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.01,
                    f"{val:,.0f}", ha="center", va="bottom", color="white", fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.grid(axis="y", alpha=0.3)

    ax.set_title(title, fontsize=14, color="white", pad=15, fontweight="bold")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 *OODA AI Office* — Professional AI\n\n"
        "🧠 Rex · 🔬 Nova · ⚙️ Axel · 🎯 Lyra\n\n"
        "📝 *Matn* → maslahat + havolalar\n"
        "🖼 *Rasm* → AI tahlil\n"
        "📊 *Raqamli ma'lumot* → avtomatik grafik\n\n"
        "_Misol: yanvar 500, fevral 800, mart 650_\n\n"
        "/help — yordam",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Yordam*\n\n"
        "*📝 Matn:*\n"
        "• Biznes strategiyasi\n"
        "• Marketing tavsiyalari\n"
        "• Har qanday savol\n\n"
        "*🖼 Rasm:*\n"
        "• Grafik, jadval, sxema rasmi\n"
        "• Mahsulot yoki dizayn rasmi\n"
        "• Skrinshot tahlili\n\n"
        "*📊 Grafik:*\n"
        "• _Yanvar 100, Fevral 200_ → bar chart\n"
        "• _Sotuv: 50, 80, 120_ → line chart\n"
        "• Tahlil natijasida ham avtomatik chizadi",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return

    status_msg = await update.message.reply_text("⚡ Tahlil qilinmoqda...")
    loop = asyncio.get_event_loop()

    try:
        chart_info = await loop.run_in_executor(None, detect_chart, question)

        if chart_info.get("draw") and chart_info.get("values"):
            chart_bytes = await loop.run_in_executor(
                None, draw_chart,
                chart_info.get("title", "Grafik"),
                chart_info.get("labels", []),
                chart_info.get("values", []),
                chart_info.get("chart_type", "bar"),
            )
            await ctx.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
            )
            await update.message.reply_photo(
                photo=chart_bytes,
                caption=f"📊 *{chart_info.get('title', 'Grafik')}*",
                parse_mode="Markdown",
            )
            return

        answer = await loop.run_in_executor(None, ask_text, question)
        auto = await loop.run_in_executor(None, auto_chart, answer)

        await ctx.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
        )

        full = f"❓ *{question}*\n━━━━━━━━━━━━━━━\n{answer}"
        if len(full) > 4000:
            full = full[:3997] + "..."

        await update.message.reply_text(full, parse_mode="Markdown")

        if auto.get("draw") and auto.get("values"):
            chart_bytes = await loop.run_in_executor(
                None, draw_chart,
                auto.get("title", "Tahlil grafigi"),
                auto.get("labels", []),
                auto.get("values", []),
                auto.get("chart_type", "bar"),
            )
            await update.message.reply_photo(
                photo=chart_bytes,
                caption="📊 *Tahlil grafigi*",
                parse_mode="Markdown",
            )

    except Exception as e:
        await ctx.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="❌ Xatolik. Qaytadan urinib ko'ring.",
        )
        logging.error(f"Xato: {e}")


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
            text="❌ Rasmni tahlil qilib bo'lmadi.",
        )
        logging.error(f"Rasm xato: {e}")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 OODA AI Office — Full Professional!")
    app.run_polling()


if __name__ == "__main__":
    main()
