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

# --- API SETUP ---
# On Streamlit Cloud: Add GOOGLE_API_KEY to Settings > Secrets
# Locally: Create .streamlit/secrets.toml and add GOOGLE_API_KEY = "your_key"
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception:
    st.error("API Key not found. Please set GOOGLE_API_KEY in Streamlit Secrets.")
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .main { background: linear-gradient(to right, #f0f2f6, #e0e7ff); padding: 2rem; border-radius: 15px; }
    .title { text-align: center; font-size: 2.2rem; font-weight: 700; color: #4a4a4a; }
    .subtitle { text-align: center; font-size: 1.1rem; color: #6b6b6b; }
    .avatar-box, .trait-box { border-radius: 10px; padding: 1rem; background-color: #ffffffaa; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

def classify_personality_api(sentence):
    try:
        # Note: Use gemini-1.5-flash as 2.5 does not exist yet
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        prompt = (
        "Analyze the following text and evaluate the author's personality using the Big Five model."
        "Provide scores from 0 to 100 for each trait."
        f"Text: {text}"
        "Return ONLY a flat JSON object:"
        f"{{"Openness": 50, "Conscientiousness": 50, "Extraversion": 50, "Agreeableness": 50, "Neuroticism": 50}}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def plot_personality_traits(traits_text):
    try:
        # Clean the response: remove markdown code blocks
        cleaned = re.sub(r'```json|```', '', traits_text).strip()
        
        # Find the JSON structure
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if not json_match:
            st.warning("Could not parse traits. Try a more detailed description.")
            return

        traits_dict = json.loads(json_match.group())

        # Ensure we only plot valid numeric data
        names = list(traits_dict.keys())
        values = [float(v) for v in traits_dict.values()]

        fig, ax = plt.subplots(figsize=(8, 4))
        colors = plt.cm.Paired(range(len(names)))
        ax.bar(names, values, color=colors)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score")
        ax.set_title("Big Five Personality Profile")
        plt.xticks(rotation=15)
        st.pyplot(fig)
        return traits_dict # Return for text display if needed

    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        return None

def create_avatar_by_sentence_and_gender(sentence, gender):
    try:
        s_low = sentence.lower()
        options = {
            'style': 'CIRCLE' if "calm" in s_low else 'TRANSPARENT',
            'skin_color': random.choice(list(pa.SkinColor)),
            'hair_color': random.choice(list(pa.HairColor)),
            'mouth_type': pa.MouthType.SMILE if any(x in s_low for x in ["happy", "calm", "social"]) else pa.MouthType.DEFAULT,
            'eye_type': pa.EyesType.HAPPY if any(x in s_low for x in ["positive", "calm", "open"]) else pa.EyesType.DEFAULT,
            'eyebrow_type': random.choice(list(pa.EyebrowType)),
            'accessories_type': pa.AccessoriesType.SUNGLASSES if "cool" in s_low else pa.AccessoriesType.DEFAULT,
            'clothe_type': pa.ClotheType.HOODIE if "relaxed" in s_low else pa.ClotheType.BLAZER_SHIRT,
            'clothe_graphic_type': random.choice(list(pa.ClotheGraphicType))
        }

        if gender == "Female":
            top = random.choice([pa.TopType.LONG_HAIR_BOB, pa.TopType.LONG_HAIR_BUN, pa.TopType.LONG_HAIR_CURVY])
        else:
            top = random.choice([pa.TopType.SHORT_HAIR_FRIZZLE, pa.TopType.SHORT_HAIR_SHORT_CURLY, pa.TopType.SHORT_HAIR_SHAGGY_MULLET])

        avatar = pa.PyAvataaar(
            style=options['style'] if isinstance(options['style'], pa.AvatarStyle) else getattr(pa.AvatarStyle, options['style']),
            skin_color=options['skin_color'],
            top_type=top,
            hair_color=options['hair_color'],
            mouth_type=options['mouth_type'],
            eye_type=options['eye_type'],
            eyebrow_type=options['eyebrow_type'],
            accessories_type=options['accessories_type'],
            clothe_type=options['clothe_type'],
            clothe_graphic_type=options['clothe_graphic_type']
        )
        return avatar
    except Exception as e:
        st.error(f"Avatar generation failed: {e}")
        return None

def imagedownload(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            return f'<a href="data:image/png;base64,{b64}" download="{filename}" style="text-decoration:none; background-color:#6c5ce7; color:white; padding:10px 20px; border-radius:5px;">📥 Download Avatar</a>'
    return ""

# --- UI ---
st.markdown('<div class="main">', unsafe_allow_html=True)
st.markdown('<div class="title">🧠 Personality Classifier & 🎭 Avatar</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Describe your personality and let AI visualize you!</div><br>', unsafe_allow_html=True)

with st.form("user_form"):
    col1, col2 = st.columns(2)
    name = col1.text_input("🧑 Your Name", placeholder="e.g. Alex")
    gender = col2.radio("⚧️ Gender", ["Male", "Female"], horizontal=True)
    description = st.text_area("✍️ Describe yourself (hobbies, mood, vibes)...")
    submitted = st.form_submit_button("🔍 Analyze & Generate")

if submitted:
    if not name or not description:
        st.warning("Please fill in all fields.")
    else:
        with st.spinner("Analyzing traits..."):
            raw_traits = classify_personality_api(description)
            
            st.markdown('<div class="trait-box">', unsafe_allow_html=True)
            st.subheader(f"📊 Insights for {name}")
            parsed_data = plot_personality_traits(raw_traits)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
            st.subheader("🎭 Your Avatar")
            avatar = create_avatar_by_sentence_and_gender(description, gender)
            if avatar:
                fname = f"avatar_{uuid.uuid4().hex}.png"
                avatar.render_png_file(fname)
                st.image(fname, width=250)
                st.markdown(imagedownload(fname), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
