"""
orchestrator.py
-------------------------------------------------------------------------------
The AI Nutrition Assistant's orchestrator (Section 17-18).

Two modes, chosen automatically by src/utils/config.py:LLM_ASSISTANT_ENABLED:

1. LLM MODE (ANTHROPIC_API_KEY is set and DEMO_MODE=false):
   Uses Anthropic's tool-use ("function calling") feature. The LLM can only
   act by calling the tool functions in tools.py -- it cannot invent
   nutrition numbers itself. See prompts.py for the safety system prompt.

2. RULE-BASED FALLBACK MODE (default, no API key needed):
   A simple, transparent keyword/intent router. It is intentionally
   readable: every "if this phrase is in the message, call that tool"
   branch can be explained line-by-line in a viva. This keeps the whole
   application demonstrable with ZERO external API keys (Section 29).

Both modes funnel every actual calculation through tools.py, and both
refuse medical-advice questions using the same keyword safety net
(prompts.MEDICAL_ADVICE_TRIGGER_KEYWORDS) before anything else runs.
-------------------------------------------------------------------------------
"""

import json
import re
from dataclasses import dataclass
from typing import List, Optional

from src.agent import tools
from src.agent.prompts import MEDICAL_ADVICE_REFUSAL_MESSAGE, MEDICAL_ADVICE_TRIGGER_KEYWORDS, SYSTEM_PROMPT
from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    text: str
    data: Optional[dict] = None
    mode: str = "rule_based"  # "rule_based" or "llm"


def _mentions_medical_advice(message: str) -> bool:
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in MEDICAL_ADVICE_TRIGGER_KEYWORDS)


def handle_user_message(user_id: int, message: str, image_bytes: Optional[bytes] = None) -> AgentResponse:
    """
    Main entry point used by the Streamlit "AI Nutrition Assistant" page.
    """
    if _mentions_medical_advice(message):
        return AgentResponse(text=MEDICAL_ADVICE_REFUSAL_MESSAGE, mode="safety_refusal")

    if config.LLM_ASSISTANT_ENABLED:
        try:
            return _handle_with_llm(user_id, message, image_bytes)
        except Exception as exc:
            logger.warning("LLM assistant call failed (%s); falling back to rule-based mode.", exc)

    return _handle_with_rules(user_id, message, image_bytes)


# ==============================================================================
# RULE-BASED FALLBACK (no external API key required)
# ==============================================================================

def _handle_with_rules(user_id: int, message: str, image_bytes: Optional[bytes]) -> AgentResponse:
    text = message.lower()

    if image_bytes:
        result = tools.analyze_scanned_label(image_bytes, user_id)
        return AgentResponse(text=_format_scan_result(result), data=result)

    if any(p in text for p in ["what should i eat", "eat next", "eat today", "eat now", "recommend"]):
        meal_type = _extract_meal_type(text)
        result = tools.suggest_next_foods(user_id, meal_type=meal_type)
        return AgentResponse(text=_format_next_food_result(result), data=result)

    if any(p in text for p in ["how many calories", "how much have i", "consumed", "my intake today"]):
        consumption = tools.get_daily_consumption(user_id)
        remaining = tools.get_remaining_targets_today(user_id)
        return AgentResponse(text=_format_consumption(consumption, remaining), data={"consumption": consumption, "remaining": remaining})

    if any(p in text for p in ["meal plan", "plan my meals", "create a plan"]):
        result = tools.generate_meal_plan(user_id)
        return AgentResponse(text=_format_meal_plan(result), data=result)

    replace_match = re.search(r"replace\s+([a-zA-Z\s]+?)(?:\s+with|\?|$)", text)
    if replace_match or "substitut" in text or "alternative to" in text:
        food_name = None
        if replace_match:
            food_name = replace_match.group(1).strip()
        else:
            for pattern in [r"substitut\w*\s+for\s+([a-zA-Z\s]+)", r"alternative to\s+([a-zA-Z\s]+)"]:
                m = re.search(pattern, text)
                if m:
                    food_name = m.group(1).strip()
                    break
        if food_name:
            result = tools.suggest_substitutions(user_id, food_name)
            return AgentResponse(text=_format_substitutions(result), data=result)

    if any(p in text for p in ["this week", "weekly", "past week", "last 7 days"]):
        result = tools.get_weekly_summary(user_id)
        return AgentResponse(text=_format_weekly_summary(result), data=result)

    if any(p in text for p in ["my target", "my profile", "bmi", "bmr", "how many calories should i"]):
        result = tools.get_daily_targets(user_id)
        return AgentResponse(text=_format_targets(result), data=result)

    return AgentResponse(
        text=(
            "I can help with: 'What should I eat next?', 'How many calories have I consumed?', "
            "'Create a meal plan', 'Can I replace X with something else?', "
            "'How has my nutrition been this week?', or you can upload a food label photo to analyze it. "
            "What would you like to do?"
        ),
    )


