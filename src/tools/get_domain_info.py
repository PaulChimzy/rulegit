from langchain_core.tools import tool
from urllib.parse import urlparse
import whois
from whois.exceptions import UnknownTldError
import json
import time
from termcolor import colored

# --- Get Domain Info ---
@tool
def get_domain_info(url: str) -> str:
    """
    Description: Checks the domain registration information (like age) for a given URL or domain.
    Accepts both full URLs (https://example.com) and domain names (example.com).
    Returns a JSON string with domain creation date, expiration, and registrar.
    This is a critical first step for triage.

    Input: A URL or domain name as a string.

    Output: A JSON string containing domain information or an error message.
    """
    print(colored(50 * "=", "green"))
    start_time = time.time()
    
    try:   
        domain_info = whois.whois(url)

        if not domain_info or not domain_info.creation_date:
            return json.dumps({"error": f"No domain info found for {url}. This is a red flag."})
        
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0] if creation_date else None
        
        expiration_date = domain_info.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0] if expiration_date else None
        
        result = {
            "domain": domain_info.domain_name,
            "creation_date": str(creation_date) if creation_date else None,
            "expiration_date": str(expiration_date) if expiration_date else None,
            "registrar": domain_info.registrar
        }
        
        return json.dumps(result, indent=2)
    
    except UnknownTldError:
        return json.dumps({"domain": url, 
                           "error": "Could not check domain for domain, unknown TLD."})
    
    except Exception as e:
       return json.dumps({"domain": url, 
                           "error": f"Error getting domain info: {e}"})
    
    finally:
        print(f"[TIME] Time taken for get_domain_info: {time.time() - start_time} seconds")