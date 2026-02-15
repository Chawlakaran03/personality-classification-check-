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
st.set_page_config(page_title="PersonaGen AI", layout="wide")

# Replace with your actual key or use st.secrets
API_KEY = "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE"

if API_KEY != "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE" :
    genai.configure(api_key=API_KEY)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTextArea textarea { font-size: 1.1rem !important; }
    .stat-box {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def get_personality_analysis(text):
    """Fetches Big Five scores from Gemini."""
    if API_KEY == "AIzaSyBv1rh97bKNEfVaaPGWyIZ9HhCX7RkBMeE":
        st.error("Please provide a valid Gemini API Key in the code.")
        return None
        
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        Analyze the following text and evaluate the author's personality using the Big Five model.
        Provide scores from 0 to 100.
        Text: "{text}"
        Return ONLY a JSON object:
        {{"Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "Neuroticism": 0}}
        """
        response = model.generate_content(prompt)
        # Clean JSON string
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Analysis Error: {e}")
        return None

def build_avatar(traits, gender):
    """Converts personality scores into visual avatar components."""
    # Mapping logic
    options = {}
    
    # 1. Eyes & Expressions (Neuroticism & Agreeableness)
    if traits['Neuroticism'] > 70:
        options['eye_type'] = pa.EyesType.WORRIED
        options['mouth_type'] = pa.MouthType.SAD
    elif traits['Agreeableness'] > 60:
        options['eye_type'] = pa.EyesType.HAPPY
        options['mouth_type'] = pa.MouthType.SMILE
    else:
        options['eye_type'] = pa.EyesType.DEFAULT
        options['mouth_type'] = pa.MouthType.DEFAULT

    # 2. Clothing (Conscientiousness & Openness)
    if traits['Conscientiousness'] > 75:
        options['clothe_type'] = pa.ClotheType.BLAZER_SHIRT
    elif traits['Openness'] > 70:
        options['clothe_type'] = pa.ClotheType.GRAPHIC_SHIRT
    else:
        options['clothe_type'] = pa.ClotheType.HOODIE

    # 3. Hair based on Gender
    if gender == "Female":
        options['top_type'] = pa.TopType.LONG_HAIR_CURVY if traits['Openness'] > 50 else pa.TopType.LONG_HAIR_BOB
    else:
        options['top_type'] = pa.TopType.SHORT_HAIR_SHORT_FLAT if traits['Conscientiousness'] > 50 else pa.TopType.SHORT_HAIR_FRIZZLE

    # 4. Accessories
    options['accessories_type'] = pa.AccessoriesType.PRESCRIPTION_02 if traits['Openness'] > 80 else pa.AccessoriesType.DEFAULT

    return pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        top_type=options['top_type'],
        eyebrow_type=pa.EyebrowType.DEFAULT,
        eye_type=options['eye_type'],
        mouth_type=options['mouth_type'],
        clothe_type=options['clothe_type'],
        accessories_type=options['accessories_type'],
        skin_color=random.choice(list(pa.SkinColor)),
        hair_color=random.choice(list(pa.HairColor))
    )

# --- UI INTERFACE ---

st.title("🧠 Persona-to-Avatar Generator")
st.write("Write a paragraph about yourself. Our AI will analyze your personality and build an avatar that matches your 'vibe'.")

with st.sidebar:
    st.header("User Details")
    user_name = st.text_input("Name", "User")
    user_gender = st.selectbox("Gender Preference", ["Male", "Female"])
    st.info("The avatar's expression and outfit are driven by your personality scores.")

user_input = st.text_area("Describe yourself (e.g., 'I am a highly organized software engineer who loves painting and traveling, but I get stressed during deadlines'):", height=150)

if st.button("Generate Avatar 🚀"):
    if not user_input.strip():
        st.warning("Please enter some text description.")
    else:
        with st.spinner("Analyzing traits..."):
            traits = get_personality_analysis(user_input)
            
            if traits:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("Personality Profile")
                    # Horizontal Bar Chart
                    fig, ax = plt.subplots()
                    names = list(traits.keys())
                    values = list(traits.values())
                    ax.barh(names, values, color='#6c5ce7')
                    ax.set_xlim(0, 100)
                    st.pyplot(fig)
                    st.json(traits)

                with col2:
                    st.subheader(f"Generated Avatar for {user_name}")
                    avatar = build_avatar(traits, user_gender)
                    
                    # Generate unique file to avoid caching issues
                    filename = f"{uuid.uuid4()}.png"
                    avatar.render_png_file(filename)
                    
                    st.image(filename, width=300)
                    
                    with open(filename, "rb") as file:
                        st.download_button("Download Image", file, "my_avatar.png", "image/png")
                    
                    # Clean up
                    if os.path.exists(filename):
                        os.remove(filename)
