from langchain_core.tools import tool
from urllib.parse import urlparse
import whois
from tld.exceptions import TldDomainNotFound, TldBadUrl
import json

# --- Get Domain Info ---
@tool
def get_domain_info(url: str) -> str:
    """
    Checks the domain registration information (like age) for a given website URL.
    Returns a string summary of the domain's creation date, expiration, and registrar.
    This is a critical first step for triage.
    """
    
    try:
        domain = urlparse(url).netloc
        domain_info = whois.whois(domain)

        if not domain_info.creation_date:
            return f"No domain info found for {domain}. This is a red flag."
        
        result= {"domain": domain,
                "creation_date": domain_info.creation_date,
                "expiration_date": domain_info.expiration_date,
                "registrar": domain_info.registrar}
        
        return json.dumps(result)
    
    except (TldDomainNotFound, TldBadUrl):
        return f"Could not check domain for {url}, unknown TLD. This is suspicious."
    
    except Exception as e:
       return f"Error getting domain info for {url}: {e}"