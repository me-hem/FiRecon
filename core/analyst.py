import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

SYSTEM_INSTRUCTION = """
You are the AI explanation layer of FiRecon, an AI Finance Controller. The deterministic reconciliation controller is the financial source of truth.
You must NEVER override its status or invent financial facts. Use only the supplied evidence. Never invent amounts, dates, fees, taxes, refunds, settlements, bank credits, UTRs, transactions, or causes. 
Your task is to explain the controller decision for a finance operator, classify the situation, and recommend an appropriate operational action.
If evidence is insufficient to explain a discrepancy, explicitly say that it remains unresolved and recommend investigation/escalation. Do not guess.
For batch settlements, remember that one settlement can contain multiple payments and the bank credit is batch-level. Do not attribute the entire batch bank credit to one payment.
For duplicates, do not assume which record is legitimate unless the evidence establishes that.
For refunds, distinguish full and partial refunds.

Return ONLY valid JSON with exactly these fields:
{
  "classification": "short machine-readable classification",
  "explanation": "clear explanation for a finance operator",
  "recommended_action": "specific operational recommendation",
}
"""


def _parse_json(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("LLM response is not a JSON object")
    return value


def _normalise(result: Dict[str, Any], controller_status: str, controller_reason: str,) -> Dict[str, Any]:
    required = ["classification", "explanation", "recommended_action",]
    for key in required:
        if key not in result:
            raise ValueError(f"Missing field: {key}")

    if not isinstance(result["classification"], str):
        raise ValueError("Invalid classification")
    if not isinstance(result["explanation"], str):
        raise ValueError("Invalid explanation")
    if not isinstance(result["recommended_action"], str):
        raise ValueError("Invalid recommended_action")


    return {
        "classification": result["classification"].strip(),
        "explanation": result["explanation"].strip(),
        "recommended_action": result["recommended_action"].strip(),
        "controller_status": controller_status,
        "controller_reason": controller_reason,
        "model": LLM_MODEL,
        "source": "gemini",
    }


def _fallback(controller_status: str, controller_reason: str, error: str,) -> Dict[str, Any]:
    if controller_status == "EXCEPTION":
        action = "Investigate the exception using the supplied financial evidence. Do not auto-close."
    elif controller_status == "EXPLAINED":
        action = "Review the supporting evidence; no corrective action is recommended unless contrary evidence appears."
    else:
        action = "No additional action required."

    return {
        "classification": "AI_ANALYSIS_UNAVAILABLE",
        "explanation": (
            "AI analysis is unavailable. The deterministic controller remains "
            f"authoritative: {controller_status} / {controller_reason}."
        ),
        "recommended_action": action,
        "controller_status": controller_status,
        "controller_reason": controller_reason,
        "model": LLM_MODEL,
        "source": "fallback",
        "error": error,
    }


def analyze_financial_evidence(evidence: Dict[str, Any], controller_status: str, controller_reason: str,) -> Dict[str, Any]:
    if controller_status == "MATCHED" and controller_reason == "EXACT_MATCH":
        return {
            "classification": "EXACT_MATCH",
            "explanation": "The deterministic reconciliation engine found an exact match; no AI analysis is required.",
            "recommended_action": "No action required.",
            "controller_status": controller_status,
            "controller_reason": controller_reason,
            "model": LLM_MODEL,
            "source": "deterministic",
        }

    if not LLM_API_KEY:
        return _fallback(
            controller_status,
            controller_reason,
            "LLM_API_KEY is not configured.",
        )

    try:
        client = genai.Client(api_key=LLM_API_KEY)

        payload = {
            "controller_decision": {"status": controller_status, "reason": controller_reason,},
            "financial_evidence": evidence,
        }

        prompt = (
            "Analyze this FiRecon case. The controller decision is authoritative. "
            "Explain it using only the evidence and return only the requested JSON.\n\n"
            + json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        )

        chat = client.chats.create(
            model=LLM_MODEL,
            config={"system_instruction": SYSTEM_INSTRUCTION, "temperature": 0.1, "response_mime_type": "application/json",},
        )

        response = chat.send_message(prompt)

        return _normalise(_parse_json(response.text), controller_status, controller_reason,)

    except Exception as exc:
        return _fallback(controller_status, controller_reason, str(exc),)


if __name__ == "__main__":
    print("FiRecon LLM layer")
    print(f"Model: {LLM_MODEL}")
    print(f"API key configured: {'yes' if LLM_API_KEY else 'no'}")
