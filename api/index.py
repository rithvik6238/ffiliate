import os
from flask import Flask, request, jsonify
from gradio_client import Client, handle_file
import firebase_admin
from firebase_admin import credentials, storage, firestore

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "lumethrv",
    "private_key_id": "1eacf503125d8738d41e7300870fd40ae985e8cb",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDN0Go7fpR9kgaG\nkN0NzSZM9CRV7AVXRCCsiv2STMWlXopLOB8F3rQVqYk39aRoVKbW0Do11XSOJxer\nYlo/jED1iP/5CQngTTNEuopB1wJWGWOJzbVQfgvYz/Nw12BWCYYmwgdY2NN7UphG\n+ulLk6HaOnVLQz3sIqLuR5UZfKvPuxzLNC55tqO/YLt4lambkDAdG5vD87qCgeSs\nF5nD2BNOcaPMgbMrXl05ELnze04Tonr56R64PqzLQBJgIuRuuWxWNdOf4lSqrbCR\nnvvotH3W1TGs6lU3SGcpzjtZ+ClANOs0I2F/Dj668CAV1BvXB20ZPT1TuiNDG+4B\nMy8uOAQjAgMBAAECggEACs5jlYYa49Dz+MLIaH4aAbZb5gsDaMaR9J1DnRfc1Mb2\n+eYTcupziCOjqcWDAVtYezTpqYPwn7obuwrp9CY4DuxHjFrWIunKxFQLCFPysnSY\nzlZ3q6dClfqtLIKSc1ICsixD2H1h9Tqr9iYcc7Rnrh6do/r+2FQlO9+US4dJOhnf\n1Abf9QInLcv3u7YNJwS99Py09NskSfEE53/ClEl/2oIeMXJGEMDQ9Q3eCDTTHIt0\n8g9qjOh1U3gppZ71JkUKlLUa+NwUvWIjlGPjmRfBGfOl3GmqsJDeCbavBbs+wRoi\nk1RuS0NrY0abIqqUX36Qu7Qmya/BIlNvmjdiFu3CCQKBgQDvZjlPrAR8CQsqGwuE\n6GCUBxaWMjnTNOuX7FlxkFA0jJQc0isZu9d7mYRjSmZf5zNlYMGn3+2I9Sw5I7IW\nuQPWdZA/mFvE5TdXLyy+9o4HQ0QdJZXMB6RREEqG3fpjsKdneQssNZlpQs6Za/ky\ns9d9D0Bhm4Pdyf2zC+QToyJifQKBgQDcFf4SElsrzszJaQNFlAWAumM2Z/tvva4x\nVRUfDAUk6b6Go2hqo1DkA3n0v6J78lyr/ZArdOwEXyehKCjg9jKCVG6MXn3jD7gx\nd+l/TzHU2/k/+NIcQGnJ37qOI5Z4+v2BiertqleyOk66koQDGLOtghKxxZAoAYUN\nYPZnVKMjHwKBgE3ntzjNIrx2ePKf0HTU5jDlyZzhBV5M92n+GPFS5DbllIF4h1wd\ne7cWMzXYjU4iP+B6xyppPbR3DIgfrKGmXbBZm7KGUz7U1NiDWo1eUMPeSPkvNPsr\ndXaH1ajj7cqpPyD2DAO8AYt2mSLmNzcfvT1OTEY3RIdVZ0Dv2q3lRZhFAoGBAKgy\nzpe1G6RhSbTr4qo8M/BrggNEeK6vQf9FzPyLTSsm0ItJOzW0Vs/LsFrSUjVzxktT\nX+k2VGIK7tiFPqiev39HU61HUeJEUzrLL9IyDh1leBnh6YHZ4H990q9ql0ciWrez\nVa4JLzhww1ZnPyi2qisCa5MdL8zDTJIq9mWGE591AoGBAMDh6jRDFDJqB3FZzMSo\nB9+0qgb5KW1YqlkFr86zrwKPHLJj0+8BJKbXSL9ulIbEs40SgVEuKAb801I+dFxg\ne1rPrQnqFTqrBPgPVcWzj5n8x69GqOJaoNOc0AjG5gJI8Ls3ecenpJ9xVDLRzsMn\nt4Gkj3uWEVGElzmUSgS2Zqzu\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-mmudl@lumethrv.iam.gserviceaccount.com",
    "client_id": "118272570511746214100",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-mmudl%40lumethrv.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
})

firebase_admin.initialize_app(cred, {'storageBucket': 'lumethrv.appspot.com'})

# Firestore client
db = firestore.client()

@app.route('/process-images', methods=['POST'])
def process_images():
    try:
        client = Client("franciszzj/Leffa")
        
        if 'src_image' not in request.files or 'ref_image' not in request.files:
            return jsonify({"error": "Both 'src_image' and 'ref_image' must be provided"}), 400

        src_image = request.files['src_image']
        ref_image = request.files['ref_image']

        src_image_path = handle_file(src_image)
        ref_image_path = handle_file(ref_image)

        result = client.predict(
            src_image_path=src_image_path,
            ref_image_path=ref_image_path,
            ref_acceleration=False,
            step=30,
            scale=2.5,
            seed=42,
            vt_model_type="viton_hd",
            vt_garment_type="upper_body",
            vt_repaint=False,
            api_name="/leffa_predict_vt"
        )

        first_image_path = result[0] if result and len(result) > 0 else None

        if first_image_path:
            src_image_ref = storage.bucket().blob(f"images/{src_image.filename}")
            ref_image_ref = storage.bucket().blob(f"images/{ref_image.filename}")
            src_image_ref.upload_from_filename(src_image_path)
            ref_image_ref.upload_from_filename(ref_image_path)

            src_image_url = src_image_ref.public_url
            ref_image_url = ref_image_ref.public_url

            doc_ref = db.collection('images').add({
                'src_image_url': src_image_url,
                'ref_image_url': ref_image_url,
                'processed_image_url': first_image_path
            })

            return jsonify({
                "first_image_url": first_image_path,
                "src_image_url": src_image_url,
                "ref_image_url": ref_image_url
            })
        else:
            return jsonify({"error": "No valid result from Gradio client"}), 500

    except Exception as e:
        print(f"Error: {str(e)}")  # Print the error to the console for debugging
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=506501)
