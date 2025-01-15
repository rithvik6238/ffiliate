from flask import Flask, jsonify, send_file
from gradio_client import Client, handle_file
import httpx

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

        # Assuming result is a tuple and the first element is the image path
        if isinstance(result, tuple):
            image_path = result[0]  # Adjust based on actual result structure
        else:
            image_path = result.get('image_path')  # If it's a dictionary, use get()

        if not image_path:
            return jsonify({"error": "Image path not found in response"}), 500
        
        # Serve the image file using send_file, assuming it's a local path or accessible path
        return send_file(image_path, mimetype='image/png')

    except httpx.ProxyError as e:
        print(f"Proxy error occurred: {e}")
        return jsonify({"error": "Proxy error occurred"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
