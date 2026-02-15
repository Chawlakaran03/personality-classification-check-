import streamlit as st
import py_avataaars as pa
from PIL import Image
import base64
import os
import matplotlib.pyplot as plt
import random
import uuid
import google.generativeai as genai
import json
import re

# --- 1. SETTINGS & SECRETS ---
st.set_page_config(page_title="🧠 Personality & Avatar Generator", layout="centered")

# GitHub pe upload karne ke liye API key secrets se uthayenge
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("API Key missing! Add GOOGLE_API_KEY to Streamlit Secrets.")
        st.stop()
except Exception:
    st.warning("Running locally? Make sure .streamlit/secrets.toml exists.")
    st.stop()

# --- 2. STYLING ---
st.markdown("""
    <style>
    .main { background: linear-gradient(to bottom right, #f8f9fa, #e9ecef); padding: 20px; border-radius: 15px; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #6c5ce7; color: white; }
    .box { padding: 20px; border-radius: 15px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---

def classify_personality_api(sentence):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Strict prompt taaki JSON hi mile
        prompt = (
            "Analyze the following personality description and provide scores (0-100) for the Big Five traits: "
            "Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism. "
            "Return ONLY a JSON object. No intro, no outro. "
            f"Description: {sentence}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def parse_and_plot(raw_text):
    try:
        # Regex: Yeh line saara extra text hata degi aur sirf { ... } nikalegi
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not match:
            return None
        
        data = json.loads(match.group())
        
        # Plotting
        fig, ax = plt.subplots(figsize=(7, 4))
        categories = list(data.keys())
        values = [float(str(v).replace('%', '')) for v in data.values()]
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        ax.bar(categories, values, color=colors)
        ax.set_ylim(0, 100)
        plt.xticks(rotation=15)
        st.pyplot(fig)
        return data
    except:
        return None

def make_avatar(gender, desc):
    s = desc.lower()
    # Basic logic to vary avatar based on gender
    top = random.choice([pa.TopType.LONG_HAIR_BOB, pa.TopType.LONG_HAIR_STRAIGHT]) if gender == "Female" \
          else random.choice([pa.TopType.SHORT_HAIR_FRIZZLE, pa.TopType.SHORT_HAIR_SHORT_CURLY])
    
    avatar = pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        top_type=top,
        mouth_type=pa.MouthType.SMILE if "happy" in s or "cool" in s else pa.MouthType.DEFAULT,
        eye_type=pa.EyesType.HAPPY if "positive" in s else pa.EyesType.DEFAULT,
        skin_color=random.choice(list(pa.SkinColor)),
        hair_color=random.choice(list(pa.HairColor))
    )
    return avatar

# --- 4. UI ---
st.title("🧠 Personality & Avatar AI")

with st.container():
    st.markdown('<div class="main">', unsafe_allow_html=True)
    with st.form("my_form"):
        name = st.text_input("Name")
        gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
        desc = st.text_area("Tell us about yourself...")
        btn = st.form_submit_button("Generate Magic ✨")
    st.markdown('</div>', unsafe_allow_html=True)

if btn:
    if name and desc:
        with st.spinner("AI is thinking..."):
            res_text = classify_personality_api(desc)
            
            # Left side: Chart, Right side: Avatar
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="box">', unsafe_allow_html=True)
                st.subheader("Personality Traits")
                parsed_data = parse_and_plot(res_text)
                if not parsed_data:
                    st.error("Could not parse data. Try a longer description!")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="box">', unsafe_allow_html=True)
                st.subheader("Your Avatar")
                av = make_avatar(gender, desc)
                fname = f"{uuid.uuid4().hex}.png"
                av.render_png_file(fname)
                st.image(fname)
                
                # Download button
                with open(fname, "rb") as f:
                    st.download_button("📥 Download", f, file_name="avatar.png")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Bhai, naam aur description toh daal de!")
