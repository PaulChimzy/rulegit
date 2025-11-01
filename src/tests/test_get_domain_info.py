from tools.get_domain_info import get_domain_info

# Test with legitimate sites
print("Testing Amazon:")
print(get_domain_info.invoke({"url": "https://amazon.com"}))
print()

print("Testing Google:")
print(get_domain_info.invoke({"url": "https://google.com"}))
print()

# Test with suspicious/newer domain
print("Testing newer domain:")
print(get_domain_info.invoke({"url": "https://example.com"}))