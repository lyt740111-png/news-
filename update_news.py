import feedparser
import json
import os
import google.generativeai as genai
from datetime import datetime

# إعداد مفتاح الذكاء الاصطناعي (Gemini Free API)
# سنضعه في إعدادات GitHub Secrets للأمان
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# روابط RSS للمواقع الموثوقة (يمكنك إضافة المزيد)
RSS_FEEDS =[
    "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9", # الجزيرة سياسة
    "https://arabic.cnn.com/api/v1/rss/tech/rss.xml" # CNN تقنية
]

news_data =[]

def process_news_with_ai(title, summary):
    try:
        # نطلب من الذكاء الاصطناعي تصنيف الخبر وتقييم أهميته
        prompt = f"""
        اقرأ الخبر التالي:
        العنوان: {title}
        التفاصيل: {summary}
        
        استخرج التالي بصيغة JSON فقط بدون أي نص إضافي:
        {{
            "category": "تصنيف الخبر (سياسة، اقتصاد، رياضة، تكنولوجيا، صحة)",
            "importance": "رقم من 1 إلى 10 يمثل أهمية الخبر (10 عاجل ومهم جدا)",
            "seo_title": "أعد صياغة العنوان ليكون جذابا ومناسبا لمحركات البحث"
        }}
        """
        response = model.generate_content(prompt)
        # تحويل رد الذكاء الاصطناعي إلى قاموس بايثون
        ai_data = json.loads(response.text.replace('```json', '').replace('```', ''))
        return ai_data
    except:
        # في حال فشل الذكاء الاصطناعي نعطي قيماً افتراضية
        return {"category": "أخبار عامة", "importance": 5, "seo_title": title}

# جلب الأخبار
for url in RSS_FEEDS:
    feed = feedparser.parse(url)
    # نأخذ أحدث 5 أخبار من كل مصدر لتجنب الضغط على الـ API
    for entry in feed.entries[:5]:
        ai_result = process_news_with_ai(entry.title, getattr(entry, 'summary', ''))
        
        news_item = {
            "title": ai_result["seo_title"],
            "original_link": entry.link,
            "category": ai_result["category"],
            "importance": int(ai_result["importance"]),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=500" # صورة افتراضية
        }
        news_data.append(news_item)

# ترتيب الأخبار حسب الأهمية (من 10 إلى 1) التي حددها الذكاء الاصطناعي
news_data = sorted(news_data, key=lambda x: x['importance'], reverse=True)

# حفظ الأخبار في ملف JSON لتقرأه واجهة الموقع
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(news_data, f, ensure_ascii=False, indent=4)

print("تم تحديث الأخبار بنجاح!")
