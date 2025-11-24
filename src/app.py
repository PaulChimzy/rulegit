import os
from fastapi import  FastAPI
from tools.scrapper import scrape_url_info
from dotenv import load_dotenv
from agent_workflow import run_agent_workflow
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or chrome-extension://your-id
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def read_root():
    return {"message": "Service is up and running"}

@app.get("/validate_url")
def validate_url(url: str = "enroutejewelry.com", mode: str = "requests"):

    # Placeholder for URL validation logic

    print("🧠 Running LLM analysis ...")

    result = run_agent_workflow(url=url)
    result.update({"url": url})
    
    return result

    # return {
    #     "Risk Level": "Medium",
    #     "Rationale": [
    #         "Domain age (~30 years) and MarkMonitor in the registrar field strongly support legitimacy for amazon.com.",
    #         "Scam Detector outputs show no blacklist hits, valid HTTPS, and ownership/registrar alignment with Amazon Technologies, Inc., indicating reputable infrastructure.",
    #         "Reddit and Trustpilot signals reflect generalized consumer feedback (mixed experiences) but do not indicate domain-level fraud or deception.",
    #     ],
    #     "Confidence Level": 60,
    # }
