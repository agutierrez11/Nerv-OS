import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

ANAKIN_API_KEY = os.getenv("ANAKIN_API_KEY")

def test_scrape():
    if not ANAKIN_API_KEY:
        print("Error: ANAKIN_API_KEY not found in environment!")
        return
        
    print(f"Testing Anakin URL Scraper using API Key: {ANAKIN_API_KEY[:10]}...")
    url = "https://api.anakin.io/v1/url-scraper"
    
    headers = {
        "X-API-Key": ANAKIN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "url": "https://example.com"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print("\n--- Scrape Job Submission ---")
        print("Status Code:", response.status_code)
        res_json = response.json()
        print("Response:", res_json)
        
        if response.status_code in (200, 202):
            job_id = res_json.get("jobId")
            print(f"Job ID obtained: {job_id}. Polling for status...")
            
            # Realizar polling
            for i in range(12):
                time.sleep(2)
                status_url = f"https://api.anakin.io/v1/url-scraper/{job_id}"
                status_resp = requests.get(status_url, headers={"X-API-Key": ANAKIN_API_KEY})
                
                print(f"Poll #{i+1} status: {status_resp.status_code}")
                if status_resp.status_code == 200:
                    status_json = status_resp.json()
                    status = status_json.get("status")
                    print(f"Job Status: {status}")
                    
                    if status == "completed":
                        content = status_json.get("content", "")
                        print("\n--- Scraped Content (First 200 chars) ---")
                        # Evitar emojis o caracteres raros al imprimir para evitar charmap crash en Windows
                        safe_print = content[:200].encode('ascii', errors='ignore').decode('ascii')
                        print(safe_print)
                        print("\nAnakin API key works and job completed successfully!")
                        return
                    elif status == "failed":
                        print("Job failed. Error details:", status_json.get("error"))
                        return
                else:
                    print("Status API Error:", status_resp.text)
            
            print("Timeout waiting for job completion.")
        else:
            print("API returned error status. Check key permissions or endpoint.")
            
    except Exception as e:
        print("Exception occurred:", e)

if __name__ == "__main__":
    test_scrape()
