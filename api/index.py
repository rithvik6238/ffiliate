import json
import re
import os
import requests
import logging
from flask import Flask, request, jsonify
from gradio_client import Client

app = Flask(__name__)

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)


def generate_affiliate_link(asin, affiliate_id="lumeth2023-21"):
    """Generate an Amazon affiliate link based on ASIN."""
    return f"https://www.amazon.in/dp/{asin}/?tag={affiliate_id}&linkCode=ll1&language=en_IN"


def extract_asin(url):
    """Extract ASIN from Amazon product URL."""
    match = re.search(r"/dp/([A-Z0-9]+)", url)
    return match.group(1) if match else None


def google_image_search(query, api_key, cx, fallback_search=False):
    """Perform Google Image Search to find product images."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "searchType": "image",
        "num": 3
    }

    response = requests.get(url, params=params)
    search_results = []

    if response.status_code == 200:
        results = response.json()
        found_amazon = False

        for item in results.get("items", []):
            image_link = item['link']
            if "amazon.com" in image_link or "amazon.in" in image_link:
                search_results.append({
                    "title": item['title'],
                    "image_link": image_link,
                    "context_link": item['image']['contextLink']
                })
                found_amazon = True
                break  # Stop at the first Amazon result

        # If no Amazon image is found, fallback to Flipkart
        if not found_amazon and fallback_search:
            params["q"] = f"{query} site:flipkart.com"
            response = requests.get(url, params=params)

            if response.status_code == 200:
                results = response.json()
                for item in results.get("items", []):
                    search_results.append({
                        "title": item['title'],
                        "image_link": item['link'],
                        "context_link": item['image']['contextLink']
                    })

    return search_results


@app.route('/get_affiliate_links', methods=['GET'])
def get_affiliate_links():
    """Main API route to generate affiliate links."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Initialize Gradio AI client
    try:
        client = Client("Qwen/Qwen2-72B-Instruct")
        response = client.predict(
            query=query,
            history=[],
            system="""based on the user input suggest the products from Amazon available in the market return in json format 
            example category: [
                {
                    "product_name": "",
                    "short_description": ""
                }
            ] """,
            api_name="/model_chat_1"
        )
    except Exception as e:
        logging.error(f"AI API request failed: {e}")
        return jsonify({"error": "Failed to fetch product suggestions"}), 500

    # Extract JSON response safely
    string = response[1][0][1] if len(response) > 1 and len(response[1]) > 0 else ""
    json_match = re.search(r'{.*}', string, re.DOTALL)

    if not json_match:
        logging.error("Invalid JSON format from AI response")
        return jsonify({"error": "Invalid JSON format from AI"}), 500

    try:
        product_data = json.loads(json_match.group(0))
    except json.JSONDecodeError:
        logging.error("JSON decoding failed")
        return jsonify({"error": "AI response contained invalid JSON"}), 500

    # Get Google API credentials from environment variables
    API_KEY = "AIzaSyBOPWyQKGuSARQCAxFMpE8VHWW1qJ8hV7s"
    CX = "000c0d4dcdc184f06"
    if not API_KEY or not CX:
        logging.error("Google API credentials missing")
        return jsonify({"error": "Missing Google API credentials"}), 500

    results = {}

    for category, products in product_data.items():
        results[category] = []
        for product in products:
            product_name = product["product_name"]
            search_results = google_image_search(product_name, API_KEY, CX, fallback_search=True)

            if search_results:
                for result in search_results:
                    asin = extract_asin(result['context_link'])
                    affiliate_link = generate_affiliate_link(asin) if asin else result['context_link']

                    results[category].append({
                        "product_name": product_name,
                        "short_description": product.get("short_description", ""),
                        "image": result['image_link'],
                        "affiliate_link": affiliate_link
                    })
                    break  # Take only the first valid image

    return jsonify(results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
