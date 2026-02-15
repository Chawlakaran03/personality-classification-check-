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
import sqlite3
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="PersonaGen AI", layout="wide", page_icon="🧠")

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('personality_db.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            gender TEXT,
            openness REAL,
            conscientiousness REAL,
            extraversion REAL,
            agreeableness REAL,
            neuroticism REAL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_entry(name, gender, traits, description):
    conn = sqlite3.connect('personality_db.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO entries 
        (name, gender, openness, conscientiousness, extraversion, agreeableness, neuroticism, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, gender, traits['Openness'], traits['Conscientiousness'], 
          traits['Extraversion'], traits['Agreeableness'], traits['Neuroticism'], description))
    conn.commit()
    conn.close()

# Initialize DB at startup
init_db()

# --- API SETUP ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

# --- HELPER FUNCTIONS (Personality & Avatar) ---
def get_personality_analysis(text):
    try:
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
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

def build_avatar(traits, gender):
    # (Existing avatar logic remains the same)
    return pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        top_type=pa.TopType.SHORT_HAIR_SHORT_FLAT if gender=="Male" else pa.TopType.LONG_HAIR_BOB,
        mouth_type=pa.MouthType.SMILE if traits.get('Agreeableness', 50) > 50 else pa.MouthType.DEFAULT,
        eye_type=pa.EyesType.HAPPY if traits.get('Extraversion', 50) > 50 else pa.EyesType.DEFAULT,
        skin_color=random.choice(list(pa.SkinColor)),
        clothe_type=pa.ClotheType.BLAZER_SHIRT if traits.get('Conscientiousness', 50) > 70 else pa.ClotheType.HOODIE
    )

# --- UI INTERFACE ---
st.title("🧠 Persona-to-Avatar Generator")

# --- SIDEBAR ADMIN PANEL ---
with st.sidebar:
    st.header("👤 User Info")
    user_name = st.text_input("Name", "User")
    user_gender = st.selectbox("Gender", ["Male", "Female"])
    
    st.divider()
    
    # Hidden Admin Section
    with st.expander("🔐 Admin Dashboard"):
        password = st.text_input("Admin Password", type="password")
        if password == "admin123": # Change this password!
            st.success("Access Granted")
            conn = sqlite3.connect('personality_db.db')
            df = pd.read_sql_query("SELECT * FROM entries ORDER BY id ASC", conn)
            conn.close()
            st.dataframe(df)
            
            # Option to download data
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", csv, "user_data.csv", "text/csv")
        elif password:
            st.error("Wrong Password")

# --- MAIN APP LOGIC ---
user_input = st.text_area("Tell us about yourself:", height=150)

if st.button("Generate My Vibe 🚀", use_container_width=True):
    if not user_input.strip():
        st.warning("Please enter a description.")
    else:
        with st.spinner("Analyzing and saving data..."):
            traits = get_personality_analysis(user_input)
            
            if traits:
                # SAVE TO DATABASE
                save_entry(user_name, user_gender, traits, user_input)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("📊 Personality Profile")
                    fig, ax = plt.subplots()
                    ax.barh(list(traits.keys()), list(traits.values()), color='#6c5ce7')
                    ax.set_xlim(0, 100)
                    st.pyplot(fig)
                
                with col2:
                    st.subheader("🎭 Your Avatar")
                    avatar = build_avatar(traits, user_gender)
                    filename = f"avatar_{uuid.uuid4().hex}.png"
                    avatar.render_png_file(filename)
                    st.image(filename, width=300)
                    os.remove(filename)
