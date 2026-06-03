import json
import re
import asyncio
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8879366892:AAGSozS7aaADKosbT0qS29CFK9GHUl4ydhM"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

user_urls = {}

def extract_video_id(url):
    m = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None

async def call_groq(prompt):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_URL,
            headers={"Authorization": "Bearer " + GROQ_API_KEY, "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 5000
            }
        )
        data = r.json()
        if not r.is_success:
            raise Exception(str(data.get("error", "Groq API error")))
        return data["choices"][0]["message"]["content"]

def make_prompt(url, vid, lang):
    if lang == "ru":
        lang_instruction = "Весь анализ строго на русском языке."
    elif lang == "en":
        lang_instruction = "All analysis strictly in English."
    else:
        lang_instruction = "Provide all text fields in both languages, format: 'RU: [russian] | EN: [english]'"

    return """You are a top YouTube marketing expert. Analyze this video:
URL: """ + url + """
Video ID: """ + vid + """

""" + lang_instruction + """

Return ONLY valid JSON without markdown:

{
  "niche": {
    "main_niche": "главная ниша (например: Образование, Финансы, Здоровье, Развлечения)",
    "sub_niche": "подниша (например: Личные финансы для молодёжи, Похудение без диет)",
    "niche_popularity": 8,
    "niche_competition": 7,
    "niche_money": 9,
    "niche_verdict": "краткий вывод — стоит ли заходить в эту нишу",
    "content_sources": [
      {"source": "название источника", "url": "ссылка или описание где искать", "type": "тип: YouTube / Reddit / Форум / Сайт / Телеграм"},
      {"source": "название", "url": "ссылка", "type": "тип"},
      {"source": "название", "url": "ссылка", "type": "тип"},
      {"source": "название", "url": "ссылка", "type": "тип"},
      {"source": "название", "url": "ссылка", "type": "тип"}
    ]
  },
  "score": {
    "overall_score": 75,
    "verdict": "verdict text",
    "metrics": [
      {"label": "Удержание аудитории", "value": 70},
      {"label": "Качество хука", "value": 80},
      {"label": "Вовлечённость", "value": 75},
      {"label": "SEO", "value": 65},
      {"label": "Монетизация", "value": 70}
    ],
    "recommendations": ["рек1","рек2","рек3","рек4","рек5"]
  },
  "title_analysis": {
    "original_title": "original video title",
    "clickbait_score": 7,
    "clickbait_verdict": "explanation",
    "what_works": "what works",
    "what_lacks": "what is missing",
    "improved_titles": ["title1","title2","title3"],
    "your_titles": ["your title1","your title2","your title3"]
  },
  "hooks": [
    {"type": "hook type", "timestamp": "0:00", "text": "description", "why": "why it works", "power": "HIGH"},
    {"type": "hook type", "timestamp": "0:15", "text": "description", "why": "explanation", "power": "MEDIUM"}
  ],
  "triggers": ["trigger1","trigger2","trigger3","trigger4"],
  "scenario": {
    "structure": [
      {"time": "0:00-0:30", "phase": "HOOK", "description": "description"},
      {"time": "0:30-2:00", "phase": "PROBLEM", "description": "description"},
      {"time": "2:00-8:00", "phase": "MAIN CONTENT", "description": "description"},
      {"time": "8:00-9:30", "phase": "SOLUTION", "description": "description"},
      {"time": "9:30-end", "phase": "CALL TO ACTION", "description": "description"}
    ],
    "full_script": "detailed scenario 3-5 paragraphs"
  },
  "breakdown": [
    {"timestamp": "0:00", "description": "scene", "technique": "technique", "impact": "HIGH"},
    {"timestamp": "0:20", "description": "scene", "technique": "technique", "impact": "HIGH"},
    {"timestamp": "1:00", "description": "scene", "technique": "technique", "impact": "MEDIUM"},
    {"timestamp": "3:00", "description": "scene", "technique": "technique", "impact": "MEDIUM"},
    {"timestamp": "6:00", "description": "scene", "technique": "technique", "impact": "HIGH"}
  ],
  "thumbnail": {
    "contrast_score": 7,
    "text_score": 8,
    "emotion_score": 7,
    "ctr_score": 7,
    "elements": ["element1","element2","element3"],
    "improvement_steps": ["step1","step2","step3","step4"]
  }
}

Replace all values with real analysis. Only JSON, no other words."""

