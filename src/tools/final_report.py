from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# --- 2. DEFINE THE PYDANTIC "FINAL ANSWER" SCHEMA ---

class TrustReport(BaseModel):
   """The structured trust report for the web extension."""
   risk_level: Literal["Low", "Medium", "High", "Critical"] = Field(..., description="The overall risk level assessed.")
   explanation: str = Field(..., description="A 1-2 sentence summary explaining the risk level for the user.")
   red_flags: List[str] = Field(..., description="A bullet-point list of 3-5 specific red flags found.")
   confidence: Literal["High", "Medium", "Low"] = Field(..., description="The confidence level of this assessment (e.g., 'Low' if data is scarce).")



#  "Final Answer" Tool  ---
@tool(args_schema=TrustReport)
def submit_final_report(risk_level: str, explanation: str, red_flags: List[str], confidence: str) -> str:
   """
   Call this tool ONLY when you have completed all investigations, performed your
   final self-correction review, and are ready to provide the final trust report.
   """
   return f"Final report submitted. Risk: {risk_level}, Confidence: {confidence}"