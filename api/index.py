from flask import Flask, request, jsonify
import json
import re
import requests
from gradio_client import Client

app = Flask(__name__)

def generate_affiliate_link(asin, affiliate_id="lumeth2023-21"):
    return f"https://www.amazon.in/dp/{asin}/?tag={affiliate_id}&linkCode=ll1&language=en_IN"

def extract_asin(url):
    match = re.search(r"/dp/([A-Z0-9]+)", url)
    return match.group(1) if match else None

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
            if "amazon.com" in image_link or "amazon.in" in image_link:
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
                    search_results.append({
                        "title": item['title'],
                        "image_link": item['link'],
                        "context_link": item['image']['contextLink']
                    })
    return search_results

@app.route('/get_affiliate_links', methods=['GET'])
def get_affiliate_links():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    client = Client("Qwen/Qwen2-72B-Instruct")
    response = client.predict(
        query=query,
        history=[],
        system="""based on the user input suggest the products from Amazon available in the market return in json format 
        example catagory: [
        {
          product_name: ,
          short_discription: 
        }
      ] """,
        api_name="/model_chat_1"
    )
    
    string = response[1][0][1]
    json_part = re.search(r'```json\n(.*?)```', string, re.DOTALL)
    if not json_part:
        return jsonify({"error": "Invalid response format from AI"}), 500
    
    text = json.loads(json_part.group(1))
    
API_KEY = "AIzaSyBOPWyQKGuSARQCAxFMpE8VHWW1qJ8hV7s"
CX = "000c0d4dcdc184f06"
    
    results = {}
    for category, products in text.items():
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
                        "short_description": product.get("short_discription", ""),
                        "image": result['image_link'],
                        "affiliate_link": affiliate_link
                    })
                    break  # Only take the first relevant image
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
