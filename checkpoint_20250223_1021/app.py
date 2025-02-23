from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from emerald_rag import EmeraldAssistant
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the Emerald Assistant
assistant = EmeraldAssistant()

@app.route('/')
def serve_report():
    return send_from_directory('.', 'sentiment_report.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get response from Emerald Assistant
        response = assistant.get_response(user_message)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 