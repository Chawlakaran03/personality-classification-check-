import streamlit as st
import py_avataaars as pa
from PIL import Image
import matplotlib.pyplot as plt
import random
import uuid
import google.generativeai as genai
import json
import re
import os

# --- APP CONFIG ---
st.set_page_config(page_title="PersonaGen AI", layout="wide", page_icon="🧠")

# API Setup
API_KEY = "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE"
genai.configure(api_key=API_KEY)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTextArea textarea { font-size: 1.1rem !important; }
    .result-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def get_personality_analysis(text):
    """Fetches Big Five scores from Gemini with robust JSON cleaning."""
    try:
        # Latest stable free model
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
        Analyze the following text and evaluate the author's personality using the Big Five model.
        Provide scores from 0 to 100 for each trait.
        Text: "{text}"
        Return ONLY a flat JSON object like this:
        {{"Openness": 50, "Conscientiousness": 50, "Extraversion": 50, "Agreeableness": 50, "Neuroticism": 50}}
        """
        
        response = model.generate_content(prompt)
        
        # JSON Extracting logic (agar AI markdown blocks use kare tab bhi chalega)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            # Ensure all values are floats/ints
            return {k: float(v) for k, v in data.items()}
        return None
    except Exception as e:
        st.error(f"Analysis Error: {e}")
        return None

def build_avatar(traits, gender):
    """Maps Big Five traits to visual avatar components."""
    # Logic mapping
    # 1. Emotions
    if traits.get('Neuroticism', 0) > 70:
        eye_type, mouth_type = pa.EyesType.WORRIED, pa.MouthType.SAD
    elif traits.get('Agreeableness', 0) > 60:
        eye_type, mouth_type = pa.EyesType.HAPPY, pa.MouthType.SMILE
    else:
        eye_type, mouth_type = pa.EyesType.DEFAULT, pa.MouthType.DEFAULT

    # 2. Outfit
    if traits.get('Conscientiousness', 0) > 75:
        clothe_type = pa.ClotheType.BLAZER_SHIRT
    elif traits.get('Openness', 0) > 70:
        clothe_type = pa.ClotheType.GRAPHIC_SHIRT
    else:
        clothe_type = pa.ClotheType.HOODIE

    # 3. Style based on Openness
    acc_type = pa.AccessoriesType.PRESCRIPTION_02 if traits.get('Openness', 0) > 80 else pa.AccessoriesType.DEFAULT

    # 4. Gendered Hair
    if gender == "Female":
        top_type = pa.TopType.LONG_HAIR_CURVY if traits.get('Extraversion', 0) > 60 else pa.TopType.LONG_HAIR_BOB
    else:
        top_type = pa.TopType.SHORT_HAIR_FRIZZLE if traits.get('Extraversion', 0) > 60 else pa.TopType.SHORT_HAIR_SHORT_FLAT

    return pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        top_type=top_type,
        eye_type=eye_type,
        mouth_type=mouth_type,
        clothe_type=clothe_type,
        accessories_type=acc_type,
        skin_color=random.choice(list(pa.SkinColor)),
        hair_color=random.choice(list(pa.HairColor))
    )

# --- UI INTERFACE ---

st.title("🧠 Persona-to-Avatar Generator")
st.write("Apne baare mein likho aur AI aapka personality avatar create karega.")

with st.sidebar:
    st.header("👤 User Info")
    user_name = st.text_input("Name", "User")
    user_gender = st.selectbox("Gender", ["Male", "Female"])
    st.divider()
    st.info("Avatar ke expressions aur kapde aapke 'Big Five' scores par base hain.")

user_input = st.text_area("Tell us about yourself (Hobbies, work style, feelings):", height=150)

if st.button("Generate My Vibe 🚀", use_container_width=True):
    if not user_input.strip():
        st.warning("Pehle kuch likho toh sahi, bro!")
    else:
        with st.spinner("AI is analyzing your DNA (well, your text)..."):
            traits = get_personality_analysis(user_input)
            
            if traits:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Personality Profile")
                    # Chart formatting
                    fig, ax = plt.subplots(figsize=(10, 6))
                    names = list(traits.keys())
                    values = list(traits.values())
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
                    
                    ax.barh(names, values, color=colors)
                    ax.set_xlim(0, 100)
                    ax.set_title(f"{user_name}'s Big Five Scores")
                    st.pyplot(fig)
                    st.json(traits)

                with col2:
                    st.subheader("🎭 Your Avatar")
                    avatar = build_avatar(traits, user_gender)
                    
                    filename = f"avatar_{uuid.uuid4().hex}.png"
                    avatar.render_png_file(filename)
                    
                    st.image(filename, width=350)
                    
                    with open(filename, "rb") as file:
                        st.download_button("📥 Download Avatar", file, f"{user_name}_avatar.png", "image/png")
                    
                    if os.path.exists(filename):
                        os.remove(filename)
                st.markdown('</div>', unsafe_allow_html=True)
