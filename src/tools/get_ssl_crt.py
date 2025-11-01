import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime
import json

def get_ssl_cert(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or 443
    
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            return ssock.getpeercert()

def extract_cert_info(url):
    cert = get_ssl_cert(url)

    # Helper function to safely extract a field
    def safe_get(dic, key, default=None):
        return dic.get(key, default) if isinstance(dic, dict) else default

    cert_info = {
        "subject_common_name": None,
        "subject_alt_names": [],
        "issuer": {},
        "valid_from": cert.get("notBefore"),
        "valid_until": cert.get("notAfter"),
        "serial_number": cert.get("serialNumber"),
        "version": cert.get("version"),
        "raw_subject": cert.get("subject"),
        "raw_issuer": cert.get("issuer"),
    }

    # Extract subject common name
    for item in cert.get("subject", []):
        for key, value in item:
            if key == "commonName":
                cert_info["subject_common_name"] = value

    # Extract issuer info
    issuer_dict = {}
    for item in cert.get("issuer", []):
        for key, value in item:
            issuer_dict[key] = value
    cert_info["issuer"] = issuer_dict

    # Extract Subject Alternative Names
    alt_names = []
    for typ, name in cert.get("subjectAltName", []):
        if typ == "DNS":
            alt_names.append(name)
    cert_info["subject_alt_names"] = alt_names

    # Convert validity dates to ISO format for JSON
    fmt = "%b %d %H:%M:%S %Y %Z"
    try:
        cert_info["valid_from_iso"] = datetime.strptime(cert["notBefore"], fmt).isoformat()
        cert_info["valid_until_iso"] = datetime.strptime(cert["notAfter"], fmt).isoformat()
    except Exception:
        pass

    return cert_info

# Example usage
if __name__ == "__main__":
    url = "https://google.com"
    info = extract_cert_info(url)
    print(json.dumps(info, indent=2))
