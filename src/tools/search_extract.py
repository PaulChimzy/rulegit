# core imports (your existing environment)
import os
import json
from dotenv import load_dotenv
from langchain_tavily import TavilySearch, TavilyExtract
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
# from langchain.agents import create_openai_tools_agent, AgentExecutor

load_dotenv("../../.env")

# Configuration
MODEL_NAME = "gpt-4"
TEMPERATURE = 0
MAX_RESULTS = 8
MAX_EXTRACTS = 10
MAX_CONTENT_CHARS = 4000


# init LLM
# llm = init_chat_model(ChatOpenAI, model_name=MODEL_NAME, temperature=TEMPERATURE)

# Tavily Search: expand query set per-platform
search_tool = TavilySearch(
    max_results=MAX_RESULTS,
    # max_content_chars=MAX_CONTENT_CHARS,
    # k=100,  # semantic retrieval window (optional)
    # include_images=False,
    # include_raw_content=False,
    # include_domains=True,  # useful to see domain
    # include_answer=False,
    # include_sources=True,
)

# Tavily Extract: pull full content for a url
extract_tool = TavilyExtract()

tools = [search_tool, extract_tool]


# helper: build platform-targeted queries
def build_queries(domain):
    """Generate platform-targeted queries for multi-source analysis."""
    base = [
        f'"{domain}" review',
        f'"{domain}" scam',
        f'"{domain}" complaint',
        f'"{domain}" feedback',
        f'"{domain}" refund',
        f'"{domain}" not delivered',
        f'"{domain}" customer experience',
        f'"{domain}" site review',
        f'"{domain}" legit',
        f'"{domain}" fraudulent',

    ]
    platforms =  [
        f'site:reddit.com "{domain}"',
        f'site:trustpilot.com "{domain}"',
        f'site:yelp.com "{domain}"',
        f'site:quora.com "{domain}"',
        f'site:twitter.com "{domain}" scam',
        f'site:facebook.com "{domain}" reviews',
    ]

    return base + platforms


# run searches across mltiple queries and collect results
def run_searches(domain):
    queries = build_queries(domain)
    results = []
    for q in queries:
        try:
            res = search_tool.invoke({"query": q})  # returns structured results depending on SDK
            # store results (title, snippet, url, domain, platform tag)
            # structure depends on Tavily SDK return format
            results.append({"query": q, "raw": res})
        except Exception as e:
            print(f"Error running search for query '{q}': {e}")

        break
    return results


def extract_urls(urls):
    """Extract content from each URL using TavilyExtract."""
    extracted = []
    for url in urls[:MAX_EXTRACTS]:
        try:
            res = extract_tool.invoke({"urls": [url]})
            extracted.append({"url": url, "content": res})
        except Exception as e:
            print(f"Extraction error for {url}: {e}")
    return extracted


# Load markdown prompt
prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/extract_prompt.md')

with open(prompt_path, 'r') as f:
    prompt_template = f.read()

# Define PromptTemplate (still dynamic)
prompt = PromptTemplate(
    input_variables=["domain", "search_results", "extracted_contents"],
    template=prompt_template,
)

# Create agent with the prompt template (not formatted yet)
# agent = create_openai_tools_agent(llm, tools, prompt, verbose=True)
# agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

# Execute search and extraction
if __name__ == "__main__":
    domain = "silverdz.youcan.store"
    search_results = run_searches(domain)

    # Collect URLs from search results for extraction
    urls_to_extract = []
    for result in search_results:
        print(result)
        if isinstance(result.get("raw"), dict):
            for entry in result.get("raw", {}).get("results", []):
                if "url" in entry:
                    urls_to_extract.append(entry.get("url"))
    
    
    urls = list(set(urls_to_extract))  # deduplicate
    print(f"Extracting content from {len(urls)} unique URLs...")

    extracted_contents = extract_urls(urls)

    # Run agent with collected data
    search_results_formatted = [
        {
            "query": res["query"],
            "results": res.get("raw", {}).get("results", [])
        }
        for res in search_results
    ]

    agent_input = {
        "domain": domain,
        "search_results": search_results_formatted,
        "extracted_contents": extracted_contents
    }

    # Save input to JSON for debugging
    with open("../test/search_extraction.json", "w") as f:
        json.dump(agent_input, f, indent=4)

    # print("🧠 Running LLM analysis ...")
    # response = agent_executor.run(agent_input)

    # Save output to JSON
    # with open("../test/test_search_report_output.json", "w") as f:
    #     import json
    #     json.dump(search_results, f, indent=4)
    # print(search_results)
