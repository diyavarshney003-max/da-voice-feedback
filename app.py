import streamlit as st
from google import genai
import tempfile
import os
import json
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="DA Shift Feedback", page_icon="🎙️", layout="centered")

DATA_FILE = "da_feedback_data.csv"

if not os.path.exists(DATA_FILE):
    df_empty = pd.DataFrame(columns=["Date", "DA ID", "Phone Number", "Language", "Sentiment", "Translation", "Takeaways", "Facts"])
    df_empty.to_csv(DATA_FILE, index=False)

# ==========================================
# 1. ADMIN DASHBOARD (SECURE)
# ==========================================
if st.query_params.get("admin") == "true":
    st.title("🔒 Manager Dashboard")
    
    admin_pass = st.text_input("Enter Manager Password", type="password")
    
    if admin_pass == "Manager@123":
        try:
            df = pd.read_csv(DATA_FILE)
            
            if df.empty:
                st.info("No feedback data available yet.")
                st.stop()
                
            df['Date'] = pd.to_datetime(df['Date'])
            
            st.subheader("📅 Filter Data by Date")
            min_date = df['Date'].dt.date.min()
            max_date = df['Date'].dt.date.max()
            
            date_range = st.date_input("Select Time Period", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
                filtered_df = df.loc[mask]
            else:
                filtered_df = df
            
            st.write(f"Showing {len(filtered_df)} records:")
            st.dataframe(filtered_df, use_container_width=True)
            
            if not filtered_df.empty:
                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Filtered Data",
                    data=csv_data,
                    file_name=f"DA_Feedback_{start_date}_to_{end_date}.csv" if len(date_range)==2 else "DA_Feedback.csv",
                    mime="text/csv",
                    type="primary"
                )
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")
    elif admin_pass:
        st.error("❌ Incorrect Password")
        
    st.stop()


# ==========================================
# 2. DA FEEDBACK FLOW (PUBLIC)
# ==========================================
ALL_LANGUAGES = [
    "English", "हिन्दी (Hindi)", "বাংলা (Bengali)", "తెలుగు (Telugu)",
    "मराठी (Marathi)", "தமிழ் (Tamil)", "ಕನ್ನಡ (Kannada)"
]

# ==========================================
# ⚠️ PLACEHOLDER: UPDATE YOUR DA IDs HERE ⚠️
# ==========================================
# Add all your actual DA numbers inside the brackets below.
# Keep the first option as "-- Select DA ID --" so they are forced to choose.
# Make sure each ID is inside quotes with a comma after it!
DA_LIST = [
    "-- Select DA ID --",
    "1045",
    "PLACEHOLDER_ID_1",
    "PLACEHOLDER_ID_2",
    "PLACEHOLDER_ID_3",
    "PLACEHOLDER_ID_4"
]
# ==========================================

