from fastapi import  FastAPI
from tools.scrapper import main

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Service is up and running"}

@app.get("/validate_url")
def validate_url(url: str, mode: str = "requests"):
    
    # Placeholder for URL validation logic

    result = main(url=url, mode=mode)
    return {"url": url, "result": result}