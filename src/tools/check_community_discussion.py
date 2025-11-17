from langchain_core.tools import tool
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key= os.getenv("TAVILY_API_KEY"))


@tool
def check_reddit_reviews(domain: str):
   """
   Searches Reddit for consumer reviews
   for a given domain name (e.g., 'enroutejewelry.com').
   """
   query = f"get the reddit reviews for {domain}"

   response = tavily_client.search(query, search_depth="advanced")
   return response