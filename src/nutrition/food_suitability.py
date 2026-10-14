"""
food_suitability.py
-------------------------------------------------------------------------------
Implements Section 10: Personalized Food Suitability Analysis.

This is DELIBERATELY NOT a binary "healthy" / "unhealthy" classifier.
Instead it produces a short checklist of factual, explainable observations
(fits diet type? uses how much of the remaining calorie budget? high in
sugar/sodium? contributes useful protein?) plus a cautious, qualified
overall suitability phrase. All of the underlying numbers come from the
deterministic nutrition calculator and the food's own nutrition values --
this module contains NO machine learning.
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SuitabilityChecklistItem:
    symbol: str   # a Material Symbols shortcode, e.g. ":material/check_circle:"
    text: str


@dataclass
class FoodSuitabilityResult:
    calories: float
    protein_g: float
    carbohydrates_g: float
    fat_g: float
    sugar_g: float
    sodium_mg: float
    checklist: List[SuitabilityChecklistItem] = field(default_factory=list)
    suitability_label: str = ""


def analyze_food_suitability(
    nutrition: dict,
    diet_type: str,
    food_dietary_type: Optional[str],
    food_allergen_warnings: List[str],
    remaining_calorie_budget: Optional[float],
    remaining_protein_budget: Optional[float],
) -> FoodSuitabilityResult:
    """
    nutrition dict keys expected: calories, protein_g, carbohydrates_g,
    fat_g, sugar_g, sodium_mg (fiber_g/saturated_fat_g optional).
    """
    calories = nutrition.get("calories", 0.0)
    protein_g = nutrition.get("protein_g", 0.0)
    carbs_g = nutrition.get("carbohydrates_g", 0.0)
    fat_g = nutrition.get("fat_g", 0.0)
    sugar_g = nutrition.get("sugar_g", 0.0)
    sodium_mg = nutrition.get("sodium_mg", 0.0)

    checklist: List[SuitabilityChecklistItem] = []
    concerns = 0
    positives = 0

    # 1. Dietary preference compatibility.
    diet_hierarchy = ["vegan", "vegetarian", "eggetarian", "non_vegetarian"]
    if food_dietary_type:
        if food_dietary_type in diet_hierarchy and diet_type in diet_hierarchy:
            compatible = diet_hierarchy.index(food_dietary_type) <= diet_hierarchy.index(diet_type)
        else:
            compatible = food_dietary_type == diet_type
        if compatible:
            checklist.append(SuitabilityChecklistItem(":material/check_circle:", f"Fits your {diet_type.replace('_', ' ')} dietary preference"))
            positives += 1
        else:
            checklist.append(SuitabilityChecklistItem(":material/cancel:", f"Does NOT fit your {diet_type.replace('_', ' ')} dietary preference"))
            concerns += 2  # a hard dietary mismatch is weighted more heavily

    # 2. Allergen / restriction warnings (already computed by ingredient_parser or profile check).
    if food_allergen_warnings:
        for warning in food_allergen_warnings:
            checklist.append(SuitabilityChecklistItem(":material/warning:", f"Potential match: {warning}"))
        concerns += 2

    # 3. Protein contribution.
    if protein_g >= 10:
        checklist.append(SuitabilityChecklistItem(":material/check_circle:", f"Provides useful protein ({protein_g:.0f}g)"))
        positives += 1
    elif protein_g > 0:
        checklist.append(SuitabilityChecklistItem(":material/warning:", f"Provides modest protein ({protein_g:.0f}g)"))

    # 4. Calorie budget usage.
    if remaining_calorie_budget and remaining_calorie_budget > 0:
        pct_of_budget = (calories / remaining_calorie_budget) * 100
        if pct_of_budget <= 25:
            checklist.append(SuitabilityChecklistItem(":material/check_circle:", f"Uses a small share of your remaining calorie budget ({pct_of_budget:.0f}%)"))
            positives += 1
        elif pct_of_budget <= 60:
            checklist.append(SuitabilityChecklistItem(":material/warning:", f"Uses a moderate share of today's remaining calorie budget ({pct_of_budget:.0f}%)"))
        else:
            checklist.append(SuitabilityChecklistItem(":material/warning:", f"Uses a large share of today's remaining calorie budget ({pct_of_budget:.0f}%)"))
            concerns += 1

    # 5. Sugar.
    if sugar_g >= 15:
        checklist.append(SuitabilityChecklistItem(":material/warning:", f"Relatively high in sugar ({sugar_g:.0f}g) -- consider your overall daily intake"))
        concerns += 1
    elif sugar_g > 0:
        checklist.append(SuitabilityChecklistItem(":material/check_circle:", f"Moderate sugar content ({sugar_g:.0f}g)"))

    # 6. Sodium.
    if sodium_mg >= 400:
        checklist.append(SuitabilityChecklistItem(":material/warning:", f"Relatively high in sodium ({sodium_mg:.0f}mg)"))
        concerns += 1

    # Overall suitability phrase -- deliberately cautious language, never a
    # medical claim, never a bare "healthy"/"unhealthy" label.
    if concerns == 0 and positives >= 2:
        label = "Potentially suitable for your current goal."
    elif concerns >= 2:
        label = "May not align well with your current goal or preferences -- review the notes above."
    else:
        label = "Can fit your current goal in moderation -- review the notes above."

    return FoodSuitabilityResult(
        calories=calories, protein_g=protein_g, carbohydrates_g=carbs_g, fat_g=fat_g,
        sugar_g=sugar_g, sodium_mg=sodium_mg, checklist=checklist, suitability_label=label,
    )
