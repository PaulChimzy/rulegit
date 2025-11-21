import os
from fastapi import  FastAPI
from tools.scrapper import scrape_url_info
from dotenv import load_dotenv
from agent_workflow import run_agent_workflow

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/health")
def read_root():
    return {"message": "Service is up and running"}

@app.get("/validate_url")
def validate_url(url: str = "enroutejewelry.com", mode: str = "requests"):
    
    # Placeholder for URL validation logic

    result = run_agent_workflow(url=url)
    return {"url": url, "result": result}
