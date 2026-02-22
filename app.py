import streamlit as st
from groq import Groq
import json

# --- إعدادات الصفحة ---
st.set_page_config(page_title="NBUG AI Scanner", page_icon="🔐")

# --- محاولة جلب المفاتيح من الأسرار ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    ADMIN_PASS = st.secrets["ADMIN_PASS"]
except Exception:
    st.error("⚠️ خطأ: لم يتم ضبط مفاتيح API في إعدادات Streamlit Secrets.")
    st.stop()

# --- إدارة الحالة ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'keys_db' not in st.session_state: st.session_state.keys_db = {"NBUG-FREE": 3}

# واجهة الدخول
if not st.session_state.auth:
    st.title("🛡️ NBUG Lab Activation")
    key_input = st.text_input("أدخل كود التفعيل:", type="password")
    if st.button("تفعيل"):
        if key_input == ADMIN_PASS:
            st.session_state.auth = True
            st.session_state.role = "admin"
            st.rerun()
        elif key_input in st.session_state.keys_db:
            st.session_state.auth = True
            st.session_state.role = "user"
            st.session_state.current_key = key_input
            st.rerun()
        else: st.error("الكود غير صحيح")
    st.stop()

# واجهة الفحص
st.title("🕵️ NBUG AI Scanner")
code_to_scan = st.text_area("أدخل الكود هنا:", height=200)

if st.button("ابدأ تحليل الثغرات 🔍"):
    if not code_to_scan:
        st.warning("الرجاء إدخال كود")
    else:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            res = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[
                    {"role": "system", "content": "You are a cyber security expert. Return a JSON with a 'vulnerabilities' list (name, severity, description in Arabic)."},
                    {"role": "user", "content": code_to_scan}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            for v in data.get("vulnerabilities", []):
                with st.expander(f"🔴 {v['name']}"):
                    st.write(v['description'])
        except Exception as e:
            st.error(f"خطأ تقني: {e}")

if st.button("تسجيل خروج 🚪"):
    st.session_state.auth = False
    st.rerun()
