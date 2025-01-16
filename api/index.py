import os
from flask import Flask, jsonify, request
from gradio_client import Client, handle_file
import firebase_admin
from firebase_admin import credentials, storage

app = Flask(__name__)

# Get the absolute path of the current script
firebase_credentials = {
    "type": "service_account",
    "project_id": "lumethrv",
    "private_key_id": "d6ad777c3ce84b02adc9524771f806b670dc1387",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCPMcDfykUCvK/j
qKmswGvdhGeblJMVQeOpYekVJ5GQyvszc0W9hIFDharKVtMxXDoPL0N6f32oufNP
Jbumy3ZmfODw4z/CvZwOkSdf53O4Ld1rI7ichIXEID8sEvU18Ll8UcotsEnOJFfa
TnTAoMBgMLTm39bnfEL13N1G/yHKNjQYorhT01UTowkppiA/mUetu9PUe38KX6mL
P4cteVa5Z21JjJ9vWjpAo5AoRKlhuA9v8AUD4HbjP8xHmuMJikrlLz0S7n1dHBzm
rNJtvqxjhUskHkDruqNwxqJjTz/p3yJQszMwYiBSq7ylrZZKx/Ii9b+G7FbH7u/z
LWKrxqYjAgMBAAECggEAOSfj06/Z8ei80EMvTswTgfzqmhgoyVBefeqd7Zq4qLHM
qNG3IZl1Oy1saY1UiRxF9G+qIIgo8SMf8hSenUoTPX9VDfG3LpUeaFYaAFbTQs3T
1oMQmjDvb8RrUr1ScTBf6TaAW9JE82pgQrwUMBs6DmsCmjD4h7d6xsZc8Iy/wQVe
082ps/AHI88GNB9EjLsWogZKv8acRTKdzkdXy/tGAjrKWHVeEeOo7/KI0hzOZmfF
spmwvqyDybM6bIykqxT4mvy/dIQZyXsgsOCtMQna019GbsQ5mO7PNeB42D+LyBpl
4rGtPGtEeeu6afe2lMfBbDgUI/Xzb7bDZxZMTcGyiQKBgQC834th+AMPGkOCF1To
4Rvs57laJk1ls5EPBA4i0QCrpmqIhS/wXYBBUHleCjgjrBIrM6iPm42wMZMEH5Qg
3blMUaobN9BUHIn+c+j7N5n3DvBXOajG+SPtONV99+9C+LxmMYT332sT0FLGsY+i
VR64Sj0ZibRooqYb1HtnWyw+9wKBgQDCFii2flKdzEu61HQRi4ega+hqpeC1WrF9
RKABhC76Ow4Sn4x8HCO2xFjPaohVaX1B/pKasxaTeGzEtrhKLJVPkXEf7OnmOFni
mF7EWyedvkDe6f4UcUc8XMzgftOI4TitBUfQVNhjrwog96YLt0eiim0JLskEpcvb
N2iZox8LNQKBgQCBN5tfglNtcLWA+j9wOBpn4T1RLOVE0C5NDKQzM7R2uxslnaFn
nECT7t+p8+nmleG0RtpqraypP7FqX8RzG96bFUAA8RWJhiDuwhRCUw72FPVfZ6ZN
wsPOl1SQoyDBO/WBIR3si6DxZFRNdctj70JeKQRWRXz1HVnxrlRjKOBDjwKBgHjj
/oX1VxZs6vq7XHSVOWxl6kWLftTXYdiKBzQKloxMfm6BLKsdh+1OjZbcX4D8DQYv
QDfVtwkyKGW6/j1NWc9O42ykT+iTTwGCMP0TXjC2EYgHrbgj+uARWZe3x6Dp0DiN
IncUchhdLezs9GM1zQvkNxhSKOmZL8oi0CdqYGrFAoGAUWJYNo8enHnch026jIi9
8KvZUdOA2b19JyYBO0wYyuudZln+/NSXllLW+0zTmHfUzkHwSZfSuoABPVk/HIaH
Iu2uLWqxD5WxgX90pq3JS+R7Z2Vrf2hRptd6DKrRxTkaMQP73DNWBEn1c1fo8a5z
GGJO5l8ua9zFm4ctVJEbySE=
-----END PRIVATE KEY-----
""",
    "client_email": "firebase-adminsdk-mmudl@lumethrv.iam.gserviceaccount.com",
    "client_id": "118272570511746214100",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-mmudl%40lumethrv.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
initialize_app(cred)
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
