from tools.get_domain_info import get_domain_info
from tests.test_domains import GOOD_DOMAINS, BAD_DOMAINS
import json
from datetime import datetime, timedelta
from dateutil import parser
import pytz


# Test with legitimate sites
def test_get_good_domains():
    print("Testing with legitimate sites:")
    cnt = 0
    new = set()
    no_domain = set()

    for domain in GOOD_DOMAINS:
        res_str = get_domain_info.invoke({"url": domain})
        
        res = json.loads(res_str)
        if res.get("error"):
            no_domain.add(domain)
            continue

        date_str = res["creation_date"]
        creation_date = parser.parse(date_str)
        cutoff_date = datetime.now(pytz.UTC) - timedelta(days=3*365)
        
        # Add a count if the domain matches the logic that the domain was created a while ago
        if creation_date < cutoff_date:
            cnt +=1
        else:
            new.add((domain, date_str))

    print(f"Summary of good domains: {len(GOOD_DOMAINS)}")
    print(f"Number of older domains: {cnt}")
    print("Newer domains:")
    for item in new:
        print(item)
    print(f"No domain: {no_domain}")
    print()

# Test with legitimate sites
def test_get_bad_domains():
    print("Testing with bad sites:")
    cnt = 0
    no_domain = set()
    old = set()

    for domain in BAD_DOMAINS:
        res_str = get_domain_info.invoke({"url": domain})
    
        res = json.loads(res_str)

        if res.get("error"):
            no_domain.add(domain)
            continue

        date_str = res["creation_date"]
        creation_date = parser.parse(date_str)
        cutoff_date = datetime.now(pytz.UTC) - timedelta(days=3*365)

        # Add count if the domain matches the logic that the domain was created just recently
        if creation_date > cutoff_date:
            cnt +=1
        else:
            old.add((domain, date_str))

    print(f"Summary of good domains: {len(BAD_DOMAINS)}")
    print(f"Number of newer domains: {cnt}")
    print("Old domains:")
    for item in old:
        print(item) 
    print(f"No domain: {no_domain}")

    
if __name__ == "__main__":
    test_get_good_domains()
    test_get_bad_domains()

