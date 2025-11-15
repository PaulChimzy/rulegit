from tools.check_verified_reviews import extract_with_diffbot, get_trustpilot_review
from tests.test_domains import GOOD_DOMAINS, BAD_DOMAINS


def test_trustpilot_good_domains():
    """Test Trustpilot reviews for good domains"""
    print("Testing Trustpilot reviews for good domains:")
    
    review_found_count = 0
    review_not_found = []
    totat_cnt = 0

    for domain in GOOD_DOMAINS[:3]:  
        totat_cnt += 1
        print("...")
        # print(f"\nTesting {domain}:")
        result = get_trustpilot_review(domain)
        
        if "Error" in result:
            # print(f"  No Trustpilot review found")
            review_not_found.append(domain)
        else:
            # print(f"  Found Trustpilot data")
            review_found_count += 1

    print(f"Summary for {totat_cnt} domains:")
    print(f"Total reviews found: {review_found_count}")
    print(f"Domains with reviews not found: {review_not_found}")


def test_trustpilot_bad_domains():
    """Test Trustpilot reviews for bad domains"""
    print("\nTesting Trustpilot reviews for bad domains:")

    review_not_found_count= 0
    review_found = []
    total_cnt = 0
    
    for domain in BAD_DOMAINS[:3]: #testing first 3 domains
        total_cnt += 1
        print("...") 
        # print(f"\nTesting {domain}:")
        result = get_trustpilot_review(domain)
        
        if "Error" in result:
            # print(f"  No Trustpilot review found")
            review_not_found_count +=1
        else:
            # print(f"  Found Trustpilot data")
            review_found.append(domain)

    print(f"Summary for {total_cnt} domains:")
    print(f"Total reviews not found: {review_not_found_count}")
    print(f"Domains with reviews found: {review_found}")


def test_diffbot_extraction():
    """Test Diffbot extraction with sample URLs"""
    print("\nTesting Diffbot extraction:")
    
    test_url = "https://www.trustpilot.com/review/burga.com"
    result = extract_with_diffbot.invoke(test_url)
    
    if result:
        print(f"  Successfully extracted data from {test_url}")
    else:
        print(f"  Failed to extract data from {test_url}")


if __name__ == "__main__":
    test_trustpilot_good_domains()
    test_trustpilot_bad_domains()
    test_diffbot_extraction()