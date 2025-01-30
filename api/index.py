import json
import re
import requests
from app import Flask, request, jsonify
from gradio_client import Client

app = Flask(__name__)

# Function to generate an affiliate link
def generate_affiliate_link(asin, affiliate_id="lumeth2023-21"):
    return f"https://www.amazon.in/dp/{asin}/?tag={affiliate_id}&linkCode=ll1&language=en_IN"

# Function to extract ASIN from Amazon product URL
def extract_asin(url):
    match = re.search(r"/dp/([A-Z0-9]+)", url)
    return match.group(1) if match else None

# Function to extract headings from JSON response
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
                    "context_link": item['image']['contextLink']
                })
                found_amazon = True
                break
        
        # If no Amazon image found and fallback is enabled, search for Flipkart
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
                        "context_link": item['image']['contextLink']
                    })
    else:
        print(f"Error: {response.status_code}, {response.text}")
    
    return search_results

# Initialize the client
client = Client("Qwen/Qwen2-72B-Instruct")

@app.route('/get_affiliate_products', methods=['POST'])
def get_affiliate_products():
    # Read JSON request data
    data = request.get_json()
    print("Received Request Data:", data)  # Debugging log

    if not data or "query" not in data:
        return jsonify({"error": "Invalid JSON or missing 'query' field"}), 400

    query = data.get("query", "")

    # Fetch AI-generated response
    response = client.predict(
        query=query,
        history=[],
        system=""" based on the user input suggest the products from Amazon available in the market return in json 
        example: 
        {
            "category": [
                {
                    "product_name": "Example Product",
                    "short_description": "Example Description"
                }
            ]
        }""",
        api_name="/model_chat_1"
    )

    # Extract relevant JSON response
    try:
        json_part = re.search(r'```json\n(.*?)```', response[1][0][1], re.DOTALL).group(1)
        text = json.loads(json_part)
    except (IndexError, AttributeError, json.JSONDecodeError) as e:
        print("Error extracting JSON:", e)
        return jsonify({"error": "Invalid AI response format"}), 500

    # Extract headings
    headings = extract_headings(text)

    # Set API keys for Google Search
    API_KEY = "AIzaSyBOPWyQKGuSARQCAxFMpE8VHWW1qJ8hV7s"
    CX = "000c0d4dcdc184f06"

    # Perform image search and generate affiliate links
    results = []
    for category in text:
        category_results = []
        for product in text[category]:
            product_name = product["product_name"]
            search_query = f"{product_name} site:amazon.in"
            search_results = google_image_search(search_query, API_KEY, CX, fallback_search=True)

            if search_results:
                for result in search_results:
                    asin = extract_asin(result['context_link'])
                    affiliate_link = generate_affiliate_link(asin) if asin else result['context_link']

                    category_results.append({
                        "product_name": product_name,
                        "image_title": result['title'],
                        "image_link": result['image_link'],
                        "affiliate_link": affiliate_link
                    })
            else:
                category_results.append({
                    "product_name": product_name,
                    "image_title": "No Image Found",
                    "image_link": "",
                    "affiliate_link": ""
                })
        
        results.append({category: category_results})

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
