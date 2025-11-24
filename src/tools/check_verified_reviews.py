from langchain_core.tools import tool
from termcolor import colored
import requests
import json
import os
from dotenv import load_dotenv
import time

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


@tool
def get_trustpilot_review(domain: str):

    """
   Description: This function get trustpilot reviews for a given domain using Diffbot extraction tool.
   It helps to gather verified reviews from Trustpilot to assess the credibility of the domain.

   Input: A domain name as a string.
   
   Output: A dictionary containing extracted Trustpilot reviews or an error message.
   """
    print(colored(50 * "=", "green"))
    start_time = time.time()
    # print(f"[TIME] Starting trustpilot review extraction for: {domain} at {start_time}")

    print(f"[DEBUG] Domain: {domain}")

    try:
        url = f"https://www.trustpilot.com/review/{domain}"
        trustpilot_review = extract_with_diffbot.invoke(url)
        print(f"[DEBUG] Trustpilot review: {trustpilot_review}")
        
        if trustpilot_review is None:
            url = f"https://www.trustpilot.com/review/www.{domain}"
            trustpilot_review = extract_with_diffbot.invoke(url)
            print(f"[DEBUG] Trustpilot review 2: {trustpilot_review}")

    except Exception as e:
        print(colored(f"Error retrieving trustpilot review for {domain}: {e}", "red"))

    finally:
        print(colored(f"[TIME] Time taken for trustpilot review extraction: {time.time() - start_time} seconds", "blue"))

    return trustpilot_review
