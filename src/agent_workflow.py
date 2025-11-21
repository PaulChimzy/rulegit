import os
import json
from termcolor import colored
from dotenv import load_dotenv
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from tools.scrapper import scrape_url_info
from tools.get_domain_info import get_domain_info
from langchain_core.prompts import PromptTemplate
from tools.check_verified_reviews import get_trustpilot_review, extract_with_diffbot
from tools.final_report import submit_final_report, TrustReport
from tools.check_community_discussion import check_reddit_reviews
import time


def get_system_prompt(file_path: str, all_tools: List) -> str:
    try:
        with open(file_path, "r", encoding="UTF-8") as file:
            system_prompt = file.read()

        agent_template = PromptTemplate(
            input_variables=["agent_tools"],
            template=system_prompt,
        )
        agent_tools = {
            f"{tool}" : f"{tool.__doc__}" 
            for tool in all_tools
        }

        system_prompt = agent_template.format(
            agent_tools=json.dumps(agent_tools)
        )

        print("Agent prompt loaded successfully!")
        return system_prompt

    except FileNotFoundError:
        print(f"Error: System prompt file not found at {system_prompt}.")

    except KeyError as e:
        print(
            f"Error: Missing key in system prompt file: {e}. Check the 'agent_config' and 'system_prompt' keys."
        )

# THE PYDANTIC "FINAL ANSWER" SCHEMA ---
class TrustReport(BaseModel):
    """The structured trust report for the web extension."""

    risk_level: Literal["Low", "Medium", "High", "Mixed", "Critical"] = Field(
        ..., description="The overall risk level assessed."
    )
    rationale: List[str] = Field(
        ...,
        description="A bullet-point list of 3-5 specific rationales for the score. Key evidence (e.g., “Domain created last week,” “Users report non-delivery,” “No digital footprint”)",
    )
    confidence_level: str = Field(
        ...,
        description="The confidence level of this assessment (low | medium | High). This should reflect how certain you are about your analysis.",
    )

# MAIN AGENT WORKFLOW ---
def run_agent_workflow(url: str) -> TrustReport:
    start_time = time.time()
    prompt_file_path = "prompts/refined_prompt.md"

    all_tools = [
        get_domain_info,
        scrape_url_info,
        check_reddit_reviews,
        get_trustpilot_review,
        submit_final_report,
    ]

    input_prompt = get_system_prompt(prompt_file_path, all_tools)
    llm = ChatOpenAI(model="gpt-5-nano")
    agent = create_agent(
        model=llm,
        tools=all_tools,
        system_prompt=input_prompt
        # response_format=TrustReport,
    )

    # response = agent.invoke(
    #     {
    #         "messages": [
    #             {"role": "user", "content": f"Is this domain legit {url}. Strictly use the domain name as provided without converting to url"}
    #         ]
    #     }
    # )
    count = 0
    print(colored(50 * "=", "green"))
    for chunk in agent.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Is this domain legit {url}. Strictly use the domain name as provided without converting to url",
                }
            ]
        },
        stream_mode="updates",
    ):
        for step, data in chunk.items():
            print(f"step: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")
        
        print(colored(50 * "=", "green"))
        print("\n\n")

    print(colored(f"[TIME] Time taken for agent workflow: {time.time() - start_time} seconds", "blue"))

    # return response["structured_response"].model_dump()
    return {"status": "Done streaming"}


if __name__ == "__main__":

    # load_dotenv()

    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # prompt_file_path = "prompts/system_prompt.md"

    # all_tools = [
    #     get_domain_info,
    #     scrape_url_info,
    #     check_reddit_reviews,
    #     get_trustpilot_review,
    #     submit_final_report,
    # ]

    # input_prompt = get_system_prompt(prompt_file_path)
    # llm = ChatOpenAI(model="gpt-5-nano")
    # agent = create_agent(
    #     model=llm, tools=all_tools, system_prompt=input_prompt, response_format=TrustReport
    # )

    # response = agent.invoke(
    #     {
    #         "messages": [
    #             {"role": "user", "content": "Is this domain legit enroutejewelry.com"}
    #         ]
    #     }
    # )

    # print(response)

    # print(50 * "=")
    # final_report: TrustReport = response["structured_response"]
    # print(final_report)

    report = TrustReport(
        risk_level="Medium",
        explanation="Phase 1 shows an aged domain (since 2017) with a reputable registrar (Squarespace) and HTTPS in place, but owner/admin info is privacy-protected. Phase 2 reveals neutral technical signals with no active blacklist or obvious malware indicators. Phase 3 Reddit mentions are mixed and raise some concerns (dropshipping/origin questions). Phase 4 Trustpilot data was not retrievable in this run. Overall, there isn’t clear fraud evidence, but signals are mixed and not definitively legitimate either; exercise caution for purchases.",
        red_flags=[
            "Privacy/protected owner and administrative contacts",
            "Redacted company/address details on site and WHOIS data",
            "Reddit discussions suggesting potential dropshipping or origin concerns",
            "Trustpilot data not retrievable in this session (data availability issue)",
        ],
        confidence_score=0.6,
    )

    print(report.__dict__)
