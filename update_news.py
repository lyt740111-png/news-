import feedparser
import json
import os
import time
import google.generativeai as genai
from newspaper import Article
from datetime import datetime

# إعداد الذكاء الاصطناعي
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ خطأ: مفتاح GEMINI_API_KEY غير موجود في Secrets!")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

# روابط RSS متنوعة وموثوقة جداً
RSS_FEEDS =[
    "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
    "https://arabic.cnn.com/api/v1/rss/world/rss.xml",
    "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9",
    "https://rss.rtarabic.com/news/"
]

def get_detailed_article(title, text, summary):
    try:
        prompt = f"أعد صياغة هذا الخبر بشكل مقال طويل ومفصل بالعربية: العنوان: {title}\nالنص: {text[:2000]}\nأجب بصيغة JSON فقط: {{\"seo_title\": \"...\", \"content\": \"...\", \"category\": \"...\"}}"
        response = model.generate_content(prompt)
        # محاولة استخراج JSON من رد الذكاء الاصطناعي
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        return json.loads(raw_text)
    except Exception as e:
        print(f"⚠️ فشل الذكاء الاصطناعي: {e}")
        return None

# جلب البيانات القديمة
existing_news = []
if os.path.exists('news.json'):
    try:
        with open('news.json', 'r', encoding='utf-8') as f:
            existing_news = json.load(f)
    except:
        existing_news = []

existing_links = {item['link'] for item in existing_news}
new_articles = []

for url in RSS_FEEDS:
    print(f"🌐 فحص المصدر: {url}")
    feed = feedparser.parse(url)
    print(f"🔎 وجدنا {len(feed.entries)} خبر في هذا المصدر")
    
    for entry in feed.entries:
        if len(new_articles) >= 50: break
        if entry.link in existing_links: continue
        
        try:
            print(f"📝 جاري معالجة: {entry.title[:50]}...")
            article = Article(entry.link)
            article.download()
            article.parse()
            
            ai_data = get_detailed_article(entry.title, article.text, entry.summary if 'summary' in entry else "")
            
            # نظام الطوارئ: إذا فشل AI، استخدم البيانات الأصلية
            if ai_data:
                item = {
                    "id": str(hash(entry.link)),
                    "title": ai_data.get('seo_title', entry.title),
                    "link": entry.link,
                    "image": article.top_image if article.top_image else "https://via.placeholder.com/800",
                    "category": ai_data.get('category', "أخبار عامة"),
                    "body": ai_data.get('content', article.text[:1000]),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            else:
                # إضافة الخبر حتى لو فشل الـ AI لكي لا يظهر الموقع فارغاً
                item = {
                    "id": str(hash(entry.link)),
                    "title": entry.title,
                    "link": entry.link,
                    "image": article.top_image if article.top_image else "https://via.placeholder.com/800",
                    "category": "أخبار عاجلة",
                    "body": article.text[:1000] if article.text else entry.get('summary', 'لا يوجد تفاصيل'),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            
            new_articles.append(item)
            time.sleep(2) # استراحة بسيطة
        except Exception as e:
            print(f"❌ خطأ في معالجة خبر: {e}")

# حفظ النتائج
final_data = new_articles + existing_news
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_data[:200], f, ensure_ascii=False, indent=4)
print(f"✅ تم الانتهاء! إجمالي الأخبار في الملف: {len(final_data[:200])}")
