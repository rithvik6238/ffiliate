from flask import Flask, request, jsonify
from gradio_client import Client

app = Flask(__name__)

# Initialize Gradio client with the model
client = Client("vantexidprvt/facebook-bart-large-mnli")

@app.route('/predict', methods=['POST'])
def predict():
    # Get the 'param_0' value from the user input
    param_0 = request.json.get('param_0', '')

    # The other params (param_1 and param_2) are predefined
    param_1 = "chatting , giving beauty solutions,  giving beauty suggestions , giving body building solutions ,giving body building suggestions , giving  diet plan  suggestions"
    param_2 = False

    # Call the Gradio client predict method
    result = client.predict(
        param_0=param_0,
        param_1=param_1,
        param_2=param_2,
        api_name="/predict"
    )

    # Extract the highest confidence label from the result
    confidences = result.get('confidences', [])
    if confidences:
        highest_confidence = max(confidences, key=lambda x: x.get('confidence', 0))
        return jsonify({'label': highest_confidence['label']})
    else:
        return jsonify({'error': 'No confidences found in the result'}), 400

if __name__ == '__main__':
    app.run(debug=True)
