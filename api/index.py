import os
from flask import Flask, jsonify, request
from gradio_client import Client, handle_file
import firebase_admin
from firebase_admin import credentials, storage

app = Flask(__name__)

# Get the absolute path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the credentials file (one level up)
credentials_path = os.path.join(current_dir, '..', 'lumethrv-firebase-adminsdk-mmudl-d6ad777c3c.json')

# Initialize Firebase Admin SDK
cred = credentials.Certificate(credentials_path)
firebase_admin.initialize_app(cred, {
    "storageBucket": "lumethrv.appspot.com"  # Replace with your Firebase Storage bucket name
})

# Function to upload file to Firebase Storage and get public URL
def upload_to_firebase(file_path, file_name):
    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_path)
    blob.make_public()  # Make the file publicly accessible
    return blob.public_url

# Route to process uploaded image
@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Check if the image file is included in the request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        # Save the uploaded image locally
        image = request.files['image']
        image_path = os.path.join(current_dir, 'uploaded_image', image.filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)

        # Call the Gradio model for prediction
        client = Client("franciszzj/Leffa")
        result = client.predict(
            src_image_path=handle_file(image_path),
            ref_image_path=handle_file(image_path),  # Replace with actual reference image logic
            ref_acceleration=False,
            step=30,
            scale=2.5,
            seed=42,
            vt_model_type="viton_hd",
            vt_garment_type="upper_body",
            vt_repaint=False,
            api_name="/leffa_predict_vt"
        )

        # Assuming result contains the processed image path
        if isinstance(result, tuple):
            processed_image_path = result[0]  # Adjust based on actual result structure
        else:
            processed_image_path = result.get('image_path')

        if not processed_image_path:
            return jsonify({"error": "Processed image path not found in response"}), 500

        # Upload the processed image to Firebase Storage
        processed_file_name = os.path.basename(processed_image_path)
        firebase_url = upload_to_firebase(processed_image_path, processed_file_name)

        # Return the Firebase Storage URL of the processed image
        return jsonify({"processed_image_url": firebase_url})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
