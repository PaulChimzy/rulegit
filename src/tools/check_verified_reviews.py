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
   try:
      base_url = f"https://api.diffbot.com/v3/analyze?token={DIFFBOT_API_KEY}"
       
      params = {
         'url': url
         }
      
      headers = {"accept": "application/json"}

      response = requests.request("GET", base_url, params=params, headers=headers)
      response.raise_for_status()
       
      if "errorCode" in response.text:
         return None
       
      return json.loads(response.text)
   except requests.exceptions.RequestException as e:
      return {"Error": f"Request failed: {str(e)}"}
   except json.JSONDecodeError as e:
      return {"Error": f"JSON decode error: {str(e)}"}
   except Exception as e:
      return {"Error": f"Unexpected error: {str(e)}"}



def get_trustpilot_review(domain):
   """Get trustpilot review for a domain"""
   try:
      url = f"https://www.trustpilot.com/review/{domain}"
      trustpilot_review = extract_with_diffbot.invoke(url)

      if trustpilot_review and "Error" not in trustpilot_review:
         return trustpilot_review
      else:
         return {"Error": f"Error retrieving trustpilot review for {domain}"}
   except Exception as e:
      return {"Error": f"Failed to get trustpilot review for {domain}: {str(e)}"}




