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

# 1. Page Configuration
st.set_page_config(page_title="🧠 Personality & Avatar Generator", layout="centered")

# 2. Secure API Setup (GitHub Safe)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("API Key missing! Add GOOGLE_API_KEY to Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error("Secrets not configured. Create .streamlit/secrets.toml locally.")
    st.stop()

# 3. Custom CSS for Styling
st.markdown("""
    <style>
    .main { background: linear-gradient(to right, #f0f2f6, #e0e7ff); padding: 2rem; border-radius: 15px; }
    .title { text-align: center; font-size: 2.2rem; font-weight: 700; color: #4a4a4a; }
    .avatar-box, .trait-box { 
        border-radius: 10px; padding: 1.5rem; 
        background-color: #ffffffaa; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); 
        margin-top: 20px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Gemini API Call
def classify_personality_api(sentence):
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        prompt = (
            "Analyze this text for Big Five Personality Traits. "
            "Return ONLY a clean JSON object with traits as keys and scores (0-100) as values. "
            "Traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism. "
            f"Text: {sentence}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# 5. Robust JSON Parsing & Plotting
def plot_personality_traits(traits_text):
    try:
        # Regex to find the JSON block even if there is text around it
        json_match = re.search(r'\{.*\}', traits_text, re.DOTALL)
        if not json_match:
            st.error("Could not parse traits. Try a more detailed description.")
            return None

        traits_dict = json.loads(json_match.group())
        
        # Clean data (ensure numbers)
        names = list(traits_dict.keys())
        values = [float(str(v).replace('%', '')) for v in traits_dict.values()]

        # Create Plot
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = plt.cm.viridis([i/5 for i in range(5)])
        ax.bar(names, values, color=colors)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score (0-100)")
        plt.xticks(rotation=15)
        st.pyplot(fig)
        return traits_dict
    except Exception as e:
        st.error(f"Visualization Error: {e}")
        return None

# 6. Avatar Generation Logic
def create_avatar(sentence, gender):
    try:
        s_low = sentence.lower()
        # Logic for avatar features based on description keywords
        avatar = pa.PyAvataaar(
            style=pa.AvatarStyle.CIRCLE if "calm" in s_low else pa.AvatarStyle.TRANSPARENT,
            skin_color=random.choice(list(pa.SkinColor)),
            top_type=random.choice([pa.TopType.LONG_HAIR_BOB, pa.TopType.LONG_HAIR_BUN]) if gender == "Female" 
                     else random.choice([pa.TopType.SHORT_HAIR_FRIZZLE, pa.TopType.SHORT_HAIR_SHORT_CURLY]),
            hair_color=random.choice(list(pa.HairColor)),
            mouth_type=pa.MouthType.SMILE if any(x in s_low for x in ["happy", "good", "chill"]) else pa.MouthType.DEFAULT,
            eye_type=pa.EyesType.HAPPY if "positive" in s_low else pa.EyesType.DEFAULT,
            clothe_type=pa.ClotheType.HOODIE if "relaxed" in s_low else pa.ClotheType.BLAZER_SHIRT,
        )
        return avatar
    except Exception as e:
        st.error(f"Avatar Error: {e}")
        return None

def get_image_download_link(filename):
    with open(filename, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f'<a href="data:image/png;base64,{data}" download="{filename}" style="padding: 10px; background-color: #6c5ce7; color: white; border-radius: 5px; text-decoration: none;">📥 Download Avatar</a>'

# 7. UI Layout
st.markdown('<div class="main">', unsafe_allow_html=True)
st.markdown('<div class="title">🧠 AI Personality & Avatar</div>', unsafe_allow_html=True)

with st.form("main_form"):
    name = st.text_input("🧑 Name")
    gender = st.radio("⚧️ Gender", ["Male", "Female"], horizontal=True)
    desc = st.text_area("✍️ Describe yourself...")
    submit = st.form_submit_button("Analyze & Generate")

if submit:
    if name and desc:
        with st.spinner("Processing..."):
            # Trait Analysis Section
            st.markdown('<div class="trait-box">', unsafe_allow_html=True)
            st.subheader(f"Analysis for {name}")
            raw_result = classify_personality_api(desc)
            plot_personality_traits(raw_result)
            st.markdown('</div>', unsafe_allow_html=True)

            # Avatar Section
            st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
            st.subheader("Your Custom Avatar")
            my_avatar = create_avatar(desc, gender)
            if my_avatar:
                temp_name = f"{uuid.uuid4().hex}.png"
                my_avatar.render_png_file(temp_name)
                st.image(temp_name, width=250)
                st.markdown(get_image_download_link(temp_name), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please fill in all details!")

st.markdown('</div>', unsafe_allow_html=True)
