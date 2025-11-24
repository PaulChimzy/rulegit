from langchain_core.tools import tool
from tavily import TavilyClient
from termcolor import colored
import os
import time
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key= os.getenv("TAVILY_API_KEY"))


@tool
def check_reddit_reviews(domain: str):
   """
   Description: Searches Reddit for consumer reviews
   for a given domain name (e.g., 'enroutejewelry.com').

   Input: A domain name as a string.

   Output: The search results from Reddit containing reviews or discussions about the domain.
   """
   print(colored(50 * "=", "green"))
   start_time = time.time()
   try:
      query = f"get the reddit reviews for {domain}"
      response = tavily_client.search(query, search_depth="advanced")

   except Exception as e:
      print(colored(f"Error retrieving reddit reviews for {domain}: {e}", "red"))
      response = {"Error": f"Error retrieving reddit reviews for {domain}: {e}"}

   finally:
      print(colored(f"[TIME] Time taken for reddit review check: {time.time() - start_time} seconds", "blue"))
   
   return response
