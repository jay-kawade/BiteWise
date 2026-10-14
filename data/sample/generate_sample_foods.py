"""
generate_sample_foods.py
-------------------------------------------------------------------------------
WHAT THIS SCRIPT DOES (read this before trusting the numbers below)
-------------------------------------------------------------------------------
This script builds the file `data/sample/foods_sample.csv`, which is the food
database used throughout this project in DEMO_MODE.

IMPORTANT - PLEASE READ:
The nutrition values below are APPROXIMATE, commonly-cited figures for common,
everyday foods (the kind of numbers you would find on a generic nutrition
label or in a general nutrition reference). They are written by the project
developers as a DEVELOPMENT / DEMONSTRATION dataset so the application has
something realistic to run against. They are:
    - NOT pulled from a single verified scientific database,
    - NOT laboratory-measured values,
    - NOT suitable for clinical, medical, or research use,
    - intended ONLY to demonstrate how the system works end-to-end.

For a real deployment, replace this file with a licensed/verified dataset,
for example:
    - USDA FoodData Central (public domain, api.nal.usda.gov)
    - Indian Food Composition Tables, IFCT 2017 (National Institute of
      Nutrition, ICMR)
Both provide per-100g macro/micronutrient values with documented provenance.
See data/sample/README.md and data/raw/README.md for exact swap-in
instructions -- the rest of the codebase reads foods through
`src/database/repositories.py`, so replacing the CSV is the only change
needed.

Every row's `source` column is explicitly set to "demo_reference" so that no
part of the application can ever confuse this data with a verified source.
-------------------------------------------------------------------------------
"""

import csv
import os

# Each tuple is:
# (name, category, serving_size_g, calories, protein_g, carbs_g, fat_g,
#  fiber_g, sugar_g, sodium_mg, saturated_fat_g, dietary_type, meal_type,
#  cuisine, allergens, notes_tag)
#
# dietary_type in {vegan, vegetarian, eggetarian, non_vegetarian}
# meal_type in {breakfast, lunch, dinner, snack} -- the food's most COMMON
#   meal context. This is used as the target label for the ML classifier
#   (see src/ml/train.py). Real foods can appear at multiple meals; this is
#   a simplifying, documented assumption (see ASSUMPTIONS.md).
# allergens is a "|"-separated list drawn from a small controlled vocabulary:
#   milk, egg, gluten, peanut, tree_nut, soy, shellfish, fish

