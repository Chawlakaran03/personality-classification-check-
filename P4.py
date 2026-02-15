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
# Streamlit page setup
st.set_page_config(page_title="🧠 Personality & Avatar Generator", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(to right, #f0f2f6, #e0e7ff);
        padding: 2rem;
        border-radius: 15px;
    }
    .title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        color: #4a4a4a;
    }
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #6b6b6b;
    }
    .avatar-box {
        border-radius: 10px;
        padding: 1rem;
        background-color: #ffffffaa;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .trait-box {
        border-radius: 10px;
        padding: 1rem;
        background-color: #ffffffaa;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Google Gemini API setup
GOOGLE_API_KEY = "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE"
genai.configure(api_key=GOOGLE_API_KEY)

# Gemini call for personality classification
def classify_personality_api(sentence):
    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        response = model.generate_content(
            f"Classify the following text based on the Big Five Personality Traits. "
            f"Provide a JSON-like format for the traits and their scores out of 100:\n\n{sentence}")
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Trait plot (Bar chart)
def plot_personality_traits(traits_data):
    try:
        # Check if traits_data is a string (JSON) or already a dict
        if isinstance(traits_data, str):
            # Clean markdown formatting if Gemini included it
            clean_json = re.search(r'\{.*\}', traits_data, re.DOTALL).group()
            traits_dict = json.loads(clean_json)
        else:
            traits_dict = traits_data

        # Ensure all values are numeric (sometimes AI returns strings)
        processed_traits = {k: float(v) for k, v in traits_dict.items() if k != "Error"}

        # Creating the Plot
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Use a nice color palette
        colors = ['#6c5ce7', '#00cec9', '#fab1a0', '#fd79a8', '#55efc4']
        
        keys = list(processed_traits.keys())
        values = list(processed_traits.values())

        bars = ax.bar(keys, values, color=colors[:len(keys)])
        
        # Formatting
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score (0-100)")
        ax.set_title("Big Five Personality Analysis", fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        
        # Add value labels on top of bars
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 1, int(yval), ha='center', va='bottom')

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        st.write("Raw data received:", traits_data) # Helps you debug what went wrong
# Avatar generator
def create_avatar_by_sentence_and_gender(sentence, gender):
    try:
        options = {
            'style': 'CIRCLE' if "calm" in sentence.lower() else 'TRANSPARENT',
            'skin_color': random.choice(["TANNED", "YELLOW", "PALE", "LIGHT", "BROWN", "DARK_BROWN", "BLACK"]),
            'hair_color': random.choice(["AUBURN", "BLACK", "BLONDE", "BROWN", "RED", "SILVER_GRAY"]),
            'mouth_type': "SMILE" if "happy" in sentence.lower() or "calm" in sentence.lower() else "DEFAULT",
            'eye_type': "HAPPY" if "positive" in sentence.lower() or "calm" in sentence.lower() else "DEFAULT",
            'eyebrow_type': random.choice(["DEFAULT", "RAISED_EXCITED", "FROWN_NATURAL"]),
            'accessories_type': "SUNGLASSES" if "cool" in sentence.lower() else "DEFAULT",
            'clothe_type': "HOODIE" if "relaxed" in sentence.lower() else "BLAZER_SHIRT",
            'clothe_graphic_type': random.choice(["BAT", "DIAMOND", "HOLA", "SKULL"])
        }

        options['top_type'] = random.choice([
            "LONG_HAIR_BOB", "LONG_HAIR_BUN", "LONG_HAIR_CURVY"
        ]) if gender == "Female" else random.choice([
            "SHORT_HAIR_FRIZZLE", "SHORT_HAIR_SHORT_CURLY", "SHORT_HAIR_SHAGGY_MULLET", "HAT"
        ])

        avatar = pa.PyAvataaar(
            style=getattr(pa.AvatarStyle, options['style']),
            skin_color=getattr(pa.SkinColor, options['skin_color']),
            top_type=getattr(pa.TopType, options['top_type']),
            hair_color=getattr(pa.HairColor, options['hair_color']),
            mouth_type=getattr(pa.MouthType, options['mouth_type']),
            eye_type=getattr(pa.EyesType, options['eye_type']),
            eyebrow_type=getattr(pa.EyebrowType, options['eyebrow_type']),
            accessories_type=getattr(pa.AccessoriesType, options['accessories_type']),
            clothe_type=getattr(pa.ClotheType, options['clothe_type']),
            clothe_graphic_type=getattr(pa.ClotheGraphicType, options['clothe_graphic_type'])
        )
        return avatar
    except Exception as e:
        st.error(f"Error creating avatar: {str(e)}")
        return None

# Avatar download link
def imagedownload(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as image_file:
            b64 = base64.b64encode(image_file.read()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 Download Avatar</a>'
            return href
    else:
        st.error("Image not found.")
        return ""

# -------------------------------
# Streamlit UI Layout
# -------------------------------
st.markdown('<div class="main">', unsafe_allow_html=True)
st.markdown('<div class="title">🧠 Personality Classifier & 🎭 Avatar Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Describe yourself and get personalized insights and a cool avatar!</div><br>', unsafe_allow_html=True)

with st.form("user_form"):
    col1, col2 = st.columns(2)
    name = col1.text_input("🧑 Your Name")
    gender = col2.radio("⚧️ Your Gender", ["Male", "Female"], horizontal=True)
    description = st.text_area("✍️ Tell us about your personality...")

    submitted = st.form_submit_button("🔍 Analyze & Generate")

if submitted:
    if not name or not description:
        st.warning("Please fill in both name and personality description.")
    else:
        with st.spinner("Analyzing your personality..."):
            traits = classify_personality_api(description)

        # Show traits
        st.markdown('<div class="trait-box">', unsafe_allow_html=True)
        st.subheader(f"🧠 Personality Insights for **{name}**")
        st.markdown(f"```{traits}```")
        plot_personality_traits(traits)
        st.markdown('</div><br>', unsafe_allow_html=True)

        # Show avatar
        st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
        st.subheader("🎭 Your Personalized Avatar")
        avatar = create_avatar_by_sentence_and_gender(description, gender)
        if avatar:
            unique_filename = f"avatar_{uuid.uuid4().hex}.png"
            avatar.render_png_file(unique_filename)
            image = Image.open(unique_filename)
            st.image(image, caption=f"{name}'s Avatar")
            st.markdown(imagedownload(unique_filename), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
