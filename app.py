import streamlit as st
from duckduckgo_search import DDGS
from groq import Groq
import os

# إعدادات الصفحة
st.set_page_config(page_title="نظام توقع كأس العالم 2026", layout="wide")
st.title("🏆 نظام تحليل وتوقع كأس العالم 2026 (Llama 3.3 70B)")
st.markdown("هذا النظام يقوم بالبحث في الإنترنت عن أحدث الإحصائيات، ثم يحللها بذكاء اصطناعي عالمي لتقديم توقع دقيق.")

# إعداد مفتاح API (يمكنك وضعه هنا مباشرة أو عبر متغيرات البيئة)
GROQ_API_KEY = "ضع_مفتاح_الـ API_الخاص_بك_هنا"
client = Groq(api_key=GROQ_API_KEY)

def search_latest_stats(match_query):
    """دالة للبحث في الإنترنت عن معلومات اللاعبين والمنتخبات"""
    with DDGS() as ddgs:
        # البحث عن آخر الأخبار والإحصائيات
        results = list(ddgs.text(f"{match_query} stats players injuries 2025 2026", max_results=6))
        context = "أحدث البيانات من الإنترنت:\n"
        for r in results:
            context += f"- {r['title']}: {r['body']}\n"
        return context

def analyze_and_predict(team1, team2):
    """جلب البيانات وتحليلها بواسطة الذكاء الاصطناعي"""
    with st.spinner("🌍 جاري البحث عن إحصائيات اللاعبين والإصابات..."):
        match_info = f"{team1} vs {team2} World Cup 2026"
        live_data = search_latest_stats(match_info)
        
    with st.spinner("🧠 جاري تحليل البيانات رياضياً وتوقع النتيجة..."):
        prompt = f"""
        أنت خبير إحصائي عالمي ومحلل تكتيكي لكأس العالم 2026.
        بناءً على البيانات الحديثة التالية من الإنترنت:
        {live_data}
        
        قم بتحليل مباراة {team1} ضد {team2} وقدم تقريراً باللغة العربية يشمل:
        1. **حالة اللاعبين**: أبرز النجوم، الإصابات، والإيقافات.
        2. **التحليل التكتيكي**: أسلوب اللعب المتوقع لكل منتخب.
        3. **التوقع الرياضي**: استخدم حسابات الاحتمالات (xG) لتوقع النتيجة الدقيقة.
        4. **نسب الفوز**: اعطِ نسبة الفوز لكل منتخب بالمئوية.
        5. **اللاعبون الأكثر تسجيلاً**: توقع أسماء اللاعبين المرجح تسجيلهم.
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # نموذج قوي جداً ومتاح مجاناً
            messages=[
                {"role": "system", "content": "أنت محلل رياضي دقيق لا يهتم بالعواطف، بل بالأرقام والاحتمالات فقط."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # درجة حرارة منخفضة لضمان الدقة العالية في الأرقام
        )
        return completion.choices[0].message.content

# واجهة المستخدم
col1, col2 = st.columns(2)
with col1:
    team1 = st.text_input("المنتخب الأول 🟦", placeholder="مثال: الأرجنتين")
with col2:
    team2 = st.text_input("المنتخب الثاني 🟥", placeholder="مثال: فرنسا")

if st.button("🔮 ابدأ التحليل الدقيق وتوقع النتيجة", type="primary"):
    if team1 and team2:
        result = analyze_and_predict(team1, team2)
        st.divider()
        st.subheader("📊 التحليل والتوقع النهائي:")
        st.markdown(result)
    else:
        st.warning("الرجاء إدخال اسم المنتخبين لبدء التحليل.")
