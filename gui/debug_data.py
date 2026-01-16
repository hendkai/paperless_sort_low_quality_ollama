
import os
import requests
from dotenv import load_dotenv

load_dotenv('../.env')

API_URL = os.getenv('API_URL')
API_TOKEN = os.getenv('API_TOKEN')

print(f"Checking API: {API_URL}")

headers = {'Authorization': f'Token {API_TOKEN}'}
params = {'page_size': 100, 'tags__id__none': '91,92'}

try:
    response = requests.get(f'{API_URL}/documents/', headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    
    results = data.get('results', [])
    print(f"Total count in DB: {data.get('count')}")
    print(f"Returned in page 1: {len(results)}")
    
    empty = 0
    tagged = 0
    valid = 0
    
    for doc in results:
        content = doc.get('content', '').strip()
        tags = doc.get('tags', [])
        
        is_empty = len(content) == 0
        is_tagged = len(tags) > 0
        
        if is_empty:
            empty += 1
        elif is_tagged:
            tagged += 1
        else:
            valid += 1
            print(f"DEBUG: Found PROPER doc ID {doc.get('id')} Title: {doc.get('title')}")
            
    print(f"Stats Page 1: Empty={empty}, Tagged={tagged}, Valid(Untagged & Content)={valid}")
    
except Exception as e:
    print(f"Error: {e}")