UI_TEXT = {
    "English": {"title": "🎙️ End-of-Shift Voice Feedback", "select_lang": "Step 1: Language", "enter_id": "Step 2: Select DA ID", "enter_num": "Step 3: Phone Number", "record": "Step 4: Record", "record_clip": "Record your clip", "submit": "🚀 Submit Feedback", "success": "✅ Submitted!", "err_id": "⚠️ Select ID", "err_num": "⚠️ Enter Phone Number", "err_aud": "⚠️ Record Audio"},
    "हिन्दी (Hindi)": {"title": "🎙️ शिफ्ट समाप्ति फीडबैक", "select_lang": "भाषा", "enter_id": "DA ID चुनें", "enter_num": "फ़ोन नंबर दर्ज करें", "record": "रिकॉर्ड करें", "record_clip": "अपना क्लिप रिकॉर्ड करें", "submit": "🚀 सबमिट करें", "success": "✅ धन्यवाद!", "err_id": "⚠️ ID चुनें", "err_num": "⚠️ फ़ोन नंबर दर्ज करें", "err_aud": "⚠️ ऑडियो रिकॉर्ड करें"},
    "বাংলা (Bengali)": {"title": "🎙️ শিফট শেষের প্রতিক্রিয়া", "select_lang": "भाषा", "enter_id": "DA ID নির্বাচন করুন", "enter_num": "ফোন নম্বর লিখুন", "record": "রেকর্ড করুন", "record_clip": "আপনার অডিও রেকর্ড করুন", "submit": "🚀 জমা দিন", "success": "✅ সফল হয়েছে!", "err_id": "⚠️ ID নির্বাচন করুন", "err_num": "⚠️ ফোন নম্বর লিখুন", "err_aud": "⚠️ অডিও রেকর্ড করুন"},
    "తెలుగు (Telugu)": {"title": "🎙️ షిఫ్ట్ ముగింపు ఫీడ్‌బ్యాక్", "select_lang": "భాష", "enter_id": "DA ID ఎంచుకోండి", "enter_num": "ఫోన్ నంబర్ నమోదు చేయండి", "record": "రికార్డ్ చేయండి", "record_clip": "మీ వాయిస్ రికార్డ్ చేయండి", "submit": "🚀 సమర్పించండి", "success": "✅ విజయవంతమైంది!", "err_id": "⚠️ ID ఎంచుకోండి", "err_num": "⚠️ ఫోన్ నంబర్ నమోదు చేయండి", "err_aud": "⚠️ ఆడియో రికార్డ్ చేయండి"},
    "मराठी (Marathi)": {"title": "🎙️ शिफ्ट समाप्ती फीडबॅक", "select_lang": "भाषा", "enter_id": "DA ID निवडा", "enter_num": "फोन नंबर एंटर करा", "record": "रेकॉर्ड करा", "record_clip": "तुमचा ऑडिओ रेकॉर्ड करा", "submit": "🚀 सबमिट करा", "success": "✅ सबमिट केले!", "err_id": "⚠️ ID निवडा", "err_num": "⚠️ फोन नंबर एंटर करा", "err_aud": "⚠️ ऑडिओ रेकॉर्ड करा"},
    "தமிழ் (Tamil)": {"title": "🎙️ பணி முடிவு கருத்து", "select_lang": "மொழி", "enter_id": "DA ID ஐ தேர்ந்தெடுக்கவும்", "enter_num": "தொலைபேசி எண்ணை உள்ளிடவும்", "record": "பதிவு செய்யவும்", "record_clip": "உங்கள் ஆடியோவை பதிவு செய்யவும்", "submit": "🚀 சமர்ப்பிக்கவும்", "success": "✅ சமர்ப்பிக்கப்பட்டது!", "err_id": "⚠️ ID ஐ தேர்ந்தெடுக்கவும்", "err_num": "⚠️ தொலைபேசி எண்ணை உள்ளிடவும்", "err_aud": "⚠️ ஆடியோவைப் பதிவு செய்யவும்"},
    "ಕನ್ನಡ (Kannada)": {"title": "🎙️ ಶಿಫ್ಟ್ ಮುಕ್ತಾಯದ ಪ್ರತಿಕ್ರಿಯೆ", "select_lang": "ಭಾಷೆ", "enter_id": "DA ID ಆಯ್ಕೆಮಾಡಿ", "enter_num": "ಫೋನ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ", "record": "ರೆಕಾರ್ಡ್ ಮಾಡಿ", "record_clip": "ನಿಮ್ಮ ಆಡಿಯೋ ರೆಕಾರ್ಡ್ ಮಾಡಿ", "submit": "🚀 ಸಲ್ಲಿಸಿ", "success": "✅ ಸಲ್ಲಿಸಲಾಗಿದೆ!", "err_id": "⚠️ ID ಆಯ್ಕೆಮಾಡಿ", "err_num": "⚠️ ಫೋನ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ", "err_aud": "⚠️ ಆಡಿಯೋ ರೆಕಾರ್ಡ್ ಮಾಡಿ"}
}

if "submitted" not in st.session_state:
    st.session_state.submitted = False

selected_lang = st.selectbox("🌐 Language / भाषा / ভাষা / భాష / மொழி / ಭಾಷೆ", options=ALL_LANGUAGES)
t = UI_TEXT.get(selected_lang, UI_TEXT["English"])

st.title(t["title"])

if st.session_state.submitted:
    st.success(t["success"])
    if st.button("🔄 Start Over"):
        st.session_state.submitted = False
        st.rerun()
    st.stop()

# Dropdown for ID using the placeholder list
da_id_val = st.selectbox(t["enter_id"], options=DA_LIST)

# Text input for Phone Number
phone_val = st.text_input(t["enter_num"], placeholder="e.g. 9876543210")

st.subheader(t["record"])
audio = st.audio_input(t["record_clip"])

if st.button(t["submit"], type="primary", use_container_width=True):
    if da_id_val == DA_LIST[0]:
        st.error(t["err_id"])
    elif not phone_val.strip():
        st.error(t["err_num"])
    elif not audio:
        st.error(t["err_aud"])
    else:
        with st.spinner("Processing..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio.getvalue())
                tmp_path = tmp_file.name
                
            try:
                client = genai.Client()
                uploaded_audio = client.files.upload(file=tmp_path)
                
                prompt = f"""
                Analyze this feedback in {selected_lang}. 
                Translate to English, extract 3 facts, determine sentiment.
                Output JSON strictly: {{"translation": "...", "facts": ["..."], "sentiment": "...", "summary": ["..."]}}
                """
                response = client.models.generate_content(model='gemini-3.6-flash', contents=[prompt, uploaded_audio])
                
                raw_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
                data = json.loads(raw_text)
                
                new_row = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "DA ID": da_id_val,
                    "Phone Number": phone_val,
                    "Language": selected_lang,
                    "Sentiment": data.get("sentiment", ""),
                    "Translation": data.get("translation", ""),
                    "Takeaways": " | ".join(data.get("summary", [])),
                    "Facts": " | ".join(data.get("facts", []))
                }])
                new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                
                st.session_state.submitted = True
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
