from flask import Flask, render_template, request, jsonify
import os
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv() # .env

os.environ['TF_USE_LEGACY_KERAS'] = '1'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

#Load model
model = tf.keras.models.load_model('plant_model.h5', compile=False)

CLASSES = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy', 
    'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy', 
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_', 
    'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Corn___Common_Rust', 
    'Corn___Gray_Leaf_Spot', 'Corn___Healthy', 'Corn___Northern_Leaf_Blight', 'Grape___Black_rot', 
    'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy', 
    'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy', 
    'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_Blight', 
    'Potato___Early_blight', 'Potato___Healthy', 'Potato___Late_Blight', 'Potato___Late_blight', 
    'Potato___healthy', 'Raspberry___healthy', 'Rice___Brown_Spot', 'Rice___Healthy', 
    'Rice___Leaf_Blast', 'Rice___Neck_Blast', 'Soybean___healthy', 'Squash___Powdery_mildew', 
    'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Sugarcane_Bacterial Blight', 
    'Sugarcane_Healthy', 'Sugarcane_Red Rot', 'Tomato___Bacterial_spot', 'Tomato___Early_blight', 
    'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 
    'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot', 
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 
    'Tomato___healthy', 'Wheat___Brown_Rust', 'Wheat___Healthy', 'Wheat___Yellow_Rust'
]

# API
genai.configure(api_key=os.getenv("GEMINI_KEY_1"))
genai.configure(api_key=os.getenv("GEMINI_KEY_2"))
gemini_model_1 = genai.GenerativeModel('gemini-2.5-flash')
gemini_model_2 = genai.GenerativeModel('gemini-2.5-flash')


#Route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/advisor')
def advisor():
    return render_template('advisor.html')

@app.route('/doctor')
def doctor():
    return render_template('doctor.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # computer vision
    img = image.load_img(filepath, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)
    result_index = np.argmax(predictions)
    confidence = np.max(predictions) * 100
    
    disease_name = CLASSES[result_index].replace('___', ' - ').replace('_', ' ')

    if confidence < 94:
        return jsonify({
            'error': "This doesn't look like a plant leaf. Please upload a clear photo of the leaf itself."
        })

    # llm
    organic_en, chemical_en = "", ""
    organic_mr, chemical_mr = "", ""

    if "healthy" in disease_name.lower():
        organic_en = "Your plant looks healthy! Maintain regular watering and sunlight."
        chemical_en = "No chemical treatment required for a healthy plant."
        organic_mr = "तुमचे रोप निरोगी दिसत आहे! नियमित पाणी आणि सूर्यप्रकाश द्या."
        chemical_mr = "निरोगी रोपासाठी कोणत्याही रासायनिक उपचारांची गरज नाही."
    else:
        try:
            prompt = f"""
            Expert Agricultural AI. Disease: {disease_name}. 
            Provide exactly 4 lines as follows:
            ENG_ORG: [English Organic advice]
            ENG_CHEM: [English Chemical advice]
            MAR_ORG: [Marathi Organic translation]
            MAR_CHEM: [Marathi Chemical translation]
            """
            
            response = gemini_model_1.generate_content(prompt)
            text = response.text

            def extract(label, full_text):
                import re
                pattern = rf"{label}\s*(.*?)(?=ENG_ORG|ENG_CHEM|MAR_ORG|MAR_CHEM|$)"
                match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
                return match.group(1).strip().replace('*', '') if match else "Advice pending..."

            organic_en = extract("ENG_ORG:", text)
            chemical_en = extract("ENG_CHEM:", text)
            organic_mr = extract("MAR_ORG:", text)
            chemical_mr = extract("MAR_CHEM:", text)

        except Exception as e:
            print(f"GEMINI EXTRACTION FAILED: {e}")
            organic_en, chemical_en = "Remove infected leaves.", "Use fungicide."
            organic_mr, chemical_mr = "बाधित पाने काढून टाका.", "बुरशीनाशक वापरा."
    return jsonify({
        'disease': disease_name,
        'confidence': f"{confidence:.2f}%",
        'organic_en': organic_en,
        'chemical_en': chemical_en,
        'organic_mr': organic_mr,
        'chemical_mr': chemical_mr,
    })

@app.route('/schemes')
def schemes():
    active_schemes = [
        {
            "name": "PM-KISAN Samman Nidhi",
            "benefit": "₹6,000 per year (3 installments of ₹2,000)",
            "status": "22nd Installment released in March 2026",
            "link": "https://pmkisan.gov.in/",
            "type": "Central Govt"
        },
        {
            "name": "Namo Shetkari Mahasanman Nidhi",
            "benefit": "Additional ₹6,000 per year for Maharashtra farmers",
            "status": "8th Installment released March 25, 2026",
            "link": "https://nsmny.mahait.org/",
            "type": "Maharashtra Govt"
        },
        {
            "name": "PM Fasal Bima Yojana (PMFBY)",
            "benefit": "Comprehensive crop insurance at 1.5% - 2% premium",
            "status": "Enrollment open for Kharif 2026",
            "link": "https://pmfby.gov.in/",
            "type": "Insurance"
        },
        {
            "name": "Magel Tyala Shettale",
            "benefit": "Subsidy of ₹50,000 for building farm ponds",
            "status": "Active - Apply via MahaDBT portal",
            "link": "https://mahadbt.maharashtra.gov.in/",
            "type": "Maharashtra Govt"
        }
    ]
    return render_template('schemes.html', schemes=active_schemes)

@app.route('/get_advice', methods=['POST'])
def get_advice():
    try:
        data = request.get_json()
        soil = data.get('soil', 'Black Soil')
        water = data.get('water', 'Drip')
        season = data.get('season', 'Zaid/Summer')
        land_size = data.get('land_size', '1')
        prev = data.get('prev', 'None')

        # Prompt
        prompt = f"""
        You are a 2026 Precision Agriculture Advisor for Maharashtra.
        Inputs: Soil={soil}, Water={water}, Season={season}, Land={land_size} Acres, Prev Crop={prev}.

        Provide the strategy in exactly this format:
        ENGLISH:
        📍 TOP CROPS: [2 crops]
        🧪 FERTILIZER: [Schedule for {land_size} acres]
        ⛈️ 2026 WEATHER: [Short April 2026 alert]

        MARATHI:
        [Accurate Marathi translation here]
        """

        response = gemini_model_2.generate_content(prompt)
        return jsonify({'advice': response.text})

    except Exception as e:
        print(f"ERROR: {e}")
        fallback = "ENGLISH:\n📍 TOP CROPS: Moong or Groundnut.\n🧪 FERTILIZER: Apply NPK 20:40:20.\n⛈️ 2026 WEATHER: Alert: Unseasonal rain expected.\n\nMARATHI:\n📍 मुख्य पिके: मूग किंवा भुईमूग.\n🧪 खत नियोजन: २०:४०:२० NPK वापरा.\n⛈️ २०२६ हवामान: इशारा: अवकाळी पावसाची शक्यता."
        return jsonify({'advice': fallback})
if __name__ == '__main__':
    app.run(debug=True)
