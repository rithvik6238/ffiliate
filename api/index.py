from flask import Flask, request, jsonify
from gradio_client import Client, handle_file
import tempfile
import mimetypes
import os
import httpx

app = Flask(__name__)

# Replace with your Imgbb API key
IMGBB_API_KEY = "df5461c520f518a4417bd57a8446453b"  # Replace with your Imgbb API key


# Function to upload file to Imgbb and get public URL
def upload_to_imgbb(file_path):
    url = "https://api.imgbb.com/1/upload"
    with open(file_path, "rb") as file:
        files = {"image": file}
        data = {"key": IMGBB_API_KEY}
        response = httpx.post(url, data=data, files=files)
        response_json = response.json()

        if response.status_code == 200 and response_json.get("success"):
            # Extract the image URL from the response
            return response_json["data"]["url"]
        else:
            raise Exception(f"Failed to upload to Imgbb: {response_json.get('error', 'Unknown error')}")


# Route to process uploaded images and return the processed image link
@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Check if the request has the file part
        if 'src_image' not in request.files or 'ref_image' not in request.files:
            return jsonify({"error": "Both 'src_image' and 'ref_image' are required"}), 400

        src_image = request.files['src_image']
        ref_image = request.files['ref_image']

        # Get file extensions based on MIME type
        src_extension = mimetypes.guess_extension(src_image.mimetype)
        ref_extension = mimetypes.guess_extension(ref_image.mimetype)

        if src_extension not in ['.jpg', '.jpeg', '.png'] or ref_extension not in ['.jpg', '.jpeg', '.png']:
            return jsonify({"error": "Only .jpg, .jpeg, and .png files are supported"}), 400

        # Save uploaded files to temporary files
        src_temp = tempfile.NamedTemporaryFile(delete=False, suffix=src_extension)
        src_image.save(src_temp.name)

        ref_temp = tempfile.NamedTemporaryFile(delete=False, suffix=ref_extension)
        ref_image.save(ref_temp.name)

        # Call Gradio model with the local file paths
        client = Client("franciszzj/Leffa")
        result = client.predict(
            src_image_path=handle_file(src_temp.name),
            ref_image_path=handle_file(ref_temp.name),
            ref_acceleration=False,
            step=30,
            scale=2.5,
            seed=42,
            vt_model_type="viton_hd",
            vt_garment_type="upper_body",
            vt_repaint=False,
            api_name="/leffa_predict_vt"
        )

        # Assuming result is a tuple and the first element is the image path
        if isinstance(result, tuple):
            processed_image_path = result[0]
        else:
            processed_image_path = result.get('image_path')

        if not processed_image_path:
            return jsonify({"error": "Processed image path not found in response"}), 500

        # Upload the processed image to Imgbb
        imgbb_url = upload_to_imgbb(processed_image_path)

        # Cleanup temporary files
        os.remove(src_temp.name)
        os.remove(ref_temp.name)

        # Return the Imgbb URL
        return jsonify({"processed_image_url": imgbb_url})

    except httpx.ProxyError as e:
        print(f"Proxy error occurred: {e}")
        return jsonify({"error": "Proxy error occurred"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
