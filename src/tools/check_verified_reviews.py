from langchain_core.tools import tool
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

DIFFBOT_API_KEY = os.getenv("DIFFBOT_API_KEY")

@tool
def extract_with_diffbot(url: str):
   """Extract data from URL using Diffbot API"""
   base_url = f"https://api.diffbot.com/v3/analyze?token={DIFFBOT_API_KEY}"
    
   params = {
      'url': url
      }
   
   headers = {"accept": "application/json"}

   response = requests.request("GET", base_url, params=params, headers=headers)
    
   if "errorCode" in response.text:
      return None
    
   return json.loads(response.text)



def get_trustpilot_review(domain):
   """Get trustpilot review for a domain"""
   
   url = f"https://www.trustpilot.com/review/{domain}"
   trustpilot_review = extract_with_diffbot.invoke(url)

   if trustpilot_review:
      return trustpilot_review
   else:
      return {"Error": f"Error retrieving trustpilot review for {domain}"}




