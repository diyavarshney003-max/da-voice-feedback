import streamlit as st
from google import genai
import tempfile
import os
import json
import requests

st.set_page_config(page_title="DA Shift Feedback", page_icon="🎙️", layout="centered")

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Paste your deployed Google Apps Script Webhook URL here
WEBHOOK_URL = "PASTE_YOUR_WEB_APP_URL_HERE"

# All 22 Scheduled Indian Languages + English
ALL_LANGUAGES = [
    "English", "हिन्दी (Hindi)", "বাংলা (Bengali)", "తెలుగు (Telugu)",
    "मराठी (Marathi)", "தமிழ் (Tamil)", "ગુજરાતી (Gujarati)", "اردو (Urdu)",
    "ಕನ್ನಡ (Kannada)", "ଓଡ଼ିଆ (Odia)", "മലയാളം (Malayalam)", "ਪੰਜਾਬੀ (Punjabi)",
    "অসমীয়া (Assamese)", "मैथिली (Maithili)", "संताली (Santali)", "कश्मीरी (Kashmiri)",
    "नेपाली (Nepali)", "कोंकणी (Konkani)", "सिंधी (Sindhi)", "डोगरी (Dogri)",
    "मणिपुरी (Manipuri)", "बोडो (Bodo)", "संस्कृत (Sanskrit)"
]

