from tools.check_community_discussion import check_reddit_reviews
from tests.test_domains import GOOD_DOMAINS, BAD_DOMAINS


def test_reddit_reviews_good_domain():
    """Test Reddit reviews for good domain"""
    domain = GOOD_DOMAINS[0]
    print(f"\nTesting good domain: {domain}")
    
    result = check_reddit_reviews.invoke(domain)
    print(f"Result: {result}")
    
    assert isinstance(result, dict)
    assert "results" in result


def test_reddit_reviews_bad_domain():
    """Test Reddit reviews for bad domain"""
    domain = BAD_DOMAINS[0]
    print(f"\nTesting bad domain: {domain}")
    
    result = check_reddit_reviews.invoke(domain)
    print(f"Result: {result}")
    
    assert isinstance(result, dict)
    assert "results" in result


if __name__ == "__main__":
    test_reddit_reviews_good_domain()
    test_reddit_reviews_bad_domain()