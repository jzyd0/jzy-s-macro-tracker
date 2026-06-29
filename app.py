import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
from pydantic import BaseModel, Field

# -------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="AI Macro Tracker", page_icon="🍗", layout="centered")

# Replace with your actual Gemini API key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" 

# Initialize the Gemini Client
@st.cache_resource
def get_ai_client():
    return genai.Client(api_key=GEMINI_API_KEY)

client = get_ai_client()

# -------------------------------------------------------------------------
# 2. DEFINE THE STRUCTURED OUTPUT (Pydantic Model)
# -------------------------------------------------------------------------
class FoodItem(BaseModel):
    name: str = Field(description="Name of the food item")
    estimated_weight_g: int = Field(description="Estimated weight of the item in grams")
    protein: int = Field(description="Protein in grams")
    carbs: int = Field(description="Total carbohydrates in grams")
    fats: int = Field(description="Total fats in grams")
    calories: int = Field(description="Total calories for this item")

class MealAnalysis(BaseModel):
    food_items: list[FoodItem] = Field(description="List of individual food items identified")
    total_protein: int = Field(description="Sum of all protein")
    total_carbs: int = Field(description="Sum of all carbohydrates")
    total_fats: int = Field(description="Sum of all fats")
    total_calories: int = Field(description="Sum of all calories")

# -------------------------------------------------------------------------
# 3. STREAMLINED MOBILE INTERFACE
# -------------------------------------------------------------------------
st.title("📸 AI Macro Tracker")

img_file = None

# Placed first: Forces mobile browsers to immediately offer camera activation
camera_file = st.camera_input("📸 Snap a live photo of your plate")
if camera_file:
    img_file = camera_file

# Placed second: A clean separator and the local device gallery uploader
st.write("---")
uploaded_file = st.file_uploader("📁 Or choose an existing photo from your device", type=["jpg", "jpeg", "png"])
if uploaded_file and not camera_file:
    img_file = uploaded_file

# -------------------------------------------------------------------------
# 4. PROCESSING THE IMAGE
# -------------------------------------------------------------------------
if img_file is not None:
    image = Image.open(img_file)
    
    # Show preview if it's a file uploaded from the local device
    if img_file == uploaded_file:
        st.image(image, caption="Uploaded Meal", use_container_width=True)
        
    st.subheader("Analyzing your meal... 🍳")
    
    prompt_instruction = """
    You are an expert sports nutritionist and bodybuilding coach. Analyze the meal in the image.
    1. Identify each distinct food item.
    2. Estimate its weight in grams based on visual volume and proportions.
    3. Calculate the protein, carbs, fats, and calories for each item and the total meal.
    Be realistic with your estimations, keeping in mind standard portion sizes for active individuals.
    """

    with st.spinner("AI is calculating macros..."):
        try:
            # Call Gemini 1.5 Flash
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[image, prompt_instruction],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MealAnalysis,
                    temperature=0.2,
                ),
            )
            
            meal_data = json.loads(response.text)
            
            # -------------------------------------------------------------------------
            # 5. DISPLAY RESULTS
            # -------------------------------------------------------------------------
            st.success("Analysis Complete!")
            
            # Summary Cards
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Calories", f"{meal_data['total_calories']} kcal")
            col2.metric("Protein", f"{meal_data['total_protein']}g")
            col3.metric("Carbs", f"{meal_data['total_carbs']}g")
            col4.metric("Fats", f"{meal_data['total_fats']}g")
            
            # Food Breakdown Table
            st.write("### 🔍 Food Item Breakdown")
            items_list = []
            for item in meal_data['food_items']:
                items_list.append({
                    "Food Item": item['name'],
                    "Est. Weight": f"{item['estimated_weight_g']}g",
                    "Protein": f"{item['protein']}g",
                    "Carbs": f"{item['carbs']}g",
                    "Fats": f"{item['fats']}g",
                    "Calories": f"{item['calories']} kcal"
                })
            st.table(items_list)
            
            st.caption("⚠️ Note: AI estimates are based on visual volume. Hidden cooking oils or exact meat densities may vary.")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
