import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch, TavilyExtract
# from langchain.agents import AgentExecutor
from langchain.agents.agent import AgentExecutor
from langchain.agents import create_tool_calling_agent

from langchain_core.prompts import PromptTemplate

load_dotenv()

# Initialize model
llm = init_chat_model(ChatOpenAI, model_name="gpt-4", temperature=0)

# Initialize Tavily Search Tool
search_tool = TavilySearch(
    max_results=2,
    max_content_chars=4000,
    include_images=False,
    include_raw_content=False,
    include_domains=False,
    include_answer=False,
    include_sources=False
)

# Initialize Tavily Extract Tool
extract_tool = TavilyExtract()

# tools list
tools = [search_tool, extract_tool]

# Load your markdown prompt
with open(os.path.join(os.path.dirname(__file__), '../prompts/search_report.md'), 'r') as f:
    search_report_template = f.read()

# Define PromptTemplate (still dynamic)
prompt = PromptTemplate(template=search_report_template, input_variables=["input"])

# Create agent with the prompt template (not formatted yet)
agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
    verbose=True
)

# Create executor
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

# Now run agent with your input variable
user_input = "https://silverdz.youcan.store/"
response = agent_executor.run({"input": user_input})

print(response)