def format_niche(d):
    n = d.get("niche", {})
    pop = n.get("niche_popularity", 0)
    comp = n.get("niche_competition", 0)
    money = n.get("niche_money", 0)

    def bar(v):
        return "█" * int(v) + "░" * (10 - int(v))

    sources = ""
    for s in n.get("content_sources", []):
        type_emoji = {"YouTube": "▶️", "Reddit": "🟠", "Форум": "💬", "Сайт": "🌐", "Телеграм": "✈️"}.get(s.get("type",""), "📌")
        sources += "\n" + type_emoji + " *" + s.get("source","") + "*\n  " + s.get("url","") + "\n"

    return ("🗺 *НИША И ПОДНИША*\n\n"
        "📂 *Ниша:* " + n.get("main_niche","") + "\n"
        "📁 *Подниша:* " + n.get("sub_niche","") + "\n\n"
        "📊 *Показатели ниши:*\n"
        "  🔥 Популярность: " + bar(pop) + " " + str(pop) + "/10\n"
        "  ⚔️ Конкуренция:  " + bar(comp) + " " + str(comp) + "/10\n"
        "  💰 Монетизация:  " + bar(money) + " " + str(money) + "/10\n\n"
        "💡 *Вывод:* " + n.get("niche_verdict","") + "\n\n"
        "🔍 *Где искать материал:*" + sources)

