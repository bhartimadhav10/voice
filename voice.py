from flask import Flask, request, send_file
from flask_cors import CORS
from io import BytesIO
import google.generativeai as genai
from gtts import gTTS
import os
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

EMOTION_SETTINGS = {
    'insightful': {'tld': 'com.au', 'slow': False, 'pitch': 50},
    'motivational': {'tld': 'co.uk', 'slow': False, 'pitch': 120},
    'serious': {'tld': 'us', 'slow': True, 'pitch': 30},
    'default': {'tld': 'com.au', 'slow': False, 'pitch': 80}
}

def add_ssml_emphasis(text, emotion):
    """Add pseudo-SSML through text manipulation"""
    if emotion == 'insightful':
        return text.replace('.', '.\n\n')  # Add spacing for clarity
    elif emotion == 'motivational':
        return text.upper().replace('!', '!!!')  # Emphasize excitement
    elif emotion == 'serious':
        return "⚠️ " + text.replace('. ', '. \n\n')  # Add serious pauses
    return text

@app.route('/insight', methods=['POST'])
def ai_insight():
    data = request.get_json()
    if not data or 'idea' not in data:
        return {'error': 'Missing startup idea'}, 400
    
    idea = data['idea']
    emotion = data.get('emotion', 'default')
    
    try:
        # Generate constructive speech text
        prompt = f"""Provide an insightful speech on: {idea}
        Include:
        - A thought-provoking opening statement
        - 3 key challenges that could arise
        - 3 potential solutions or best practices
        - A motivational closing statement"""
        
        response = model.generate_content(prompt)
        insight_text = response.text
        
        # Enhance text for emotional speech
        enhanced_text = add_ssml_emphasis(insight_text, emotion)
        
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
            download_name=f'{emotion}_insight.mp3'
        )
        
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
