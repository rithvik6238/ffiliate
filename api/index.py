from flask import Flask, request, jsonify
from gradio_client import Client, file

app = Flask(__name__)

# Initialize the Gradio client (you can choose to initialize this per request if thread-safety is a concern)
client = Client("akhil2808/MongoDBpixtralOCR")

@app.route('/predict', methods=['POST'])
def predict():
    # Parse JSON input from the POST request
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided."}), 400

    # Extract the required parameters from the JSON body
    uploaded_file = data.get('uploaded_file')
    mrn_number = data.get('mrn_number')
    user_question = data.get('user_question')

    # Validate input parameters
    if not uploaded_file or not mrn_number or not user_question:
        return jsonify({
            "error": "Missing one or more required parameters: uploaded_file, mrn_number, user_question."
        }), 400

    try:
        # Prepare the file parameter using gradio_client's file helper function
        file_obj = file(uploaded_file)
        
        # Call the Gradio client API using the provided parameters
        result = client.predict(
            uploaded_file=file_obj,
            mrn_number=mrn_number,
            user_question=user_question,
            api_name="/predict"
        )
        
        # Return the result in JSON format
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run Flask with threaded=True to allow handling multiple requests concurrently.
    # For production, consider using a WSGI server like Gunicorn.
    app.run(host='0.0.0.0', port=5000, threaded=True)