FOODS = [
    # ---- Grains & staples ----
    ("Cooked white rice", "grain", 150, 195, 4.1, 42.9, 0.4, 0.6, 0.1, 2, 0.1, "vegan", "lunch", "indian", "", ""),
    ("Cooked brown rice", "grain", 150, 170, 3.9, 35.6, 1.4, 2.2, 0.3, 5, 0.3, "vegan", "lunch", "indian", "", ""),
    ("Roti (whole wheat)", "grain", 40, 120, 3.6, 24.0, 1.2, 3.0, 0.3, 2, 0.2, "vegan", "lunch", "indian", "gluten", ""),
    ("Plain naan", "grain", 90, 262, 8.7, 45.0, 5.1, 1.8, 3.0, 418, 1.1, "vegetarian", "dinner", "indian", "gluten|milk", ""),
    ("White bread slice", "grain", 30, 79, 2.7, 14.7, 1.0, 0.8, 1.5, 152, 0.2, "vegan", "breakfast", "continental", "gluten", ""),
    ("Whole wheat bread slice", "grain", 30, 74, 3.6, 12.9, 1.0, 1.9, 1.4, 132, 0.2, "vegan", "breakfast", "continental", "gluten", ""),
    ("Cooked oats (porridge)", "grain", 234, 158, 6.0, 27.3, 3.2, 4.0, 0.6, 115, 0.6, "vegan", "breakfast", "continental", "gluten", ""),
    ("Cooked quinoa", "grain", 185, 222, 8.1, 39.4, 5.2, 1.6, 0.6, 13, 0.6, "vegan", "lunch", "continental", "", ""),
    ("Poha (flattened rice)", "grain", 150, 250, 4.0, 45.0, 6.0, 3.0, 1.0, 300, 1.0, "vegan", "breakfast", "indian", "", ""),
    ("Upma (semolina)", "grain", 150, 240, 5.5, 38.0, 8.0, 2.0, 1.5, 350, 1.5, "vegetarian", "breakfast", "indian", "gluten", ""),
    ("Idli (steamed rice cake)", "grain", 100, 130, 4.0, 26.0, 0.6, 1.0, 0.2, 200, 0.1, "vegan", "breakfast", "indian", "", ""),
    ("Dosa (plain)", "grain", 100, 168, 3.9, 28.0, 4.0, 1.0, 0.5, 250, 0.6, "vegan", "breakfast", "indian", "", ""),
    ("Cooked pasta (plain)", "grain", 140, 221, 8.1, 43.2, 1.3, 2.5, 0.8, 1, 0.2, "vegan", "dinner", "continental", "gluten", ""),
    ("Chapati with ghee", "grain", 45, 150, 3.7, 24.0, 4.5, 3.0, 0.3, 2, 2.5, "vegetarian", "lunch", "indian", "gluten|milk", ""),
    ("Cornflakes (plain)", "grain", 30, 113, 2.1, 25.0, 0.4, 0.9, 2.4, 200, 0.1, "vegan", "breakfast", "continental", "gluten", ""),
    ("Muesli", "grain", 60, 227, 6.0, 42.0, 4.0, 5.0, 12.0, 60, 0.7, "vegetarian", "breakfast", "continental", "gluten|tree_nut", ""),

    # ---- Legumes & pulses ----
    ("Cooked yellow dal (toor)", "legume", 200, 190, 12.0, 30.0, 3.0, 3.0, 1.5, 300, 0.5, "vegan", "lunch", "indian", "", ""),
    ("Cooked chana dal", "legume", 200, 210, 13.0, 33.0, 3.5, 4.0, 2.0, 280, 0.5, "vegan", "lunch", "indian", "", ""),
    ("Cooked rajma (kidney beans)", "legume", 200, 225, 14.0, 38.0, 1.0, 8.0, 3.0, 320, 0.2, "vegan", "dinner", "indian", "", ""),
    ("Cooked chole (chickpeas)", "legume", 200, 269, 14.5, 45.0, 4.0, 7.0, 3.0, 350, 0.5, "vegan", "dinner", "indian", "", ""),
    ("Sprouted moong salad", "legume", 100, 105, 7.0, 19.0, 0.4, 4.0, 2.0, 15, 0.1, "vegan", "snack", "indian", "", ""),
    ("Boiled black beans", "legume", 172, 227, 15.2, 40.8, 15.0, 0.6, 1.9, 2, 0.1, "vegan", "lunch", "continental", "", ""),
    ("Boiled lentils (masoor)", "legume", 198, 230, 17.9, 39.9, 15.6, 3.6, 4.0, 4, 0.1, "vegan", "lunch", "indian", "", ""),
    ("Tofu (firm)", "legume", 100, 144, 15.8, 2.8, 8.7, 2.3, 0.6, 12, 1.3, "vegan", "lunch", "continental", "soy", ""),
    ("Soy chunks (cooked)", "legume", 100, 120, 17.0, 8.0, 0.7, 4.5, 4.0, 5, 0.1, "vegan", "lunch", "indian", "soy", ""),

    # ---- Dairy & eggs ----
    ("Paneer (cottage cheese)", "dairy", 100, 265, 18.3, 1.2, 20.8, 0.0, 1.2, 22, 14.0, "vegetarian", "lunch", "indian", "milk", ""),
    ("Low-fat curd (dahi)", "dairy", 100, 60, 3.5, 4.7, 3.0, 0.0, 4.7, 47, 1.8, "vegetarian", "lunch", "indian", "milk", ""),
    ("Greek yogurt (plain)", "dairy", 100, 59, 10.0, 3.6, 0.4, 0.0, 3.6, 36, 0.1, "vegetarian", "breakfast", "continental", "milk", ""),
    ("Full-cream milk", "dairy", 100, 61, 3.2, 4.8, 3.3, 0.0, 4.8, 40, 2.0, "vegetarian", "breakfast", "continental", "milk", ""),
    ("Skimmed milk", "dairy", 100, 34, 3.4, 5.0, 0.1, 0.0, 5.1, 42, 0.1, "vegetarian", "breakfast", "continental", "milk", ""),
    ("Cheddar cheese", "dairy", 30, 120, 7.4, 0.4, 9.9, 0.0, 0.1, 190, 6.0, "vegetarian", "snack", "continental", "milk", ""),
    ("Boiled egg", "egg", 50, 78, 6.3, 0.6, 5.3, 0.0, 0.6, 62, 1.6, "eggetarian", "breakfast", "continental", "egg", ""),
    ("Scrambled eggs (2 eggs, butter)", "egg", 120, 199, 13.6, 1.8, 15.0, 0.0, 1.0, 342, 6.8, "eggetarian", "breakfast", "continental", "egg|milk", ""),
    ("Egg omelette with vegetables", "egg", 150, 210, 14.0, 4.0, 15.0, 1.0, 2.0, 320, 4.0, "eggetarian", "breakfast", "indian", "egg", ""),
    ("Buttermilk (chaas)", "dairy", 200, 40, 2.0, 4.0, 1.0, 0.0, 4.0, 105, 0.6, "vegetarian", "snack", "indian", "milk", ""),

    # ---- Poultry, meat, fish ----
    ("Grilled chicken breast", "meat", 100, 165, 31.0, 0.0, 3.6, 0.0, 0.0, 74, 1.0, "non_vegetarian", "dinner", "continental", "", ""),
    ("Chicken curry (home-style)", "meat", 200, 280, 24.0, 6.0, 18.0, 1.0, 2.0, 450, 4.5, "non_vegetarian", "dinner", "indian", "", ""),
    ("Tandoori chicken", "meat", 150, 240, 32.0, 4.0, 10.0, 0.5, 2.0, 480, 2.5, "non_vegetarian", "dinner", "indian", "milk", ""),
    ("Boiled/grilled fish (rohu)", "fish", 100, 97, 16.6, 0.0, 3.0, 0.0, 0.0, 60, 0.7, "non_vegetarian", "dinner", "indian", "fish", ""),
    ("Grilled salmon", "fish", 100, 208, 20.4, 0.0, 13.4, 0.0, 0.0, 59, 3.1, "non_vegetarian", "dinner", "continental", "fish", ""),
    ("Mutton curry", "meat", 200, 350, 26.0, 8.0, 24.0, 1.0, 2.0, 500, 8.0, "non_vegetarian", "dinner", "indian", "", ""),
    ("Egg curry", "egg", 200, 260, 14.0, 10.0, 18.0, 2.0, 4.0, 420, 5.0, "eggetarian", "dinner", "indian", "egg|milk", ""),
    ("Prawns (cooked, stir-fried)", "shellfish", 100, 99, 24.0, 0.2, 0.3, 0.0, 0.0, 111, 0.1, "non_vegetarian", "dinner", "continental", "shellfish", ""),

    # ---- Vegetables ----
    ("Mixed vegetable curry", "vegetable", 200, 150, 4.0, 18.0, 7.0, 5.0, 6.0, 300, 1.0, "vegan", "lunch", "indian", "", ""),
    ("Palak (spinach) sabzi", "vegetable", 150, 110, 4.0, 8.0, 7.0, 4.0, 2.0, 250, 1.0, "vegan", "lunch", "indian", "", ""),
    ("Bhindi (okra) sabzi", "vegetable", 150, 120, 3.0, 12.0, 7.0, 5.0, 3.0, 200, 1.0, "vegan", "lunch", "indian", "", ""),
    ("Steamed broccoli", "vegetable", 100, 35, 2.4, 7.2, 0.4, 3.3, 1.6, 33, 0.1, "vegan", "dinner", "continental", "", ""),
    ("Boiled potato", "vegetable", 150, 130, 2.7, 30.0, 0.2, 2.7, 1.4, 6, 0.1, "vegan", "lunch", "indian", "", ""),
    ("Salad (cucumber, tomato, onion)", "vegetable", 150, 45, 1.8, 9.0, 0.3, 2.0, 4.0, 15, 0.0, "vegan", "lunch", "indian", "", ""),
    ("Sauteed mushrooms", "vegetable", 100, 60, 3.0, 4.0, 3.5, 1.0, 2.0, 200, 0.5, "vegan", "dinner", "continental", "", ""),
    ("Mixed salad with olive oil", "vegetable", 150, 120, 2.0, 8.0, 9.0, 3.0, 3.0, 90, 1.3, "vegan", "lunch", "continental", "", ""),

    # ---- Fruits ----
    ("Banana", "fruit", 118, 105, 1.3, 27.0, 0.4, 3.1, 14.4, 1, 0.1, "vegan", "snack", "other", "", ""),
    ("Apple", "fruit", 182, 95, 0.5, 25.0, 0.3, 4.4, 19.0, 2, 0.1, "vegan", "snack", "other", "", ""),
    ("Orange", "fruit", 131, 62, 1.2, 15.4, 0.2, 3.1, 12.2, 0, 0.0, "vegan", "snack", "other", "", ""),
    ("Papaya", "fruit", 145, 59, 0.9, 15.0, 0.2, 2.7, 11.0, 5, 0.1, "vegan", "snack", "other", "", ""),
    ("Watermelon", "fruit", 152, 46, 0.9, 11.5, 0.2, 0.6, 9.4, 2, 0.0, "vegan", "snack", "other", "", ""),
    ("Mixed fruit bowl", "fruit", 200, 110, 1.5, 27.0, 0.4, 4.0, 20.0, 5, 0.1, "vegan", "snack", "other", "", ""),
    ("Mango", "fruit", 165, 99, 1.4, 24.7, 0.6, 2.6, 22.5, 2, 0.1, "vegan", "snack", "other", "", ""),
    ("Grapes", "fruit", 92, 62, 0.6, 16.0, 0.3, 0.8, 15.5, 2, 0.1, "vegan", "snack", "other", "", ""),
    ("Pomegranate seeds", "fruit", 100, 83, 1.7, 18.7, 1.2, 4.0, 13.7, 3, 0.1, "vegan", "snack", "other", "", ""),

    # ---- Nuts & seeds ----
    ("Mixed nuts (unsalted)", "nuts", 30, 180, 5.5, 6.0, 16.0, 2.5, 1.5, 2, 2.0, "vegan", "snack", "other", "tree_nut", ""),
    ("Roasted peanuts", "nuts", 30, 170, 7.7, 6.1, 14.5, 2.4, 1.0, 5, 2.0, "vegan", "snack", "other", "peanut", ""),
    ("Almonds", "nuts", 28, 164, 6.0, 6.1, 14.2, 3.5, 1.2, 0, 1.1, "vegan", "snack", "other", "tree_nut", ""),
    ("Peanut butter (2 tbsp)", "nuts", 32, 188, 8.0, 6.9, 16.0, 1.9, 3.0, 147, 3.3, "vegan", "breakfast", "continental", "peanut", ""),
    ("Chia seeds (2 tbsp)", "nuts", 24, 116, 4.0, 10.0, 7.3, 8.3, 0.0, 4, 0.8, "vegan", "snack", "continental", "", ""),

    # ---- Snacks (mixed nutrition quality, useful for classifier variety) ----
    ("Samosa (fried)", "snack", 100, 262, 4.0, 30.0, 14.0, 2.5, 2.0, 400, 4.0, "vegetarian", "snack", "indian", "gluten", ""),
    ("Vegetable pakora (fried)", "snack", 100, 280, 5.0, 25.0, 18.0, 3.0, 2.0, 380, 3.5, "vegan", "snack", "indian", "gluten", ""),
    ("Roasted chana (snack)", "snack", 50, 180, 10.0, 27.0, 3.0, 8.0, 2.0, 100, 0.4, "vegan", "snack", "indian", "", ""),
    ("Potato chips", "snack", 30, 160, 2.0, 15.0, 10.0, 1.3, 0.2, 170, 3.1, "vegan", "snack", "other", "", ""),
    ("Chocolate chip cookies (2)", "snack", 32, 160, 1.8, 21.0, 8.0, 0.8, 11.0, 100, 3.5, "vegetarian", "snack", "continental", "gluten|milk|egg", ""),
    ("Granola bar", "snack", 40, 180, 4.0, 25.0, 7.0, 2.5, 10.0, 90, 3.0, "vegetarian", "snack", "continental", "gluten|tree_nut", ""),
    ("Protein bar (generic)", "snack", 50, 200, 20.0, 20.0, 7.0, 3.0, 5.0, 200, 3.5, "vegetarian", "snack", "continental", "milk|soy", ""),
    ("Popcorn (plain, air-popped)", "snack", 30, 110, 3.6, 22.0, 1.3, 4.1, 0.1, 2, 0.2, "vegan", "snack", "continental", "", ""),
    ("Dark chocolate (70%)", "snack", 30, 170, 2.2, 13.0, 12.0, 3.1, 6.8, 3, 7.0, "vegan", "snack", "other", "", ""),
    ("Milk chocolate bar", "snack", 40, 210, 3.0, 24.0, 12.0, 1.0, 22.0, 35, 7.5, "vegetarian", "snack", "other", "milk", ""),
    ("Namkeen mixture", "snack", 50, 250, 6.0, 25.0, 15.0, 2.0, 1.0, 450, 3.0, "vegan", "snack", "indian", "peanut|gluten", ""),
    ("Instant noodles (cooked)", "snack", 200, 380, 8.0, 52.0, 15.0, 2.0, 3.0, 900, 7.0, "vegetarian", "dinner", "other", "gluten", ""),

    # ---- Beverages ----
    ("Black coffee (no sugar)", "beverage", 240, 2, 0.3, 0.0, 0.0, 0.0, 0.0, 5, 0.0, "vegan", "breakfast", "other", "", ""),
    ("Masala chai (with milk & sugar)", "beverage", 150, 90, 2.0, 12.0, 3.5, 0.0, 10.0, 30, 2.0, "vegetarian", "breakfast", "indian", "milk", ""),
    ("Fresh orange juice", "beverage", 240, 110, 1.7, 26.0, 0.5, 0.5, 21.0, 2, 0.1, "vegan", "breakfast", "other", "", ""),
    ("Cola soft drink", "beverage", 330, 139, 0.0, 35.0, 0.0, 0.0, 35.0, 15, 0.0, "vegan", "snack", "other", "", ""),
    ("Protein shake (whey, water)", "beverage", 300, 130, 25.0, 4.0, 2.0, 0.5, 2.0, 120, 1.0, "vegetarian", "snack", "continental", "milk", ""),
    ("Coconut water", "beverage", 240, 46, 1.7, 8.9, 0.5, 2.6, 6.3, 252, 0.4, "vegan", "snack", "other", "", ""),
    ("Lassi (sweet)", "beverage", 250, 180, 5.0, 28.0, 5.0, 0.0, 26.0, 65, 3.0, "vegetarian", "snack", "indian", "milk", ""),

    # ---- Composite / restaurant-style meals ----
    ("Vegetable biryani", "composite", 250, 380, 8.0, 60.0, 12.0, 4.0, 4.0, 600, 2.5, "vegetarian", "lunch", "indian", "milk", ""),
    ("Chicken biryani", "composite", 300, 490, 22.0, 60.0, 18.0, 3.0, 4.0, 750, 5.0, "non_vegetarian", "lunch", "indian", "milk", ""),
    ("Paneer butter masala", "composite", 200, 430, 14.0, 16.0, 34.0, 2.0, 8.0, 700, 18.0, "vegetarian", "dinner", "indian", "milk", ""),
    ("Dal makhani", "composite", 200, 330, 12.0, 28.0, 19.0, 6.0, 4.0, 620, 9.0, "vegetarian", "dinner", "indian", "milk", ""),
    ("Vegetable sandwich (grilled)", "composite", 150, 260, 7.0, 34.0, 10.0, 4.0, 5.0, 420, 3.0, "vegetarian", "breakfast", "continental", "gluten|milk", ""),
    ("Chicken sandwich (grilled)", "composite", 200, 340, 24.0, 32.0, 12.0, 3.0, 5.0, 560, 3.5, "non_vegetarian", "lunch", "continental", "gluten", ""),
    ("Margherita pizza (2 slices)", "composite", 200, 500, 20.0, 60.0, 20.0, 3.0, 6.0, 900, 9.0, "vegetarian", "dinner", "continental", "gluten|milk", ""),
    ("Vegetable burger", "composite", 220, 420, 10.0, 55.0, 17.0, 5.0, 8.0, 700, 4.0, "vegetarian", "dinner", "continental", "gluten", ""),
    ("Chicken burger", "composite", 220, 480, 22.0, 45.0, 22.0, 3.0, 7.0, 850, 6.0, "non_vegetarian", "dinner", "continental", "gluten|egg", ""),
    ("Masala dosa", "composite", 180, 320, 6.0, 48.0, 12.0, 3.0, 2.0, 480, 2.5, "vegan", "breakfast", "indian", "", ""),
    ("Rajma chawal (rice + kidney beans)", "composite", 350, 420, 16.0, 70.0, 6.0, 10.0, 4.0, 520, 1.0, "vegan", "lunch", "indian", "", ""),
    ("Chole bhature", "composite", 300, 620, 15.0, 75.0, 28.0, 8.0, 6.0, 850, 8.0, "vegetarian", "lunch", "indian", "gluten", ""),
    ("Vegetable fried rice", "composite", 250, 380, 8.0, 58.0, 12.0, 3.0, 4.0, 700, 2.0, "vegan", "dinner", "other", "soy", ""),
    ("Chicken fried rice", "composite", 300, 460, 20.0, 55.0, 16.0, 2.5, 4.0, 850, 3.5, "non_vegetarian", "dinner", "other", "soy|egg", ""),
    ("Sprouts salad with lemon", "composite", 150, 140, 9.0, 22.0, 1.5, 6.0, 4.0, 120, 0.2, "vegan", "snack", "indian", "", ""),
    ("Vegetable soup (clear)", "composite", 250, 90, 3.0, 14.0, 2.0, 3.0, 4.0, 480, 0.5, "vegan", "dinner", "continental", "", ""),
    ("Sweet corn chaat", "composite", 150, 160, 4.0, 30.0, 3.0, 4.0, 6.0, 220, 0.5, "vegan", "snack", "indian", "", ""),
    ("Gulab jamun (2 pieces)", "dessert", 80, 300, 4.0, 40.0, 14.0, 0.5, 34.0, 60, 6.0, "vegetarian", "snack", "indian", "milk|gluten", ""),
    ("Rasgulla (2 pieces)", "dessert", 80, 186, 4.0, 34.0, 3.5, 0.0, 30.0, 40, 1.8, "vegetarian", "snack", "indian", "milk", ""),
    ("Ice cream (vanilla, 1 scoop)", "dessert", 66, 137, 2.3, 16.0, 7.3, 0.5, 14.0, 53, 4.5, "vegetarian", "snack", "continental", "milk|egg", ""),
    ("Fruit custard", "dessert", 150, 180, 5.0, 28.0, 5.0, 1.5, 20.0, 70, 3.0, "vegetarian", "snack", "indian", "milk|egg", ""),
]

