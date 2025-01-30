import json
import re
import requests
from flask import Flask, request, jsonify
from gradio_client import Client

app = Flask(__name__)

# Function to generate an affiliate link
def generate_affiliate_link(asin, affiliate_id="lumeth2023-21"):
    return f"https://www.amazon.in/dp/{asin}/?tag={affiliate_id}&linkCode=ll1&language=en_IN"

# Function to extract ASIN from Amazon product URL
def extract_asin(url):
    match = re.search(r"/dp/([A-Z0-9]+)", url)
    return match.group(1) if match else None

# Function to extract headings from dictionary
def extract_headings(text_dict):
    return list(text_dict.keys())

# Function to perform Google Image Search
def google_image_search(query, api_key, cx, fallback_search=False):
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
            if any(domain in image_link for domain in ["amazon.com", "sephora.com", "ulta.com", "walmart.com"]):
                search_results.append({
                    "title": item['title'],
                    "image_link": image_link,
                    "context_link": item.get('image', {}).get('contextLink', "")
                })
                found_amazon = True
                break

        if not found_amazon and fallback_search:
            print(f"Amazon image not found, searching on Flipkart...")
            params["q"] = f"{query} site:flipkart.com"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                results = response.json()
                for item in results.get("items", []):
                    search_results.append({
                        "title": item['title'],
                        "image_link": item['link'],
                        "context_link": item.get('image', {}).get('contextLink', "")
                    })
    else:
        print(f"Error: {response.status_code}, {response.text}")

    return search_results

@app.route('/get_affiliate_products', methods=['POST'])
def get_affiliate_products():
    data = request.json
    query = data.get("query", "")

    client = Client("Qwen/Qwen2-72B-Instruct")

    response = client.predict(
        query=query,
        history=[],
        system="""{
            "category": [
                {
                    "product_name": "",
                    "short_description": ""
                }
            ]
        }""",
        api_name="/model_chat_1"
    )

    # Extract the relevant string from response
    try:
        string = response[1][0][1]
        json_part = re.search(r'```json\n(.*?)```', string, re.DOTALL)
        if json_part:
            json_data = json.loads(json_part.group(1))
        else:
            return jsonify({"error": "Invalid response format"}), 400
    except (IndexError, KeyError, json.JSONDecodeError):
        return jsonify({"error": "Failed to extract JSON"}), 400

    headings = extract_headings(json_data)

    API_KEY = "AIzaSyBOPWyQKGuSARQCAxFMpE8VHWW1qJ8hV7s"
    CX = "000c0d4dcdc184f06"

    results = []
    for category in json_data:
        for product in json_data[category]:
            product_name = product["product_name"]
            query = f"{product_name} site:amazon.in"
            search_results = google_image_search(query, API_KEY, CX, fallback_search=True)

            product_info = {
                "product_name": product_name,
                "images": []
            }

            if search_results:
                for result in search_results:
                    asin = extract_asin(result['context_link'])
                    affiliate_link = generate_affiliate_link(asin) if asin else result['context_link']

                    product_info["images"].append({
                        "title": result['title'],
                        "image_link": result['image_link'],
                        "affiliate_link": affiliate_link
                    })
            results.append(product_info)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
