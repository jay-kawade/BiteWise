"""
formulas.py
-------------------------------------------------------------------------------
ALL nutrition equations used anywhere in this application live in this one
file, on purpose (Section 4 of the project spec: "make all formulas
configurable in one module"). If a professor asks "which formula did you
use and why", this file has the answer for every number the app produces.

Every function below documents:
    - the name of the formula/guideline used
    - the variables and their units
    - the assumptions made
    - a reference so the formula is NOT invented

IMPORTANT: These are widely used ESTIMATION formulas for generally healthy
adults. They do not replace an individualized assessment by a registered
dietitian or physician. See ASSUMPTIONS.md for a summary of every design
choice made where the literature allows a range rather than one fixed
number (e.g. exact protein g/kg, exact fat % of calories).
-------------------------------------------------------------------------------
"""

from typing import Literal

Sex = Literal["male", "female", "other"]
ActivityLevel = Literal["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]
Goal = Literal["weight_loss", "maintenance", "weight_gain", "muscle_gain"]


# ==============================================================================
# 1. BODY MASS INDEX (BMI)
# ==============================================================================
# Formula: BMI = weight_kg / (height_m ** 2)
# Reference: World Health Organization (WHO), standard BMI formula.
# Categories: WHO adult BMI classification (WHO, 1995/2000/2004 reports).
#   Underweight : BMI < 18.5
#   Normal      : 18.5 <= BMI < 25
#   Overweight  : 25 <= BMI < 30
#   Obese       : BMI >= 30
# LIMITATION (documented, not hidden): BMI does not account for muscle mass,
# body composition, age, or ethnicity, and the WHO Expert Consultation (2004)
# has noted that some Asian populations may face health risks at lower BMI
# cutoffs. BMI is shown here only as a common, widely recognized screening
# indicator -- never as a diagnosis.
# ==============================================================================

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    if height_m <= 0:
        raise ValueError("height_cm must be a positive number")
    return round(weight_kg / (height_m ** 2), 1)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obese"


# ==============================================================================
# 2. BASAL METABOLIC RATE (BMR) -- Mifflin-St Jeor Equation
# ==============================================================================
# Reference: Mifflin MD, St Jeor ST, Hill LA, Scott BJ, Daugherty SA, Koh YO.
# "A new predictive equation for resting energy expenditure in healthy
# individuals." American Journal of Clinical Nutrition. 1990;51(2):241-247.
#
# This equation is recommended over the older Harris-Benedict (1919/1984)
# equation by the Academy of Nutrition and Dietetics for its improved
# accuracy in modern populations.
#
#   Men:   BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
#   Women: BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
#
# ASSUMPTION: the original study population was recorded using a binary
# male/female sex variable. For a user who selects "other", this app uses
# the mathematical average of the male and female results as a documented,
# neutral approximation -- see ASSUMPTIONS.md.
# ==============================================================================

def calculate_bmr(weight_kg: float, height_cm: float, age_years: int, sex: Sex) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    if sex == "male":
        bmr = base + 5
    elif sex == "female":
        bmr = base - 161
    else:  # "other" -- see ASSUMPTION above
        bmr = base + (5 + (-161)) / 2.0
    return round(bmr, 1)


# ==============================================================================
# 3. TOTAL DAILY ENERGY EXPENDITURE (TDEE) -- Activity multipliers
# ==============================================================================
# Formula: TDEE = BMR * activity_factor
# Reference: Activity multiplier values are the commonly used set popularized
# through the Harris-Benedict / dietetics literature and widely reproduced in
# nutrition practice guides (e.g. as used in Dietary Reference Intake
# educational materials). These are general categories, not laboratory-
# measured values for a specific individual.
# ==============================================================================

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,           # little or no exercise, desk job
    "lightly_active": 1.375,    # light exercise 1-3 days/week
    "moderately_active": 1.55,  # moderate exercise 3-5 days/week
    "very_active": 1.725,       # hard exercise 6-7 days/week
    "extremely_active": 1.9,    # very hard daily exercise or physical job
}


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level)
    if multiplier is None:
        raise ValueError(
            f"Unknown activity_level '{activity_level}'. Expected one of: "
            f"{list(ACTIVITY_MULTIPLIERS.keys())}"
        )
    return round(bmr * multiplier, 1)


# ==============================================================================
# 4. GOAL-ADJUSTED CALORIE TARGET
# ==============================================================================
# Reference for the ~500 kcal/day adjustment: a long-standing, widely cited
# approximation that a sustained deficit/surplus of roughly 500 kcal/day
# corresponds to about 0.45 kg (1 lb) of body weight change per week, based
# on the approximate energy value of body fat tissue (~7700 kcal/kg).
# LIMITATION (documented): this "3500 kcal per pound" style rule is a
# simplification; real-world weight change is not perfectly linear and
# varies between individuals. It is used here only to produce a reasonable
# STARTING estimate, clearly labelled as such in the UI.
# ==============================================================================