COLUMNS = [
    "name", "category", "serving_size_g", "calories", "protein_g", "carbohydrates_g",
    "fat_g", "fiber_g", "sugar_g", "sodium_mg", "saturated_fat_g", "dietary_type",
    "meal_type", "cuisine", "allergens", "tags", "source",
]


def compute_tags(calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg,
                  saturated_fat_g, serving_size_g):
    """
    Deterministically derive descriptive tags from the nutrition profile using
    simple, documented thresholds (per 100 g, so foods with different serving
    sizes are compared fairly). These thresholds are general reference points
    used for descriptive tagging ONLY -- they are not diagnostic categories
    and are not equivalent to any specific dietary guideline's cutoffs.
    """
    scale = 100.0 / serving_size_g
    protein_100g = protein_g * scale
    sugar_100g = sugar_g * scale
    sodium_100g = sodium_mg * scale
    fiber_100g = fiber_g * scale
    sat_fat_100g = saturated_fat_g * scale

    tags = []
    if protein_100g >= 10:
        tags.append("high_protein")
    if fiber_100g >= 4:
        tags.append("high_fiber")
    if sugar_100g >= 15:
        tags.append("high_sugar")
    if sodium_100g >= 400:
        tags.append("high_sodium")
    if sat_fat_100g >= 5:
        tags.append("high_saturated_fat")
    if not tags:
        tags.append("balanced")
    return "|".join(tags)


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "foods_sample.csv")

    rows = []
    for idx, food in enumerate(FOODS, start=1):
        (name, category, serving_size_g, calories, protein_g, carbs_g, fat_g,
         fiber_g, sugar_g, sodium_mg, saturated_fat_g, dietary_type, meal_type,
         cuisine, allergens, _unused_tags) = food

        tags = compute_tags(calories, protein_g, carbs_g, fat_g, fiber_g,
                             sugar_g, sodium_mg, saturated_fat_g, serving_size_g)

        rows.append([
            name, category, serving_size_g, calories, protein_g, carbs_g, fat_g,
            fiber_g, sugar_g, sodium_mg, saturated_fat_g, dietary_type, meal_type,
            cuisine, allergens, tags, "demo_reference",
        ])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} food records to {out_path}")


if __name__ == "__main__":
    main()
