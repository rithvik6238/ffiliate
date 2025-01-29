from flask import Flask, request, jsonify
import json
from gradio_client import Client
import re
import requests

app = Flask(__name__)

def generate_affiliate_link(asin, affiliate_id="lumeth2023-21"):
    return f"https://www.amazon.in/dp/{asin}/?tag={affiliate_id}&linkCode=ll1&language=en_IN"

def extract_asin(url):
    match = re.search(r"/dp/([A-Z0-9]+)", url)
    return match.group(1) if match else None

def extract_headings(text_dict):
    headings = []
    for key in text_dict:
        headings.append(key)
    return headings

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
        
        if not found_amazon and fallback_search:
            params["q"] = f"{query} site:flipkart.com"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                results = response.json()
                for item in results.get("items", []):
                    image_link = item['link']
                    search_results.append({
                        "title": item['title'],
                        "image_link": image_link,
                        "context_link": item['image']['contextLink']
                    })
    return search_results

client = Client("Qwen/Qwen2-72B-Instruct")
API_KEY = "AIzaSyBOPWyQKGuSARQCAxFMpE8VHWW1qJ8hV7s"
CX = "000c0d4dcdc184f06"

@app.route('/search', methods=['POST'])
def handle_search():
    try:
        user_query = request.json['query']
        
        response = client.predict(
            query=user_query,
            history=[],
            system="""based on the user input suggest the products from amazone avilable in the market return in json  example catagory: [
                { product_name: , short_discription: }
            ]""",
            api_name="/model_chat_1"
        )

        string = response[1][0][1]
        json_match = re.search(r'```json\n(.*?)```', string, re.DOTALL)
        if not json_match:
            return jsonify({"error": "No JSON found in response"}), 500
            
        json_part = json_match.group(1)
        text = json.loads(json_part)

        for category in text:
            for product in text[category]:
                product_name = product["product_name"]
                search_query = f"{product_name} site:amazon.in"
                search_results = google_image_search(search_query, API_KEY, CX, True)
                
                product_images = []
                for result in search_results:
                    asin = extract_asin(result['context_link'])
                    affiliate_link = generate_affiliate_link(asin) if asin else result['context_link']
                    product_images.append({
                        "title": result['title'],
                        "image": result['image_link'],
                        "affiliate_link": affiliate_link
                    })
                
                product["images"] = product_images

        return jsonify(text)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
