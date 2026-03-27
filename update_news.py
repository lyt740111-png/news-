import feedparser
import json
import os
import time
import google.generativeai as genai
from newspaper import Article
from datetime import datetime

# إعداد الذكاء الاصطناعي
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

RSS_FEEDS = [
    "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
    "https://arabic.cnn.com/api/v1/rss/world/rss.xml",
    "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9"
]

def ai_process(title, text):
    try:
        prompt = f"أعد صياغة الخبر التالي بشكل مقال صحفي مفصل بالعربية: العنوان: {title}\nالنص: {text[:1500]}\nأجب بصيغة JSON فقط: {{\"title\": \"...\", \"content\": \"...\", \"category\": \"...\", \"importance\": 1-10}}"
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        if "```json" in res_text: res_text = res_text.split("```json")[1].split("```")[0]
        return json.loads(res_text)
    except: return None

# جلب الأرشيف
archive = []
if os.path.exists('news.json'):
    with open('news.json', 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            archive = data if isinstance(data, list) else []
        except: archive = []

existing_links = {item['link'] for item in archive}
new_entries = []

for url in RSS_FEEDS:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        if len(new_entries) >= 50: break
        if entry.link in existing_links: continue
        try:
            art = Article(entry.link)
            art.download(); art.parse()
            data = ai_process(entry.title, art.text)
            item = {
                "id": str(int(time.time() * 1000)),
                "title": data['title'] if data else entry.title,
                "link": entry.link,
                "image": art.top_image if art.top_image else "https://via.placeholder.com/800x450",
                "category": data['category'] if data else "عام",
                "body": data['content'] if data else art.text[:1000],
                "importance": data['importance'] if data else 5,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "timestamp": int(time.time())
            }
            new_entries.append(item)
            time.sleep(2)
        except: continue

# حفظ الكل (الجديد في البداية)
final_archive = new_entries + archive
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_archive, f, ensure_ascii=False, indent=4)
print(f"✅ تم حفظ {len(new_entries)} خبر جديد. الإجمالي: {len(final_archive)}")
