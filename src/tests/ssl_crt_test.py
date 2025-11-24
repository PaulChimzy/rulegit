import json
import pandas as pd
from tools.get_ssl_crt import extract_cert_info

# test_urls = pd.read_csv("Misleading e-commerce websites - Sheet1.csv")

# dict_urls = {
#     "urls": test_urls['Website'].tolist(),
#     "legit": test_urls['Is legitimate business?'].tolist()
# }

# with open("test_urls.json", "w") as f:
#     import json
#     json.dump(dict_urls, f, indent=4)

test_urls = json.load(open("test/test_urls.json"))
list_cert_info = []
for i, url in enumerate(test_urls['urls']):
    print(f"Testing {i+1}/{len(test_urls['urls'])}: {url}")
    cert_info = extract_cert_info(url)
    cert_info["legit"] = test_urls['legit'][i]
    list_cert_info.append(cert_info)

df_cert_info = pd.DataFrame(list_cert_info)
df_cert_info.to_csv("test/test_cert_info.csv", index=False)