def _extract_meal_type(text: str) -> Optional[str]:
    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        if meal in text:
            return meal
    return None


def _format_next_food_result(result: dict) -> str:
    if "error" in result:
        return result["error"]
    if not result.get("recommendations"):
        return "No suitable foods were found under your current constraints. Try relaxing a preference or logging fewer restrictions."
    lines = [f"Based on your remaining {result['remaining_calories']:.0f} kcal and {result['remaining_protein_g']:.0f}g protein today, here are some options:"]
    for rec in result["recommendations"]:
        lines.append(f"- {rec['name']} (score {rec['score']:.2f}): {', '.join(rec['reasons'])}")
    return "\n".join(lines)


def _format_consumption(consumption: dict, remaining: dict) -> str:
    totals = consumption["totals"]
    lines = [f"So far today ({consumption['entries_count']} items logged):",
             f"Calories: {totals['calories']:.0f} kcal | Protein: {totals['protein_g']:.0f}g | Carbs: {totals['carbohydrates_g']:.0f}g | Fat: {totals['fat_g']:.0f}g"]
    if remaining:
        lines.append(f"Estimated remaining today: {remaining['calories']:.0f} kcal, {remaining['protein_g']:.0f}g protein.")
    else:
        lines.append("No nutrition targets calculated yet -- visit the Profile page first.")
    return "\n".join(lines)


def _format_meal_plan(result: dict) -> str:
    if "error" in result:
        return result["error"]
    lines = [f"Generated meal plan (target: {result['target_calories']:.0f} kcal, {result['target_protein_g']:.0f}g protein):"]
    for item in result["items"]:
        food_name = item["food_name"] or "No suitable food found"
        lines.append(f"- {item['meal_slot'].replace('_', ' ').title()}: {food_name}")
    lines.append(f"Estimated total: {result['total_calories']:.0f} kcal ({result['calorie_difference']:+.0f} vs target), "
                 f"{result['total_protein_g']:.0f}g protein ({result['protein_difference']:+.0f} vs target).")
    lines.append("Note: this is an estimate, not a guarantee of exact nutritional accuracy.")
    return "\n".join(lines)


def _format_substitutions(result: dict) -> str:
    if "error" in result:
        return result["error"]
    lines = [f"Possible substitutes for {result['original_food']}:"]
    for s in result["substitutes"]:
        lines.append(f"- {s['name']} (similarity score {s['score']:.2f}): {', '.join(s['reasons'])}")
    return "\n".join(lines) if result["substitutes"] else f"No suitable substitutes for {result['original_food']} were found."


def _format_weekly_summary(result: dict) -> str:
    if result.get("days_logged", 0) == 0:
        return result.get("message", "No data logged yet this week.")
    avg = result["average_daily"]
    lines = [
        f"Weekly summary ({result['date_range']}, {result['days_logged']} day(s) with logged food):",
        f"Average daily: {avg['calories']:.0f} kcal, {avg['protein_g']:.0f}g protein, {avg['carbohydrates_g']:.0f}g carbs, {avg['fat_g']:.0f}g fat.",
    ]
    if result["days_below_protein_target"] > 0:
        lines.append(f"Your logged protein intake was below your target on {result['days_below_protein_target']} of the last {result['days_logged']} logged days.")
    return "\n".join(lines)


def _format_targets(result: dict) -> str:
    if "error" in result:
        return result["error"]
    return (
        f"BMI: {result['bmi']} ({result['bmi_category']}) | BMR: {result['bmr_kcal']:.0f} kcal | "
        f"Estimated daily needs: {result['tdee_kcal']:.0f} kcal | "
        f"Goal-adjusted calorie target: {result['calorie_target_kcal']:.0f} kcal | "
        f"Protein target: {result['protein_target_g']:.0f}g | Carb target: {result['carb_target_g']:.0f}g | "
        f"Fat target: {result['fat_target_g']:.0f}g\n"
        f"(All values are estimates based on standard formulas -- see the Nutrition Plan page for details.)"
    )


