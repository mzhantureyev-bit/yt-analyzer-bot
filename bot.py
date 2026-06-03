import os
import json
import re
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
TELEGRAM_TOKEN = "8879366892:AAGSozS7aaADKosbT0qS29CFK9GHUl4ydhM"
GEMINI_API_KEY = "AQ.Ab8RN6IuNCMtVWDoYw1VHYp1HrWiyRVpOuc3yGsoLg9atfpFGg"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generdef extract_video_id(url: str):
 m = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{1 return m.group(1) if m else None
async def call_gemini(prompt: str) -> str:
 async with httpx.AsyncClient(timeout=60) as client:
 r = await client.post(GEMINI_URL, json={
 "contents": [{"parts": [{"text": prompt}]}],
 "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4000}
 })
 data = r.json()
 if not r.is_success:
 raise Exception(data.get("error", {}).get("message", "Ошибка Gemini API"))
 return data["candidates"][0]["content"]["parts"][0]["text"]
def make_prompt(url: str, vid: str) -> str:
 return f"""Ты — топовый эксперт по YouTube маркетингу и вирусному контенту.
Проанализируй YouTube видео:
URL: {url}
Video ID: {vid}
Верни ТОЛЬКО валидный JSON без markdown, только JSON объект:
{{
 "score": {{
 "overall_score": <0-100>,
 "verdict": "<вердикт одним предложением>",
 "metrics": [
 {{"label": "Удержание аудитории", "value": <0-100>}},
 {{"label": "Качество хука", "value": <0-100>}},
 {{"label": "Вовлечённость", "value": <0-100>}},
 {{"label": "SEO оптимизация", "value": <0-100>}},
 {{"label": "Монетизация", "value": <0-100>}}
 ],
 "recommendations": ["<рек1>","<рек2>","<рек3>","<рек4>","<рек5>"]
 }},
 "hooks": [
 {{"type": "<тип хука>", "timestamp": "<время>", "text": "<описание>", "why": "<почему раб {{"type": "<тип>", "timestamp": "<время>", "text": "<описание>", "why": "<объяснение>", " {{"type": "<тип>", "timestamp": "<время>", "text": "<описание>", "why": "<объяснение>", " ],
 "triggers": ["Страх упустить", "Любопытство", "Жадность", "Социальное доказательство", "Сро "scenario": {{
 "structure": [
 {{"time": "0:00–0:30", "phase": "КРЮЧОК", "description": "<описание>"}},
 {{"time": "0:30–2:00", "phase": "ПРОБЛЕМА", "description": "<описание>"}},
 {{"time": "2:00–8:00", "phase": "ОСНОВНОЙ КОНТЕНТ", "description": "<описание>"}},
 {{"time": "8:00–9:30", "phase": "РЕШЕНИЕ", "description": "<описание>"}},
 {{"time": "9:30–конец", "phase": "ПРИЗЫВ К ДЕЙСТВИЮ", "description": "<описание>"}}
 ],
 "full_script": "<подробное описание сценария 3-5 абзацев>"
 }},
 "breakdown": [
 {{"timestamp": "0:00", "description": "<сцена>", "technique": "<техника>", "impact": "HIG {{"timestamp": "0:20", "description": "<сцена>", "technique": "<техника>", "impact": "HIG {{"timestamp": "1:00", "description": "<сцена>", "technique": "<техника>", "impact": "MED {{"timestamp": "3:00", "description": "<сцена>", "technique": "<техника>", "impact": "MED {{"timestamp": "6:00", "description": "<сцена>", "technique": "<техника>", "impact": "HIG {{"timestamp": "9:00", "description": "<сцена>", "technique": "<техника>", "impact": "HIG ],
 "thumbnail": {{
 "contrast_score": <1-10>,
 "text_score": <1-10>,
 "emotion_score": <1-10>,
 "ctr_score": <1-10>,
 "elements": ["<элемент1>","<элемент2>","<элемент3>"],
 "improvement_steps": ["<шаг1>","<шаг2>","<шаг3>","<шаг4>"]
 }}
}}
Отвечай на русском. Только JSON, никаких других слов."""
def format_score(d: dict) -> str:
 s = d.get("score", {})
 score = s.get("overall_score", 0)
 emoji = " " if score >= 80 else " " if score >= 60 else " "

 metrics_text = ""
 for m in s.get("metrics", []):
 bar = "█" * (m["value"] // 10) + "░" * (10 - m["value"] // 10)
 metrics_text += f" {m['label']}: {bar} {m['value']}\n"

 recs = "\n".join([f" {i+1}. {r}" for i, r in enumerate(s.get("recommendations", []))])

 return f""" *РЕЙТИНГ ВИДЕО*
{emoji} *Общий балл: {score}/100*
_{s.get('verdict', '')}_
 *Метрики:*
{metrics_text}
 *Топ рекомендации:*
{recs}"""
def format_hooks(d: dict) -> str:
 hooks = d.get("hooks", [])
 triggers = d.get("triggers", [])

 hooks_text = ""
 for h in hooks:
 pwr_emoji = " " if h.get("power") == "HIGH" else " " if h.get("power") == "MEDIUM"  hooks_text += f"\n{pwr_emoji} *{h.get('type', '')}* | _{h.get('timestamp', '')}_\n"
 hooks_text += f" \"{h.get('text', '')}\"\n"
 hooks_text += f" {h.get('why', '')}\n"

 trg_text = " • ".join(triggers)

 return f""" *ХУКИ И ТРИГГЕРЫ*
{hooks_text}
 *Психологические триггеры:*
{trg_text}"""
def format_scenario(d: dict) -> str:
 sc = d.get("scenario", {})
 struct = sc.get("structure", [])

 struct_text = ""
 for s in struct:
 struct_text += f"\n *{s.get('phase', '')}* _{s.get('time', '')}_\n {s.get('descrip
 script = sc.get("full_script", "")

 return f""" *СЦЕНАРИЙ ВИДЕО*
{struct_text}
 *Полный разбор:*
{script}"""
def format_breakdown(d: dict) -> str:
 scenes = d.get("breakdown", [])

 text = " *РАСКАДРОВКА*\n\n"
 for i, sc in enumerate(scenes):
 imp = sc.get("impact", "")
 imp_emoji = " " if imp == "HIGH" else " " if imp == "MEDIUM" else " "
 text += f"{imp_emoji} *#{i+1} | {sc.get('timestamp', '')}*\n"
 text += f" {sc.get('description', '')}\n"
 text += f" _Техника: {sc.get('technique', '')}_\n\n"

 return text
def format_thumbnail(d: dict) -> str:
 th = d.get("thumbnail", {})

 def stars(n):
 return " " * n + "☆" * (10 - n)

 elems = "\n".join([f" {e}" for e in th.get("elements", [])])
 steps = "\n".join([f" {i+1}. {s}" for i, s in enumerate(th.get("improvement_steps", []))
 return f""" *АНАЛИЗ ПРЕВЬЮ*
Контраст: {stars(th.get('contrast_score', 0))} {th.get('contrast_score', 0)}/10
Текст: {stars(th.get('text_score', 0))} {th.get('text_score', 0)}/10
Эмоция: {stars(th.get('emotion_score', 0))} {th.get('emotion_score', 0)}/10
 CTR прогноз: {stars(th.get('ctr_score', 0))} {th.get('ctr_score', 0)}/10
 *Элементы превью:*
{elems}
 *Как сделать лучше:*
{steps}"""
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
 await update.message.reply_text(
 " Привет! Я анализирую видео конкурентов на YouTube.\n\n"
 " Просто отправь мне ссылку на YouTube видео — и я выдам:\n\n"
 " Рейтинг и оценку\n"
 " Хуки и триггеры\n"
 " Сценарий и структуру\n"
 " Полную раскадровку\n"
 " Анализ превью\n\n"
 "Отправляй ссылку! "
 )
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
 text = update.message.text.strip()
 vid = extract_video_id(text)

 if not vid:
 await update.message.reply_text(
 " Не вижу ссылку на YouTube.\n\n"
 "Отправь в таком формате:\n"
 "https://www.youtube.com/watch?v=..."
 )
 return

 msg = await update.message.reply_text(" Анализирую видео... Подожди 20-30 секунд")

 try:
 prompt = make_prompt(text, vid)
 raw = await call_gemini(prompt)
 raw = raw.replace("```json", "").replace("```", "").strip()
 data = json.loads(raw)

 await msg.edit_text(" Готово! Отправляю результаты...")

 # Send thumbnail
 thumb_url = f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
 try:
 await update.message.reply_photo(
 photo=thumb_url,
 caption=f" Анализ видео:\n{text}"
 )
 except:
 pass

 # Send all sections
 sections = [
 format_score(data),
 format_hooks(data),
 format_scenario(data),
 format_breakdown(data),
 format_thumbnail(data),
 ]

 for section in sections:
 try:
 await update.message.reply_text(section, parse_mode="Markdown")
 await asyncio.sleep(0.5)
 except Exception as e:
 # If markdown fails, send plain
 clean = re.sub(r'[*_`]', '', section)
 await update.message.reply_text(clean)
 await asyncio.sleep(0.5)

 await msg.delete()

 except json.JSONDecodeError:
 await msg.edit_text(" ИИ вернул некорректный ответ. Попробуй ещё раз.")
 except Exception as e:
 await msg.edit_text(f" Ошибка: {str(e)}")
def main():
 app = Application.builder().token(TELEGRAM_TOKEN).build()
 app.add_handler(CommandHandler("start", start))
 app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
 print(" Бот запущен!")
 app.run_polling()
if __name__ == "__main__":
 main()
