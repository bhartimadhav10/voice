from flask import Flask, request, send_file
from flask_cors import CORS
from io import BytesIO
import google.generativeai as genai
from gtts import gTTS
import os
import re

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

EMOTION_SETTINGS = {
    'sarcastic': {'tld': 'com.au', 'slow': False, 'pitch': 50},
    'excited': {'tld': 'co.uk', 'slow': False, 'pitch': 120},
    'serious': {'tld': 'us', 'slow': True, 'pitch': 30},
    'default': {'tld': 'com.au', 'slow': False, 'pitch': 80}
}

def add_ssml_emphasis(text, emotion):
    """Add pseudo-SSML through text manipulation"""
    if emotion == 'sarcastic':
        return re.sub(r'\b(\w+)\b', r'\1... \1', text[:300])  # Add sarcastic pauses
    elif emotion == 'excited':
        return text.upper().replace('!', '!!!')[:300]  # Add excitement
    elif emotion == 'serious':
        return "⚠️ " + text.replace('. ', '. \n\n')  # Add serious pauses
    return text

@app.route('/roast', methods=['POST'])
def ai_roast():
    data = request.get_json()
    if not data or 'idea' not in data:
        return {'error': 'Missing startup idea'}, 400
    
    idea = data['idea']
    emotion = data.get('emotion', 'default')
    
    try:
        # Generate emotional roast text
        prompt = f"""Act as a {emotion} standup comedian analyzing: {idea}
        Include 3 funny but insightful critiques and 1 genuine advice.
        Format: 
        - {emotion.capitalize()} opening analogy
        - 3 joke-based market insights
        - 1 {emotion} piece of advice
        - Emotional closing line"""
        
        response = model.generate_content(prompt)
        roast_text = response.text
        
        # Enhance text for emotional speech
        enhanced_text = add_ssml_emphasis(roast_text, emotion)
        
        # Generate emotional voice using gTTS hacks
        tts = gTTS(
            text=enhanced_text,
            lang='hi',
            tld=EMOTION_SETTINGS[emotion]['tld'],
            slow=EMOTION_SETTINGS[emotion]['slow']
        )
        
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f'{emotion}_roast.mp3'
        )
        
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)