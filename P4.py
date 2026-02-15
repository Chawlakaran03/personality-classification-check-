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

# Streamlit setup
st.set_page_config(page_title="🧠 Personality & Avatar Generator", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .main { background: linear-gradient(to right, #f0f2f6, #e0e7ff); padding: 2rem; border-radius: 15px; }
    .title { text-align: center; font-size: 2.2rem; font-weight: 700; color: #4a4a4a; }
    .avatar-box, .trait-box { border-radius: 10px; padding: 1rem; background-color: #ffffffaa; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# API Setup
GOOGLE_API_KEY = "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE" # Apni key use karein
genai.configure(api_key=GOOGLE_API_KEY)

def classify_personality_api(sentence):
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash") # Stable model use karein
        prompt = (f"Classify the following text based on the Big Five Personality Traits. "
                  f"Provide ONLY a flat JSON object with scores out of 100 for Openness, Conscientiousness, "
                  f"Extraversion, Agreeableness, and Neuroticism.\n\nText: {sentence}")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# FIX: Plotting function with Dict handling
def plot_personality_traits(traits_input):
    try:
        # Check if input is string, then parse
        if isinstance(traits_input, str):
            json_match = re.search(r'\{.*\}', traits_input, re.DOTALL)
            if not json_match:
                st.error("AI response format galat hai.")
                return
            data = json.loads(json_match.group())
        else:
            data = traits_input

        # FLATTENING: Agar AI ne nested dict bheja ho
        processed_traits = {}
        for k, v in data.items():
            if isinstance(v, dict):
                processed_traits.update(v)
            else:
                processed_traits[k] = v

        # Convert to float/int
        final_scores = {k: float(v) for k, v in processed_traits.items() if isinstance(v, (int, float, str))}

        # Plotting logic
        fig, ax = plt.subplots(figsize=(8, 4))
        keys = list(final_scores.keys())
        values = list(final_scores.values())
        
        ax.bar(keys, values, color="#6c5ce7")
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score")
        ax.set_title("Big Five Personality Traits")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Plotting Error: {str(e)}")

def create_avatar_by_sentence_and_gender(sentence, gender):
    try:
        options = {
            'style': 'CIRCLE' if "calm" in sentence.lower() else 'TRANSPARENT',
            'skin_color': random.choice(["TANNED", "YELLOW", "PALE", "LIGHT", "BROWN", "DARK_BROWN", "BLACK"]),
            'hair_color': random.choice(["AUBURN", "BLACK", "BLONDE", "BROWN", "RED", "SILVER_GRAY"]),
            'mouth_type': "SMILE" if "happy" in sentence.lower() else "DEFAULT",
            'eye_type': "HAPPY" if "positive" in sentence.lower() else "DEFAULT",
            'eyebrow_type': "DEFAULT",
            'accessories_type': "SUNGLASSES" if "cool" in sentence.lower() else "DEFAULT",
            'clothe_type': "HOODIE" if "relaxed" in sentence.lower() else "BLAZER_SHIRT",
            'clothe_graphic_type': "BAT"
        }

        top = random.choice(["LONG_HAIR_BOB", "LONG_HAIR_BUN"]) if gender == "Female" else "SHORT_HAIR_FRIZZLE"

        avatar = pa.PyAvataaar(
            style=getattr(pa.AvatarStyle, options['style']),
            skin_color=getattr(pa.SkinColor, options['skin_color']),
            top_type=getattr(pa.TopType, top),
            hair_color=getattr(pa.HairColor, options['hair_color']),
            mouth_type=getattr(pa.MouthType, options['mouth_type']),
            eye_type=getattr(pa.EyesType, options['eye_type']),
            accessories_type=getattr(pa.AccessoriesType, options['accessories_type']),
            clothe_type=getattr(pa.ClotheType, options['clothe_type'])
        )
        return avatar
    except Exception as e:
        st.error(f"Avatar Error: {str(e)}")
        return None

# --- UI Layout ---
st.markdown('<div class="main">', unsafe_allow_html=True)
st.markdown('<div class="title">🧠 PersonaGen AI</div>', unsafe_allow_html=True)

with st.form("user_form"):
    name = st.text_input("🧑 Name")
    gender = st.radio("⚧️ Gender", ["Male", "Female"], horizontal=True)
    description = st.text_area("✍️ Describe yourself...")
    submitted = st.form_submit_button("Generate")

if submitted:
    if name and description:
        with st.spinner("Analyzing..."):
            traits_raw = classify_personality_api(description)
            
            st.markdown('<div class="trait-box">', unsafe_allow_html=True)
            st.subheader(f"Results for {name}")
            plot_personality_traits(traits_raw)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
            avatar = create_avatar_by_sentence_and_gender(description, gender)
            if avatar:
                filename = f"avatar_{uuid.uuid4().hex}.png"
                avatar.render_png_file(filename)
                st.image(Image.open(filename))
                os.remove(filename) # Cleanup
            st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