# UI Translations for major languages (Defaults to English for others)
UI_TEXT = {
    "English": {
        "title": "🎙️ End-of-Shift Voice Feedback",
        "select_lang": "Step 1: Choose your Preferred Language",
        "enter_id": "Step 2: Enter your DA ID",
        "record_prompt": "Step 3: Record your voice feedback",
        "add_more": "➕ Add another voice clip",
        "clear_all": "🔄 Clear & Start Over",
        "submit_btn": "🚀 Submit Feedback",
        "submitting": "Processing and submitting your feedback...",
        "success": "✅ Thank you! Your feedback has been submitted successfully.",
        "error_no_audio": "⚠️ Please record at least one audio message.",
        "error_no_da": "⚠️ Please enter your DA ID before submitting."
    },
    "हिन्दी (Hindi)": {
        "title": "🎙️ शिफ्ट समाप्ति फीडबैक",
        "select_lang": "स्टेप 1: अपनी भाषा चुनें",
        "enter_id": "स्टेप 2: अपना DA ID दर्ज करें",
        "record_prompt": "स्टेप 3: फीडबैक रिकॉर्ड करें",
        "add_more": "➕ एक और ऑडियो जोड़ें",
        "clear_all": "🔄 फिर से शुरू करें",
        "submit_btn": "🚀 सबमिट करें",
        "submitting": "फीडबैक सबमिट हो रहा है...",
        "success": "✅ धन्यवाद! फीडबैक सफलतापूर्वक दर्ज हो गया।",
        "error_no_audio": "⚠️ कृपया कम से कम एक ऑडियो रिकॉर्ड करें।",
        "error_no_da": "⚠️ कृपया अपना DA ID दर्ज करें।"
    },
    "বাংলা (Bengali)": {
        "title": "🎙️ শিফট শেষের প্রতিক্রিয়া",
        "select_lang": "ধাপ ১: আপনার ভাষা চয়ন করুন",
        "enter_id": "ধাপ ২: আপনার DA ID লিখুন",
        "record_prompt": "ধাপ ৩: আপনার প্রতিক্রিয়া রেকর্ড করুন",
        "add_more": "➕ আরও একটি অডিও যোগ করুন",
        "clear_all": "🔄 মুছে ফেলুন",
        "submit_btn": "🚀 জমা দিন",
        "submitting": "আপনার প্রতিক্রিয়া জমা হচ্ছে...",
        "success": "✅ ধন্যবাদ! সফলভাবে জমা হয়েছে।",
        "error_no_audio": "⚠️ অনুগ্রহ করে একটি অডিও রেকর্ড করুন।",
        "error_no_da": "⚠️ অনুগ্রহ করে আপনার DA ID লিখুন।"
    },
    "తెలుగు (Telugu)": {
        "title": "🎙️ షిఫ్ట్ ముగింపు ఫీడ్‌బ్యాక్",
        "select_lang": "దశ 1: మీ భాషను ఎంచుకోండి",
        "enter_id": "దశ 2: మీ DA ID నమోదు చేయండి",
        "record_prompt": "దశ 3: వాయిస్ ఫీడ్‌బ్యాక్ రికార్డ్ చేయండి",
        "add_more": "➕ మరొక ఆడియో జోడించండి",
        "clear_all": "🔄 మళ్లీ ప్రారంభించండి",
        "submit_btn": "🚀 సమర్పించండి",
        "submitting": "ప్రాసెస్ చేయబడుతోంది...",
        "success": "✅ ధన్యవాదాలు! ఫీడ్‌బ్యాక్ సమర్పించబడింది.",
        "error_no_audio": "⚠️ దయచేసి ఆడియోను రికార్డ్ చేయండి.",
        "error_no_da": "⚠️ దయచేసి మీ DA ID నమోదు చేయండి."
    },
    "मराठी (Marathi)": {
        "title": "🎙️ शिफ्ट समाप्ती फीडबॅक",
        "select_lang": "पायरी 1: तुमची भाषा निवडा",
        "enter_id": "पायरी 2: तुमचा DA ID एंटर करा",
        "record_prompt": "पायरी 3: तुमचा फीडबॅक रेकॉर्ड करा",
        "add_more": "➕ आणखी एक ऑडिओ जोडा",
        "clear_all": "🔄 पुन्हा सुरू करा",
        "submit_btn": "🚀 सबमिट करा",
        "submitting": "फीडबॅक सबमिट होत आहे...",
        "success": "✅ धन्यवाद! तुमचा फीडबॅक यशस्वीरित्या सबमिट झाला आहे.",
        "error_no_audio": "⚠️ कृपया किमान एक ऑडिओ रेकॉर्ड करा.",
        "error_no_da": "⚠️ कृपया तुमचा DA ID एंटर करा."
    },
    "தமிழ் (Tamil)": {
        "title": "🎙️ பணி முடிவு கருத்து",
        "select_lang": "படி 1: உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்",
        "enter_id": "படி 2: உங்கள் DA ID ஐ உள்ளிடவும்",
        "record_prompt": "படி 3: கருத்துக்களைப் பதிவு செய்யவும்",
        "add_more": "➕ மேலும் ஒரு ஆடியோ சேர்க்கவும்",
        "clear_all": "🔄 மீண்டும் தொடங்கவும்",
        "submit_btn": "🚀 சமர்ப்பிக்கவும்",
        "submitting": "சமர்ப்பிக்கப்படுகிறது...",
        "success": "✅ நன்றி! கருத்து பதிவு செய்யப்பட்டது.",
        "error_no_audio": "⚠️ ஆடியோவைப் பதிவு செய்யவும்.",
        "error_no_da": "⚠️ உங்கள் DA ID ஐ உள்ளிடவும்."
    },
    "ಕನ್ನಡ (Kannada)": {
        "title": "🎙️ ಶಿಫ್ಟ್ ಮುಕ್ತಾಯದ ಪ್ರತಿಕ್ರಿಯೆ",
        "select_lang": "ಹಂತ 1: ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "enter_id": "ಹಂತ 2: ನಿಮ್ಮ DA ID ನಮೂದಿಸಿ",
        "record_prompt": "ಹಂತ 3: ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ರೆಕಾರ್ಡ್ ಮಾಡಿ",
        "add_more": "➕ ಇನ್ನೊಂದು ಆಡಿಯೋ ಸೇರಿಸಿ",
        "clear_all": "🔄 ಮೊದಲಿನಿಂದ ಪ್ರಾರಂಭಿಸಿ",
        "submit_btn": "🚀 ಪ್ರತಿಕ್ರಿಯೆ ಸಲ್ಲಿಸಿ",
        "submitting": "ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ...",
        "success": "✅ ಧನ್ಯವಾದಗಳು! ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ಸಲ್ಲಿಸಲಾಗಿದೆ.",
        "error_no_audio": "⚠️ ದಯವಿಟ್ಟು ಆಡಿಯೋ ರೆಕಾರ್ಡ್ ಮಾಡಿ.",
        "error_no_da": "⚠️ ದಯವಿಟ್ಟು ನಿಮ್ಮ DA ID ನಮೂದಿಸಿ."
    }
}

