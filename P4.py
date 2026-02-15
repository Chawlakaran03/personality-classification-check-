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
st.set_page_config(page_title="🧠 Personality AI", layout="centered")

try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        st.stop()
except Exception:
    st.error("Secrets configuration error.")
    st.stop()

# --- 2. LOGIC FUNCTIONS ---

def classify_personality_api(sentence):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Prompt ko thoda aur sakht kar diya hai
        prompt = (
            "Analyze this personality description: " + sentence + "\n\n"
            "Provide scores (0-100) for: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism. "
            "Output MUST be in this exact JSON format: "
            '{"Openness": 50, "Conscientiousness": 50, "Extraversion": 50, "Agreeableness": 50, "Neuroticism": 50}'
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def clean_and_parse_json(raw_text):
    try:
        # Step 1: Text mein se sirf { ... } ke beech ka content nikalna
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            json_str = match.group()
            # Step 2: Extra cleanup agar Gemini ne koi unwanted characters daale hon
            json_str = json_str.replace('\n', '').replace('\r', '')
            return json.loads(json_str)
        return None
    except Exception as e:
        st.error(f"Internal Parsing Error: {e}")
        return None

def make_avatar(gender, desc):
    s = desc.lower()
    # Logic based on gender
    if gender == "Female":
        top = random.choice([pa.TopType.LONG_HAIR_BOB, pa.TopType.LONG_HAIR_CURLY, pa.TopType.LONG_HAIR_STRAIGHT])
    else:
        top = random.choice([pa.TopType.SHORT_HAIR_FRIZZLE, pa.TopType.SHORT_HAIR_DREADS, pa.TopType.SHORT_HAIR_SHORT_CURLY])
    
    return pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        top_type=top,
        mouth_type=pa.MouthType.SMILE if any(word in s for word in ["happy", "cool", "fun"]) else pa.MouthType.DEFAULT,
        eye_type=pa.EyesType.HAPPY if "positive" in s else pa.EyesType.DEFAULT,
        skin_color=random.choice(list(pa.SkinColor)),
        hair_color=random.choice(list(pa.HairColor))
    )

# --- 3. UI ---
st.title("🧠 Personality & Avatar AI")

with st.form("main_form"):
    name = st.text_input("Name")
    gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
    desc = st.text_area("Tell us about yourself (Try to write 3-4 sentences)...")
    btn = st.form_submit_button("Generate ✨")

if btn:
    if name and desc:
        with st.spinner("Analyzing..."):
            raw_text = classify_personality_api(desc)
            data = clean_and_parse_json(raw_text)
            
            if data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Personality Traits")
                    # Plotting
                    fig, ax = plt.subplots()
                    # Gemini kabhi keys choti-badi kar sakta hai, isliye labels handle karein
                    labels = list(data.keys())
                    values = [float(str(v).replace('%', '')) for v in data.values()]
                    ax.bar(labels, values, color=['#6c5ce7', '#00cec9', '#fab1a0', '#fdcb6e', '#ff7675'])
                    ax.set_ylim(0, 100)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                
                with col2:
                    st.subheader("Your Avatar")
                    av = make_avatar(gender, desc)
                    fname = f"{uuid.uuid4().hex}.png"
                    av.render_png_file(fname)
                    st.image(fname)
                    with open(fname, "rb") as f:
                        st.download_button("📥 Download", f, file_name="avatar.png")
            else:
                # Debugging ke liye raw text dikhayega agar fail hua
                st.error("Parsing failed. AI output format was unexpected.")
                with st.expander("See Raw Output from AI"):
                    st.write(raw_text)
    else:
        st.warning("Naam aur description bharo bhai!")