def format_score(d):
    s = d.get("score", {})
    score = s.get("overall_score", 0)
    emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
    metrics_text = ""
    for m in s.get("metrics", []):
        bar = "█" * (m["value"] // 10) + "░" * (10 - m["value"] // 10)
        metrics_text += "  " + m["label"] + ": " + bar + " " + str(m["value"]) + "\n"
    recs = "\n".join(["  " + str(i+1) + ". " + r for i, r in enumerate(s.get("recommendations", []))])
    return emoji + " *РЕЙТИНГ ВИДЕО*\n\n*Балл: " + str(score) + "/100*\n_" + s.get("verdict","") + "_\n\n📈 *Метрики:*\n" + metrics_text + "\n💡 *Рекомендации:*\n" + recs

def format_title(d):
    t = d.get("title_analysis", {})
    score = t.get("clickbait_score", 0)
    stars = "🔥" * int(score) + "▪️" * (10 - int(score))
    improved = "\n".join(["  " + str(i+1) + ". " + title for i, title in enumerate(t.get("improved_titles", []))])
    yours = "\n".join(["  " + str(i+1) + ". " + title for i, title in enumerate(t.get("your_titles", []))])
    return ("🎯 *АНАЛИЗ ЗАГОЛОВКА*\n\n"
        "📌 *Оригинал:*\n  _" + t.get("original_title","") + "_\n\n"
        "🔥 *Кликбейт: " + str(score) + "/10*\n  " + stars + "\n  " + t.get("clickbait_verdict","") + "\n\n"
        "✅ *Что работает:*\n  " + t.get("what_works","") + "\n\n"
        "❌ *Чего не хватает:*\n  " + t.get("what_lacks","") + "\n\n"
        "✨ *Улучшенные варианты:*\n" + improved + "\n\n"
        "🚀 *Твои заголовки:*\n" + yours)

def format_hooks(d):
    hooks = d.get("hooks", [])
    triggers = d.get("triggers", [])
    text = "⚡ *ХУКИ И ТРИГГЕРЫ*\n"
    for h in hooks:
        pwr = "🔥" if h.get("power") == "HIGH" else "⚡" if h.get("power") == "MEDIUM" else "💧"
        text += "\n" + pwr + " *" + h.get("type","") + "* | _" + h.get("timestamp","") + "_\n"
        text += "  " + h.get("text","") + "\n"
        text += "  📌 " + h.get("why","") + "\n"
    text += "\n🧠 *Триггеры:* " + " • ".join(triggers)
    return text

def format_scenario(d):
    sc = d.get("scenario", {})
    text = "📋 *СЦЕНАРИЙ ВИДЕО*\n"
    for s in sc.get("structure", []):
        text += "\n🔹 *" + s.get("phase","") + "* _" + s.get("time","") + "_\n  " + s.get("description","") + "\n"
    text += "\n📝 *Разбор:*\n" + sc.get("full_script","")
    return text

def format_breakdown(d):
    scenes = d.get("breakdown", [])
    text = "🎬 *РАСКАДРОВКА*\n\n"
    for i, sc in enumerate(scenes):
        imp = sc.get("impact","")
        e = "🔴" if imp == "HIGH" else "🟡" if imp == "MEDIUM" else "⚪"
        text += e + " *" + str(i+1) + " | " + sc.get("timestamp","") + "*\n"
        text += "  " + sc.get("description","") + "\n"
        text += "  _" + sc.get("technique","") + "_\n\n"
    return text

def format_thumbnail(d):
    th = d.get("thumbnail", {})
    def stars(n):
        return "⭐" * int(n) + "☆" * (10 - int(n))
    elems = "\n".join(["  ✅ " + e for e in th.get("elements",[])])
    steps = "\n".join(["  " + str(i+1) + ". " + s for i, s in enumerate(th.get("improvement_steps",[]))])
    return ("🖼 *АНАЛИЗ ПРЕВЬЮ*\n\n"
        "🎨 Контраст: " + stars(th.get("contrast_score",0)) + " " + str(th.get("contrast_score",0)) + "/10\n"
        "✍️ Текст: " + stars(th.get("text_score",0)) + " " + str(th.get("text_score",0)) + "/10\n"
        "😮 Эмоция: " + stars(th.get("emotion_score",0)) + " " + str(th.get("emotion_score",0)) + "/10\n"
        "👆 CTR: " + stars(th.get("ctr_score",0)) + " " + str(th.get("ctr_score",0)) + "/10\n\n"
        "📦 *Элементы:*\n" + elems + "\n\n"
        "🚀 *Как улучшить:*\n" + steps)

async def run_analysis(reply_func, url, lang):
    vid = extract_video_id(url)
    msg = await reply_func("⏳ Анализирую... подожди 30-40 секунд")
    try:
        prompt = make_prompt(url, vid, lang)
        raw = await call_groq(prompt)
        raw = raw.replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        await msg.edit_text("✅ Готово! Отправляю результаты...")
        try:
            await reply_func.__self__.reply_photo(
                photo="https://img.youtube.com/vi/" + vid + "/mqdefault.jpg",
                caption="🎯 " + url
            )
        except:
            pass
        sections = [
            format_niche(data),
            format_score(data),
            format_title(data),
            format_hooks(data),
            format_scenario(data),
            format_breakdown(data),
            format_thumbnail(data)
        ]
        for section in sections:
            try:
                await reply_func(section, parse_mode="Markdown")
            except:
                clean = re.sub(r'[*_`]', '', section)
                await reply_func(clean)
            await asyncio.sleep(0.5)
        await msg.delete()
    except json.JSONDecodeError:
        await msg.edit_text("❌ Ошибка ответа ИИ. Попробуй ещё раз.")
    except Exception as e:
        await msg.edit_text("❌ Ошибка: " + str(e))

async def start(update, context):
    await update.message.reply_text(
        "👋 Привет! Отправь ссылку на YouTube видео конкурента.\n\n"
        "Я проанализирую:\n"
        "🗺 Нишу и поднишу + где искать материал\n"
        "📊 Рейтинг и оценку\n"
        "🎯 Заголовок + готовые заголовки для тебя\n"
        "⚡ Хуки и триггеры\n"
        "📋 Сценарий\n"
        "🎬 Раскадровку\n"
        "🖼 Превью\n\n"
        "Отправляй ссылку! 👇"
    )

async def handle_message(update, context):
    text = update.message.text.strip()
    vid = extract_video_id(text)
    if not vid:
        await update.message.reply_text("❌ Отправь ссылку на YouTube\nПример: https://youtube.com/watch?v=...")
        return
    user_urls[update.effective_user.id] = text
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ],
        [InlineKeyboardButton("🇷🇺🇺🇸 Оба языка", callback_data="lang_both")]
    ]
    await update.message.reply_text("🌍 На каком языке сделать анализ?", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_lang(update, context):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    url = user_urls.get(query.from_user.id)
    if not url:
        await query.message.reply_text("❌ Отправь ссылку заново.")
        return
    await query.message.delete()
    await run_analysis(query.message.reply_text, url, lang)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_lang, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
