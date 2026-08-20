import streamlit as st
from google import genai
import tempfile
import os
import json

st.set_page_config(page_title="Internal Feedback App", page_icon="🎙️", layout="centered")
st.title("🎙️ 1-Click Team Voice Feedback")
st.write("Click the microphone below, speak in **any language**, and stop when done.")

# 1. Capture direct audio input
audio_value = st.audio_input("Record your feedback")

if audio_value:
    with st.spinner("Processing voice feedback with Gemini..."):
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_value.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Initialize Gemini client
            client = genai.Client()
            uploaded_audio = client.files.upload(file=tmp_path)
            
            prompt = """
            Listen to this audio. The speaker can use any language.
            1. Translate the core message to English.
            2. Extract 3 main actionable facts/points.
            3. Determine sentiment (Positive, Neutral, or Negative).
            4. Provide a 2-3 bullet meeting-style summary.
            
            Output strictly valid JSON with keys: "translation", "facts", "sentiment", "summary".
            """
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[prompt, uploaded_audio],
            )
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            data = json.loads(raw_text.strip())
            
            st.success("✅ Feedback processed successfully!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sentiment", data.get("sentiment", "N/A"))
            
            st.subheader("📋 Meeting-Style Takeaways")
            for item in data.get("summary", []):
                st.write(f"• {item}")
                
            st.subheader("📌 Key Facts Extracted")
            for fact in data.get("facts", []):
                st.write(f"• {fact}")
                
            with st.expander("🔍 View English Translation"):
                st.write(data.get("translation", ""))
                
        except Exception as e:
            st.error(f"Error analyzing audio: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
