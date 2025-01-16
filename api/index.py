from flask import Flask, request, jsonify, send_file
from gradio_client import Client, handle_file
import os
import tempfile
import mimetypes
import httpx

app = Flask(__name__)

# Function to return image directly as a response with dynamic MIME type
def send_image(file_path):
    # Get the file extension to determine the MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Fallback if MIME type cannot be determined
    return send_file(file_path, mimetype=mime_type)

# Route to process uploaded images and return the processed image
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
            processed_image_path = result[0]  # Adjust based on actual result structure
        else:
            processed_image_path = result.get('image_path')  # If it's a dictionary, use get()

        if not processed_image_path:
            return jsonify({"error": "Processed image path not found in response"}), 500

        # Cleanup temporary files
        os.remove(src_temp.name)
        os.remove(ref_temp.name)

        # Return the image directly as a response
        return send_image(processed_image_path)

    except httpx.ProxyError as e:
        print(f"Proxy error occurred: {e}")
        return jsonify({"error": "Proxy error occurred"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
