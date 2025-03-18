import streamlit as st
import openai
import requests
from datetime import datetime

# Securely load API keys using Streamlit secrets.
openai.api_key = st.secrets["openai"]["api_key"]
zapier_webhook_url = st.secrets["zapier"]["webhook_url"]

# Set up the page configuration.
st.set_page_config(page_title="Instant PCOS Risk Analyzer", layout="centered")

# App Title and Subtitle.
st.title("Instant PCOS Risk Analyzer")
st.subheader("Powered by AI")
st.write("Welcome! Let's begin your PCOS screening. Please answer the following questions:")

# -----------------------------
# PCOS Screening Questions.
# -----------------------------
cycle_regularity = st.radio(
    "1. How regular is your menstrual cycle?",
    ("Regular", "Occasionally irregular", "Mostly irregular")
)

excess_hair = st.radio(
    "2. Do you experience excess facial or body hair?",
    ("None", "Mild", "Significant")
)

weight_gain = st.radio(
    "3. How difficult is it for you to manage weight gain?",
    ("None", "Moderate", "Severe")
)

acne_skin = st.radio(
    "4. Do you experience acne or other skin issues?",
    ("None", "Mild", "Severe")
)

mood_swings = st.radio(
    "5. How often do you experience mood swings or anxiety?",
    ("Rare", "Occasionally", "Frequent")
)

physical_activity = st.radio(
    "6. How much physical activity do you engage in per week?",
    ("<1 hr", "1-3 hrs", ">3 hrs")
)

# -----------------------------
# Helper Functions.
# -----------------------------
def calculate_pcos_score():
    score = 0
    # Cycle Regularity.
    if cycle_regularity == "Regular":
        score += 0
    elif cycle_regularity == "Occasionally irregular":
        score += 1
    elif cycle_regularity == "Mostly irregular":
        score += 2

    # Excess Facial/Body Hair.
    if excess_hair == "None":
        score += 0
    elif excess_hair == "Mild":
        score += 1
    elif excess_hair == "Significant":
        score += 2

    # Weight Gain Difficulty.
    if weight_gain == "None":
        score += 0
    elif weight_gain == "Moderate":
        score += 1
    elif weight_gain == "Severe":
        score += 2

    # Acne or Skin Issues.
    if acne_skin == "None":
        score += 0
    elif acne_skin == "Mild":
        score += 1
    elif acne_skin == "Severe":
        score += 2

    # Mood Swings or Anxiety.
    if mood_swings == "Rare":
        score += 0
    elif mood_swings == "Occasionally":
        score += 1
    elif mood_swings == "Frequent":
        score += 2

    # Physical Activity (less activity = higher risk).
    if physical_activity == "<1 hr":
        score += 2
    elif physical_activity == "1-3 hrs":
        score += 1
    elif physical_activity == ">3 hrs":
        score += 0

    return score

def get_risk_category(score):
    if score <= 3:
        return "Low Risk"
    elif 4 <= score <= 7:
        return "Moderate Risk"
    else:
        return "High Risk"

def get_pcos_report(score, responses):
    prompt = f"""
Based on the following PCOS screening responses:
- Cycle Regularity: {responses['Cycle Regularity']}
- Excess Facial/Body Hair: {responses['Excess Facial/Body Hair']}
- Weight Gain Difficulty: {responses['Weight Gain Difficulty']}
- Acne or Skin Issues: {responses['Acne or Skin Issues']}
- Mood Swings or Anxiety: {responses['Mood Swings or Anxiety']}
- Physical Activity per Week: {responses['Physical Activity per Week']}

The total risk score is {score}, which indicates a {get_risk_category(score)}.
Please provide a concise, personalized, and detailed PCOS Risk Analysis report with actionable recommendations for lifestyle modifications, potential treatments, and guidance for further medical consultation.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Change to "gpt-4" if available.
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing health-related insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        # Use dictionary indexing to access the report content.
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating report: {e}"

# -----------------------------
# Process PCOS Screening Submission.
# -----------------------------
if st.button("Submit"):
    total_score = calculate_pcos_score()
    risk_category = get_risk_category(total_score)
    responses = {
        "Cycle Regularity": cycle_regularity,
        "Excess Facial/Body Hair": excess_hair,
        "Weight Gain Difficulty": weight_gain,
        "Acne or Skin Issues": acne_skin,
        "Mood Swings or Anxiety": mood_swings,
        "Physical Activity per Week": physical_activity
    }
    pcos_report = get_pcos_report(total_score, responses)

    # Save key data in session state.
    st.session_state["total_score"] = total_score
    st.session_state["risk_category"] = risk_category
    st.session_state["responses"] = responses
    st.session_state["pcos_report"] = pcos_report

# -----------------------------
# Display Report & Demographic Data Capture Form.
# -----------------------------
if "pcos_report" in st.session_state:
    st.write("---")
    st.write("### Your PCOS Risk Analysis Report:")
    st.write("**Total Score:**", st.session_state["total_score"])
    st.write("**Risk Level:**", st.session_state["risk_category"])
    st.write(st.session_state["pcos_report"])
    
    st.write("---")
    st.write("#### Optional: Save your responses for follow-up")
    
    with st.form(key="demographic_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone Number (Indian format)")
        email = st.text_input("Email Address")
        submit_demo = st.form_submit_button("Save Response")
        
        if submit_demo:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "name": name,
                "phone": phone,
                "email": email,
                "cycle_regularity": st.session_state["responses"]["Cycle Regularity"],
                "excess_hair": st.session_state["responses"]["Excess Facial/Body Hair"],
                "weight_gain": st.session_state["responses"]["Weight Gain Difficulty"],
                "acne_skin": st.session_state["responses"]["Acne or Skin Issues"],
                "mood_swings": st.session_state["responses"]["Mood Swings or Anxiety"],
                "physical_activity": st.session_state["responses"]["Physical Activity per Week"],
                "total_score": st.session_state["total_score"],
                "risk_category": st.session_state["risk_category"],
                "pcos_report": st.session_state["pcos_report"]
            }
            try:
                res = requests.post(zapier_webhook_url, json=payload)
                if res.status_code == 200:
                    st.success("Your response has been saved successfully!")
                else:
                    st.error("Error saving your response. Please try again later.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
