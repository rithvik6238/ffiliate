import json
import re
import requests
from flask import Flask, request, jsonify
from gradio_client import Client

app = Flask(__name__)

def generate_affiliate_link(asin, affiliate_id="lumeth2023-21"):
    return f"https://www.amazon.in/dp/{asin}/?tag={affiliate_id}&linkCode=ll1&language=en_IN"

def extract_asin(url):
    match = re.search(r"/dp/([A-Z0-9]+)", url)
    return match.group(1) if match else None

def extract_headings(text_dict):
    return list(text_dict.keys())

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
                    search_results.append({
                        "title": item['title'],
                        "image_link": item['link'],
                        "context_link": item['image']['contextLink']
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
        system=""" based on the user input suggest the products from amazone available in the market return in json  example category: [
        {
          product_name: ,
          short_description: 
        }
      ] """,
        api_name="/model_chat_1"
    )
    
    string = response[1][0][1]
    json_part = re.search(r'```json\n(.*?)```', string, re.DOTALL).group(1)
    text = json.loads(json_part)

    API_KEY = "AIzaSyBOPWyQKGuSARQCAxFMpE8VHWW1qJ8hV7s"
    CX = "000c0d4dcdc184f06"
    results = {}

    for category in text:
        results[category] = []
        for product in text[category]:
            product_name = product["product_name"]
            search_results = google_image_search(f"{product_name} site:amazon.in", API_KEY, CX, fallback_search=True)
            if search_results:
                for result in search_results:
                    asin = extract_asin(result['context_link'])
                    affiliate_link = generate_affiliate_link(asin) if asin else result['context_link']
                    results[category].append({
                        "product_name": product_name,
                        "image_link": result['image_link'],
                        "affiliate_link": affiliate_link
                    })
            else:
                results[category].append({"product_name": product_name, "error": "No image results found."})
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