# ==========================================
# 2. SESSION STATE
# ==========================================
if "recordings" not in st.session_state:
    st.session_state.recordings = []
if "num_inputs" not in st.session_state:
    st.session_state.num_inputs = 1
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Language Selector
selected_lang = st.selectbox(
    "🌐 Language / ಭಾಷೆ / மொழி / భాష / भाषा",
    options=ALL_LANGUAGES,
    index=0
)

# Fetch translation based on selection (Fall back to English if not in dict)
t = UI_TEXT.get(selected_lang, UI_TEXT["English"])

st.title(t["title"])

if st.session_state.submitted:
    st.success(t["success"])
    if st.button(t["clear_all"]):
        st.session_state.recordings = []
        st.session_state.num_inputs = 1
        st.session_state.submitted = False
        st.rerun()
    st.stop()

# Text Input for DA ID
da_id_val = st.text_input(t["enter_id"], placeholder="e.g. 1045")

# Audio Recording Inputs
st.subheader(t["record_prompt"])
for i in range(st.session_state.num_inputs):
    audio = st.audio_input(f"Clip #{i+1}", key=f"audio_{i}")
    if audio:
        if len(st.session_state.recordings) <= i:
            st.session_state.recordings.append(audio)
        else:
            st.session_state.recordings[i] = audio

col1, col2 = st.columns(2)
with col1:
    if st.button(t["add_more"]):
        st.session_state.num_inputs += 1
        st.rerun()
with col2:
    if st.button(t["clear_all"]):
        st.session_state.recordings = []
        st.session_state.num_inputs = 1
        st.rerun()

st.divider()

# ==========================================
# 3. BACKEND PROCESSING ON SUBMIT
# ==========================================
if st.button(t["submit_btn"], type="primary", use_container_width=True):
    if not da_id_val.strip():
        st.error(t["error_no_da"])
    elif not st.session_state.recordings:
        st.error(t["error_no_audio"])
    else:
        with st.spinner(t["submitting"]):
            uploaded_files = []
            tmp_paths = []
            try:
                client = genai.Client()
                
                # Upload all audio clips
                for rec in st.session_state.recordings:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(rec.getvalue())
                        tmp_paths.append(tmp_file.name)
                        up = client.files.upload(file=tmp_file.name)
                        uploaded_files.append(up)
                
                prompt = f"""
                You are analyzing shift feedback from a Delivery Associate.
                The speaker chose {selected_lang}. They will likely speak in this language.
                
                Tasks:
                1. Translate all audio clips combined into clear English.
                2. Extract up to 3 main operational issues/facts (route issues, customer behavior, app bugs).
                3. Determine overall sentiment (Positive, Neutral, Negative).
                4. Create a 2-3 bullet point summary for shift managers.
                
                Output STRICT valid JSON format:
                {{
                  "translation": "English translation here",
                  "facts": ["Fact 1", "Fact 2"],
                  "sentiment": "Positive/Neutral/Negative",
                  "summary": ["Bullet 1", "Bullet 2"]
                }}
                """
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt] + uploaded_files
                )
                
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                
                data = json.loads(raw_text.strip())
                data["da_id"] = da_id_val.strip()
                data["language"] = selected_lang
                
                # Post to Google Sheets
                if WEBHOOK_URL and "http" in WEBHOOK_URL:
                    requests.post(WEBHOOK_URL, json=data)
                
                st.session_state.submitted = True
                st.rerun()
                
            except Exception as e:
                st.error(f"Error submitting feedback: {e}")
            finally:
                for p in tmp_paths:
                    if os.path.exists(p):
                        os.remove(p)
