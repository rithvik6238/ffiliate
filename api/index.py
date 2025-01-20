from flask import Flask, request, jsonify
from gradio_client import Client, handle_file
import httpx

app = Flask(__name__)

# Replace with your Imgbb API key
IMGBB_API_KEY = "7050e5baffd948245c4f630ba8f66e0a"

# Function to upload file to Imgbb and get public URL
def upload_to_imgbb(image_path):
    url = "https://api.imgbb.com/1/upload"
    with open(image_path, "rb") as file:
        files = {"image": file}
        data = {"key": IMGBB_API_KEY}
        response = httpx.post(url, data=data, files=files)
        response_json = response.json()

        if response.status_code == 200 and response_json.get("success"):
            return response_json["data"]["url"]
        else:
            raise Exception(f"Failed to upload to Imgbb: {response_json.get('error', 'Unknown error')}")

# Route to process images using the Gradio API
@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Get source and target image URLs from the request
        src_image_url = request.json.get('src_image_url')
        target_image_url = request.json.get('target_image_url')

        if not src_image_url or not target_image_url:
            return jsonify({"error": "Both 'src_image_url' and 'target_image_url' are required"}), 400

        # Call the Gradio client with the provided URLs
        client = Client("tuan2308/face-swap")
        result = client.predict(
            source_file=handle_file(src_image_url),
            target_file=handle_file(target_image_url),
            doFaceEnhancer=False,
            api_name="/predict"
        )

        # Assuming the result contains the processed image path
        processed_image_path = result if isinstance(result, str) else None

        if not processed_image_path:
            return jsonify({"error": "Processed image path not found in response"}), 500

        # Upload the processed image to Imgbb
        imgbb_url = upload_to_imgbb(processed_image_path)

        # Return the Imgbb URL
        return jsonify({"processed_image_url": imgbb_url})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
