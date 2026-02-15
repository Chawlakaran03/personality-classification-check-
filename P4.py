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

# --- API SETUP (Using Secrets) ---
# Local: .streamlit/secrets.toml mein GEMINI_API_KEY daalna
# Cloud: Streamlit dashboard ke secrets mein GEMINI_API_KEY daalna
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
else:
    st.error("❌ API Key missing! Please add 'GEMINI_API_KEY' to your Streamlit Secrets.")
    st.stop()

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
    """Fetches Big Five scores from Gemini."""
    try:
        # 1.5-flash is stable and free
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        Act as an expert Psychometrician and Linguistic Analyst. 
        Analyze the following text provided by a user to determine their scores across the Big Five Personality Traits (OCEAN model):

        User Text: "{text}"

        Your goal is to infer personality characteristics based on word choice, tone, and sentence structure. 
        Provide a score from 0 to 100 for each of the following:
        1. Openness: (Curiosity, imagination, and willingness to try new things).
        2. Conscientiousness: (Organization, dependability, and discipline).
        3. Extraversion: (Sociability, energy, and outgoingness).
        4. Agreeableness: (Trust, kindness, and cooperation).
        5. Neuroticism: (Emotional sensitivity and tendency toward stress).

        STRICT OUTPUT RULES:
        - Return ONLY a valid, flat JSON object.
        - Do NOT include any conversational text, markdown formatting (no ```json blocks), or explanations.
        - Use this exact structure:
        {{"Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "Neuroticism": 0}}
         """
        
        response = model.generate_content(prompt)
        
        # JSON Cleaning
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {k: float(v) for k, v in data.items()}
        return None
    except Exception as e:
        st.error(f"Analysis Error: {e}")
        return None

def build_avatar(traits, gender):
    """Maps Big Five traits to visual components."""
    options = {}
    
    # Logic: Agreeableness/Neuroticism -> Expression
    if traits.get('Neuroticism', 0) > 70:
        eye_type, mouth_type = pa.EyesType.WORRIED, pa.MouthType.SAD
    elif traits.get('Agreeableness', 0) > 60:
        eye_type, mouth_type = pa.EyesType.HAPPY, pa.MouthType.SMILE
    else:
        eye_type, mouth_type = pa.EyesType.DEFAULT, pa.MouthType.DEFAULT

    # Logic: Conscientiousness/Openness -> Outfit
    if traits.get('Conscientiousness', 0) > 75:
        clothe_type = pa.ClotheType.BLAZER_SHIRT
    elif traits.get('Openness', 0) > 70:
        clothe_type = pa.ClotheType.GRAPHIC_SHIRT
    else:
        clothe_type = pa.ClotheType.HOODIE

    # Hair Logic
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
        skin_color=random.choice(list(pa.SkinColor)),
        hair_color=random.choice(list(pa.HairColor))
    )

# --- UI INTERFACE ---

st.title("🧠 Persona-to-Avatar Generator")
st.write("Write about yourself and watch AI build your digital twin.")

with st.sidebar:
    st.header("👤 User Details")
    user_name = st.text_input("Name", "User")
    user_gender = st.selectbox("Gender", ["Male", "Female"])
    st.divider()
    st.info("The avatar's mood and outfit adapt to your Big Five personality scores.")

user_input = st.text_area("Tell us about yourself:", height=150, placeholder="I love exploring new places and keep my workspace very neat...")

if st.button("Generate My Avatar 🚀", use_container_width=True):
    if not user_input.strip():
        st.warning("Please enter a description.")
    else:
        with st.spinner("Analyzing personality..."):
            traits = get_personality_analysis(user_input)
            
            if traits:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Personality Profile")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    names = list(traits.keys())
                    values = list(traits.values())
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
                    
                    ax.barh(names, values, color=colors)
                    ax.set_xlim(0, 100)
                    ax.set_title(f"Big Five Scores for {user_name}")
                    st.pyplot(fig)
                    st.json(traits)

                with col2:
                    st.subheader("🎭 Your Custom Avatar")
                    avatar = build_avatar(traits, user_gender)
                    
                    filename = f"avatar_{uuid.uuid4().hex}.png"
                    avatar.render_png_file(filename)
                    
                    st.image(filename, width=350)
                    
                    with open(filename, "rb") as file:
                        st.download_button("📥 Download Avatar", file, f"{user_name}_avatar.png", "image/png")
                    
                    if os.path.exists(filename):
                        os.remove(filename)
                st.markdown('</div>', unsafe_allow_html=True)
