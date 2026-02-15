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

# Streamlit config
st.set_page_config(page_title="🧠 PersonaGen AI", layout="centered")

# API Setup
API_KEY = "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE" # Apni key yahan confirm karein
genai.configure(api_key=API_KEY)

# --- HELPER FUNCTIONS ---

def clean_and_flatten_data(raw_text):
    """AI ke response se sirf numeric data nikalne ke liye logic."""
    try:
        # 1. Regex se JSON block extract karna
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not json_match:
            return None
        
        data = json.loads(json_match.group())
        
        # 2. Agar nested dict hai toh use flatten karna
        flattened = {}
        def flatten(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    flatten(v)
                else:
                    # Sirf numbers ya numeric strings ko save karna
                    try:
                        flattened[k] = float(v)
                    except (ValueError, TypeError):
                        continue
        
        flatten(data)
        return flattened
    except Exception:
        return None

def classify_personality_api(sentence):
    try:
        # gemini-1.5-flash sabse stable hai is task ke liye
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        prompt = (f"Analyze this text for Big Five Personality Traits: '{sentence}'. "
                  f"Return ONLY a flat JSON object with scores 0-100 for: "
                  f"Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def plot_personality_traits(traits_dict):
    """Isme ab 'dict' error nahi aayegi."""
    if not traits_dict:
        st.warning("Data process nahi ho paya plotting ke liye.")
        return

    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        # Custom colors
        colors = ['#6c5ce7', '#00cec9', '#fab1a0', '#fd79a8', '#55efc4']
        
        keys = list(traits_dict.keys())
        values = list(traits_dict.values())
        
        ax.bar(keys, values, color=colors[:len(keys)])
        ax.set_ylim(0, 105)
        ax.set_title("Big Five Personality Breakdown", fontsize=12)
        plt.xticks(rotation=30)
        
        # Numbers top par show karne ke liye
        for i, v in enumerate(values):
            ax.text(i, v + 2, str(int(v)), ha='center', fontweight='bold')
            
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Visual Error: {e}")

# --- AVATAR LOGIC ---

def create_avatar(description, gender):
    try:
        # Basic logic based on description keywords
        is_happy = any(word in description.lower() for word in ["happy", "excited", "good", "great"])
        is_chill = any(word in description.lower() for word in ["chill", "calm", "relax", "organized"])
        
        avatar = pa.PyAvataaar(
            style=pa.AvatarStyle.CIRCLE,
            skin_color=random.choice(list(pa.SkinColor)),
            hair_color=random.choice(list(pa.HairColor)),
            top_type=random.choice([pa.TopType.LONG_HAIR_BOB, pa.TopType.LONG_HAIR_CURVY]) if gender == "Female" else pa.TopType.SHORT_HAIR_SHORT_FLAT,
            mouth_type=pa.MouthType.SMILE if is_happy else pa.MouthType.DEFAULT,
            eye_type=pa.EyesType.HAPPY if is_happy else pa.EyesType.DEFAULT,
            clothe_type=pa.ClotheType.BLAZER_SHIRT if is_chill else pa.ClotheType.HOODIE,
            accessories_type=pa.AccessoriesType.DEFAULT
        )
        return avatar
    except Exception as e:
        st.error(f"Avatar Logic Error: {e}")
        return None

# --- UI INTERFACE ---

st.title("🧠 Personality & Avatar Generator")
st.write("Apne baare mein likhein aur dekhein AI aapko kaise classify karta hai!")

with st.form("user_input_form"):
    name = st.text_input("Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    desc = st.text_area("Tell us about yourself (Personality, habits, etc.)")
    btn = st.form_submit_button("Generate Everything ✨")

if btn:
    if name and desc:
        with st.spinner("AI is thinking..."):
            # 1. API se data lena
            raw_response = classify_personality_api(desc)
            # 2. Flatten aur Clean karna (Error prevention)
            traits = clean_and_flatten_data(raw_response)
            
            if traits:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Your Traits")
                    plot_personality_traits(traits)
                    st.json(traits)
                
                with col2:
                    st.subheader("🎭 Your Avatar")
                    avatar = create_avatar(desc, gender)
                    if avatar:
                        path = f"avatar_{uuid.uuid4().hex}.png"
                        avatar.render_png_file(path)
                        st.image(path, width=300)
                        
                        # Download button
                        with open(path, "rb") as f:
                            st.download_button("📥 Download", f, "avatar.png", "image/png")
                        os.remove(path)
            else:
                st.error("AI Response ko parse nahi kiya ja saka. Please try again.")
    else:
        st.warning("Please fill name and description.")