def _format_scan_result(result: dict) -> str:
    lines = [f"Scanned label (OCR mode: {result['ocr_mode']}, confidence {result['ocr_confidence']:.0%}):"]
    if result["parsed_nutrition"]:
        nutrition_str = ", ".join(f"{k}: {v}" for k, v in result["parsed_nutrition"].items())
        lines.append(f"Parsed nutrition -- {nutrition_str}")
    if result["parsing_warnings"]:
        lines.append("Warnings: " + "; ".join(result["parsing_warnings"]))
    if result["allergen_warnings"]:
        lines.append("ALLERGEN NOTICE: " + "; ".join(result["allergen_warnings"]))
        lines.append(result["allergen_disclaimer"])
    if "suitability_label" in result:
        lines.append(f"Suitability: {result['suitability_label']}")
    return "\n".join(lines)


# ==============================================================================
# OPTIONAL LLM MODE (Anthropic tool-use) -- only runs if an API key is configured
# ==============================================================================

TOOL_SPECS = [
    {"name": "get_user_profile", "description": "Get the user's stored profile.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_daily_targets", "description": "Get the user's estimated daily nutrition targets (calories, protein, carbs, fat).",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "search_foods", "description": "Search the food database.",
     "input_schema": {"type": "object", "properties": {
         "query_text": {"type": "string"}, "meal_type": {"type": "string"}}, "required": []}},
    {"name": "suggest_next_foods", "description": "Recommend foods to eat next based on remaining daily nutrition targets.",
     "input_schema": {"type": "object", "properties": {"meal_type": {"type": "string"}}, "required": []}},
    {"name": "get_daily_consumption", "description": "Get what the user has eaten today and totals.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "generate_meal_plan", "description": "Generate a full daily meal plan for the user.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "suggest_substitutions", "description": "Suggest nutritionally similar substitutes for a named food.",
     "input_schema": {"type": "object", "properties": {"food_name": {"type": "string"}}, "required": ["food_name"]}},
    {"name": "get_weekly_summary", "description": "Get a 7-day nutrition summary and insights.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
]

_TOOL_FUNCTION_MAP = {
    "get_user_profile": lambda user_id, args: tools.get_user_profile(user_id),
    "get_daily_targets": lambda user_id, args: tools.get_daily_targets(user_id),
    "search_foods": lambda user_id, args: tools.search_foods(**args),
    "suggest_next_foods": lambda user_id, args: tools.suggest_next_foods(user_id, **args),
    "get_daily_consumption": lambda user_id, args: tools.get_daily_consumption(user_id),
    "generate_meal_plan": lambda user_id, args: tools.generate_meal_plan(user_id),
    "suggest_substitutions": lambda user_id, args: tools.suggest_substitutions(user_id, **args),
    "get_weekly_summary": lambda user_id, args: tools.get_weekly_summary(user_id),
}


def _handle_with_llm(user_id: int, message: str, image_bytes: Optional[bytes]) -> AgentResponse:
    import anthropic  # imported lazily so the package is only required when actually used

    if image_bytes:
        # Image analysis always goes through the deterministic scanner pipeline,
        # never through the LLM directly (Section 17: tools do the real work).
        result = tools.analyze_scanned_label(image_bytes, user_id)
        return AgentResponse(text=_format_scan_result(result), data=result, mode="llm")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    messages: List[dict] = [{"role": "user", "content": message}]

    for _ in range(5):  # hard cap on tool-call loop iterations, avoids runaway loops
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SPECS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if block.type == "text")
            return AgentResponse(text=final_text, mode="llm")

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            handler = _TOOL_FUNCTION_MAP.get(block.name)
            if not handler:
                tool_output = {"error": f"Unknown tool '{block.name}'."}
            else:
                try:
                    tool_output = handler(user_id, block.input or {})
                except Exception as exc:
                    tool_output = {"error": str(exc)}
            tool_results.append({
                "type": "tool_result", "tool_use_id": block.id, "content": json.dumps(tool_output),
            })
        messages.append({"role": "user", "content": tool_results})

    return AgentResponse(text="I wasn't able to finish processing that request. Could you rephrase it?", mode="llm")
