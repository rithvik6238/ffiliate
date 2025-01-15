from flask import Flask, send_file, jsonify
from gradio_client import Client, handle_file
import httpx
import os
from io import BytesIO

app = Flask(__name__)

# Route to trigger the prediction and display the result
@app.route('/predict', methods=['GET'])
def predict():
    try:
        client = Client("franciszzj/Leffa")
        result = client.predict(
            src_image_path=handle_file('https://levihsu-ootdiffusion.hf.space/file=/tmp/gradio/aa9673ab8fa122b9c5cdccf326e5f6fc244bc89b/model_8.png'),
            ref_image_path=handle_file('https://levihsu-ootdiffusion.hf.space/file=/tmp/gradio/17c62353c027a67af6f4c6e8dccce54fba3e1e43/048554_1.jpg'),
            ref_acceleration=False,
            step=30,
            scale=2.5,
            seed=42,
            vt_model_type="viton_hd",
            vt_garment_type="upper_body",
            vt_repaint=False,
            api_name="/leffa_predict_vt"
        )
        
        # Assuming result contains an image file path or image data
        # You can adjust this depending on how the result is structured
        image_path = result['image_path']  # Adjust based on actual response format
        
        # Sending the image to be displayed
        return send_file(image_path, mimetype='image/png')

    except httpx.ProxyError as e:
        print(f"Proxy error occurred: {e}")
        return jsonify({"error": "Proxy error occurred"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)
