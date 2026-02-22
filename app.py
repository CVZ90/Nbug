import streamlit as st
from groq import Groq
import json

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="NBUG AI Scanner", 
    page_icon="🔐", 
    layout="centered"
)

# --- جلب البيانات السرية من Streamlit Secrets ---
# تأكد من إضافة هذه المفاتيح في إعدادات Streamlit Cloud لاحقاً
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    ADMIN_PASS = st.secrets["ADMIN_PASS"]
except KeyError:
    st.error("⚠️ لم يتم العثور على المفاتيح السرية (Secrets). تأكد من إعداد ملف secrets.toml أو إضافتها في Streamlit Cloud.")
    st.stop()

# --- إدارة حالة الجلسة (للمفاتيح وتجربة المستخدم) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'keys_db' not in st.session_state:
    # ملاحظة: هذه البيانات مؤقتة، ستختفي عند إعادة تشغيل التطبيق (Restart)
    st.session_state.keys_db = {"NBUG-FREE": 5} 

# --- واجهة تسجيل الدخول ---
if not st.session_state.authenticated:
    st.title("🛡️ NBUG Security Lab")
    st.subheader("تفعيل النظام الاستخباراتي")
    
    with st.container():
        license_key = st.text_input("أدخل كود التفعيل الخاص بك:", type="password", placeholder="NBUG-XXXX-XXXX")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("تفعيل ✅"):
                if license_key == ADMIN_PASS:
                    st.session_state.authenticated = True
                    st.session_state.role = "admin"
                    st.rerun()
                elif license_key in st.session_state.keys_db:
                    if st.session_state.keys_db[license_key] > 0:
                        st.session_state.authenticated = True
                        st.session_state.role = "user"
                        st.session_state.current_key = license_key
                        st.rerun()
                    else:
                        st.error("❌ انتهى رصيد هذا الكود")
                else:
                    st.error("❌ كود غير صحيح")
        
    st.markdown("---")
    st.info("📢 لشراء كود تفعيل، تواصل معنا عبر تلغرام: [@nbug_lab]")
    st.stop()

# --- لوحة التحكم (Admin Only) ---
if st.session_state.role == "admin":
    with st.expander("⚙️ لوحة تحكم المدير (توليد مفاتيح)"):
        new_k = st.text_input("اسم الكود الجديد:", placeholder="مثال: VIP-USER-2026")
        tries = st.number_input("عدد المحاولات:", min_value=1, max_value=100, value=5)
        if st.button("توليد وحفظ 🔑"):
            if new_k:
                st.session_state.keys_db[new_k] = tries
                st.success(f"تم إنشاء الكود {new_k} بنجاح!")
        
        st.write("المفاتيح الحالية في الذاكرة:")
        st.write(st.session_state.keys_db)

# --- واجهة الفحص الرئيسية ---
st.title("🕵️ NBUG AI Scanner")
status_color = "🟢" if st.session_state.role == "admin" else "🔵"
st.caption(f"{status_color} الوضع الحالي: {st.session_state.role.upper()} | الرصيد: {st.session_state.keys_db.get(st.session_state.current_key, '∞') if st.session_state.role == 'user' else 'غير محدود'}")

code_content = st.text_area("أدخل الكود البرمجي المراد فحصه:", height=250, placeholder="Python, PHP, JS, SQL code here...")

if st.button("🔍 ابدأ تحليل الثغرات"):
    if not code_content:
        st.warning("الرجاء وضع كود أولاً!")
    else:
        # خصم رصيد المستخدم العادي
        if st.session_state.role == "user":
            st.session_state.keys_db[st.session_state.current_key] -= 1
        
        with st.spinner("جاري الاتصال بذكاء NBUG وتوليد التقرير..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-specdec",
                    messages=[
                        {"role": "system", "content": "You are an elite Cyber Security Auditor. Output ONLY a valid JSON with a 'vulnerabilities' list. Use Arabic for descriptions and names. Include: name, severity, description, vulnerable_code, fixed_code."},
                        {"role": "user", "content": f"Analyze this code:\n{code_content}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                report = json.loads(completion.choices[0].message.content)
                
                if report.get("vulnerabilities"):
                    st.subheader("🛡️ نتائج الفحص:")
                    for v in report["vulnerabilities"]:
                        severity_color = "🔴" if v['severity'].lower() in ['high', 'critical'] else "🟡"
                        with st.expander(f"{severity_color} {v['name']} ({v['severity']})"):
                            st.markdown(f"**الشرح:** {v['description']}")
                            st.error(f"**الكود المكتشف:**\n```python\n{v['vulnerable_code']}\n```")
                            st.success(f"**التصحيح الآمن:**\n```python\n{v['fixed_code']}\n```")
                else:
                    st.balloons()
                    st.success("✅ نظيف! لم يتم العثور على ثغرات معروفة.")
            
            except Exception as e:
                st.error(f"خطأ تقني: {str(e)}")

if st.button("تسجيل خروج 🚪"):
    st.session_state.authenticated = False
    st.rerun()
