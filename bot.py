import json
import re
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8879366892:AAGSozS7aaADKosbT0qS29CFK9GHUl4ydhM"
GEMINI_API_KEY = "AQ.Ab8RN6IuNCMtVWDoYw1VHYp1HrWiyRVpOuc3yGsoLg9atfpFGg"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY

def extract_video_id(url):
    m = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None

async def call_gemini(prompt):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GEMINI_URL, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4000}
        })
        data = r.json()
        if not r.is_success:
            raise Exception(data.get("error", {}).get("message", "Gemini API error"))
        return data["candidates"][0]["content"]["parts"][0]["text"]

def make_prompt(url, vid):
    return """Ты эксперт по YouTube маркетингу. Проанализируй видео:
URL: """ + url + """
Video ID: """ + vid + """

Верни ТОЛЬКО валидный JSON без markdown:

{
  "score": {
    "overall_score": 75,
    "verdict": "Хорошее видео с сильным хуком",
    "metrics": [
      {"label": "Удержание аудитории", "value": 70},
      {"label": "Качество хука", "value": 80},
      {"label": "Вовлечённость", "value": 75},
      {"label": "SEO оптимизация", "value": 65},
      {"label": "Монетизация", "value": 70}
    ],
    "recommendations": ["рек1","рек2","рек3","рек4","рек5"]
  },
  "hooks": [
    {"type": "Вопрос", "timestamp": "0:00", "text": "описание хука", "why": "почему работает", "power": "HIGH"},
    {"type": "Шок", "timestamp": "0:15", "text": "описание", "why": "объяснение", "power": "MEDIUM"}
  ],
  "triggers": ["Страх упустить", "Любопытство", "Жадность", "Срочность"],
  "scenario": {
    "structure": [
      {"time": "0:00-0:30", "phase": "КРЮЧОК", "description": "описание"},
      {"time": "0:30-2:00", "phase": "ПРОБЛЕМА", "description": "описание"},
      {"time": "2:00-8:00", "phase": "ОСНОВНОЙ КОНТЕНТ", "description": "описание"},
      {"time": "8:00-9:30", "phase": "РЕШЕНИЕ", "description": "описание"},
      {"time": "9:30-конец", "phase": "ПРИЗЫВ К ДЕЙСТВИЮ", "description": "описание"}
    ],
    "full_script": "подробное описание сценария 3-5 абзацев"
  },
  "breakdown": [
    {"timestamp": "0:00", "description": "сцена", "technique": "техника", "impact": "HIGH"},
    {"timestamp": "0:20", "description": "сцена", "technique": "техника", "impact": "HIGH"},
    {"timestamp": "1:00", "description": "сцена", "technique": "техника", "impact": "MEDIUM"},
    {"timestamp": "3:00", "description": "сцена", "technique": "техника", "impact": "MEDIUM"},
    {"timestamp": "6:00", "description": "сцена", "technique": "техника", "impact": "HIGH"}
  ],
  "thumbnail": {
    "contrast_score": 7,
    "text_score": 8,
    "emotion_score": 7,
    "ctr_score": 7,
    "elements": ["элемент1", "элемент2", "элемент3"],
    "improvement_steps": ["шаг1", "шаг2", "шаг3", "шаг4"]
  }
}

Замени все значения реальным анализом. Отвечай на русском. Только JSON."""

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

def format_hooks(d):
    hooks = d.get("hooks", [])
    triggers = d.get("triggers", [])
    text = "⚡ *ХУКИ И ТРИГГЕРЫ*\n"
    for h in hooks:
        pwr = "🔥" if h.get("power") == "HIGH" else "⚡" if h.get("power") == "MEDIUM" else "💧"
        text += "\n" + pwr + " *" + h.get("type","") + "* | _" + h.get("timestamp","") + "_\n"
        text += "  \"" + h.get("text","") + "\"\n"
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
        text += e + " *#" + str(i+1) + " | " + sc.get("timestamp","") + "*\n"
        text += "  " + sc.get("description","") + "\n"
        text += "  _" + sc.get("technique","") + "_\n\n"
    return text

def format_thumbnail(d):
    th = d.get("thumbnail", {})
    def stars(n):
        return "⭐" * int(n) + "☆" * (10 - int(n))
    elems = "\n".join(["  ✅ " + e for e in th.get("elements",[])])
    steps = "\n".join(["  " + str(i+1) + ". " + s for i, s in enumerate(th.get("improvement_steps",[]))])
    return "🖼 *АНАЛИЗ ПРЕВЬЮ*\n\n🎨 Контраст: " + stars(th.get("contrast_score",0)) + " " + str(th.get("contrast_score",0)) + "/10\n✍️ Текст: " + stars(th.get("text_score",0)) + " " + str(th.get("text_score",0)) + "/10\n😮 Эмоция: " + stars(th.get("emotion_score",0)) + " " + str(th.get("emotion_score",0)) + "/10\n👆 CTR: " + stars(th.get("ctr_score",0)) + " " + str(th.get("ctr_score",0)) + "/10\n\n📦 *Элементы:*\n" + elems + "\n\n🚀 *Как улучшить:*\n" + steps

async def start(update, context):
    await update.message.reply_text(
        "👋 Привет! Отправь ссылку на YouTube видео конкурента.\n\n"
        "Я проанализирую:\n"
        "📊 Рейтинг и оценку\n"
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
    msg = await update.message.reply_text("⏳ Анализирую... подожди 20-30 секунд")
    try:
        prompt = make_prompt(text, vid)
        raw = await call_gemini(prompt)
        raw = raw.replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        await msg.edit_text("✅ Готово! Отправляю результаты...")
        try:
            await update.message.reply_photo(
                photo="https://img.youtube.com/vi/" + vid + "/mqdefault.jpg",
                caption="🎯 Анализ: " + text
            )
        except:
            pass
        sections = [format_score(data), format_hooks(data), format_scenario(data), format_breakdown(data), format_thumbnail(data)]
        for section in sections:
            try:
                await update.message.reply_text(section, parse_mode="Markdown")
            except:
                clean = re.sub(r'[*_`]', '', section)
                await update.message.reply_text(clean)
            await asyncio.sleep(0.5)
        await msg.delete()
    except json.JSONDecodeError:
        await msg.edit_text("❌ Ошибка ответа ИИ. Попробуй ещё раз.")
    except Exception as e:
        await msg.edit_text("❌ Ошибка: " + str(e))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