CALORIE_ADJUSTMENT_BY_GOAL = {
    "weight_loss": -500,
    "maintenance": 0,
    "weight_gain": 500,
    "muscle_gain": 300,   # smaller surplus, commonly suggested to favor lean mass over fat gain
}


def calculate_calorie_target(tdee: float, goal: Goal) -> float:
    adjustment = CALORIE_ADJUSTMENT_BY_GOAL.get(goal)
    if adjustment is None:
        raise ValueError(f"Unknown goal '{goal}'. Expected one of: {list(CALORIE_ADJUSTMENT_BY_GOAL.keys())}")
    target = tdee + adjustment
    # Never recommend an unsafely low calorie target; 1200 kcal/day is a
    # commonly cited general floor for adults in mainstream dietary
    # guidance below which professional supervision is advised.
    return round(max(target, 1200), 1)


# ==============================================================================
# 5. PROTEIN TARGET (grams per day)
# ==============================================================================
# Reference: protein needs scale with body weight. The Recommended Dietary
# Allowance (RDA) baseline for a sedentary adult is 0.8 g/kg/day (Institute
# of Medicine, "Dietary Reference Intakes for Energy, Carbohydrate, Fiber,
# Fat, Protein and Amino Acids", 2005). For active individuals pursuing
# fitness/body-composition goals, the International Society of Sports
# Nutrition Position Stand on protein (Jäger et al., Journal of the
# International Society of Sports Nutrition, 2017) supports a broader range
# of roughly 1.4-2.0 g/kg/day.
#
# ASSUMPTION (documented, within the cited ranges above -- not invented):
#   maintenance   -> 1.2 g/kg
#   weight_loss   -> 1.6 g/kg  (higher protein helps preserve lean mass in a deficit)
#   weight_gain   -> 1.4 g/kg
#   muscle_gain   -> 1.8 g/kg
# ==============================================================================

PROTEIN_G_PER_KG_BY_GOAL = {
    "maintenance": 1.2,
    "weight_loss": 1.6,
    "weight_gain": 1.4,
    "muscle_gain": 1.8,
}


def calculate_protein_target(weight_kg: float, goal: Goal) -> float:
    g_per_kg = PROTEIN_G_PER_KG_BY_GOAL.get(goal)
    if g_per_kg is None:
        raise ValueError(f"Unknown goal '{goal}'. Expected one of: {list(PROTEIN_G_PER_KG_BY_GOAL.keys())}")
    return round(weight_kg * g_per_kg, 1)


# ==============================================================================
# 6. FAT TARGET (grams per day)
# ==============================================================================
# Reference: Acceptable Macronutrient Distribution Range (AMDR) for fat is
# 20-35% of total daily calories (Institute of Medicine, 2005; reflected in
# the U.S. Dietary Guidelines for Americans).
# ASSUMPTION: this app uses 27% of total calorie target (the midpoint of the
# AMDR range) as a single, reasonable default. 1 gram of fat = 9 kcal.
# ==============================================================================

FAT_PERCENT_OF_CALORIES = 0.27


def calculate_fat_target(calorie_target: float) -> float:
    fat_kcal = calorie_target * FAT_PERCENT_OF_CALORIES
    return round(fat_kcal / 9.0, 1)


# ==============================================================================
# 7. CARBOHYDRATE TARGET (grams per day)
# ==============================================================================
# Formula: remaining calories after protein and fat are allocated to
# carbohydrates. 1 gram of carbohydrate = 4 kcal.
# This keeps the three macronutrient targets internally consistent so their
# calories always sum to the calorie target (Section 4 requirement: targets
# must be coherent, not independently invented numbers).
# ==============================================================================

def calculate_carb_target(calorie_target: float, protein_target_g: float, fat_target_g: float) -> float:
    protein_kcal = protein_target_g * 4.0
    fat_kcal = fat_target_g * 9.0
    remaining_kcal = max(calorie_target - protein_kcal - fat_kcal, 0.0)
    return round(remaining_kcal / 4.0, 1)


# ==============================================================================
# 8. FIBER TARGET (grams per day)
# ==============================================================================
# Reference: a commonly cited Adequate Intake (AI) guideline is ~14 grams of
# fiber per 1000 kcal consumed (Institute of Medicine, 2005; reflected in the
# U.S. Dietary Guidelines for Americans).
# ==============================================================================

FIBER_G_PER_1000_KCAL = 14.0


def calculate_fiber_target(calorie_target: float) -> float:
    return round((calorie_target / 1000.0) * FIBER_G_PER_1000_KCAL, 1)
