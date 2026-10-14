# Limitations, Ethical Considerations & Future Scope

## Limitations

1. **Demo food dataset is small and approximate** (~105 rows, developer-
   compiled reference values, not a verified scientific source). See
   `data/sample/README.md`.
2. **ML model accuracy is modest and uncertain** given the small dataset —
   reported honestly in `docs/ml_methodology.md` and the in-app evaluation
   tab, not inflated.
3. **OCR accuracy on real, photographed labels is unverified** — no
   labeled test set of real photos was available; mock mode is used when
   Tesseract isn't installed, and even real OCR quality varies with photo
   quality/lighting/angle.
4. **No cross-contamination detection**: allergen checking is text-based
   label matching only, explicitly disclosed via the allergen disclaimer
   shown throughout the app.
5. **Single-device, no authentication**: appropriate for an academic demo,
   not for handling multiple real users' private health data at scale.
6. **Nutrition formulas are population-level estimates**, not
   individualized clinical assessments — explicitly disclosed via the
   health disclaimer shown throughout the app.
7. **Meal-slot calorie allocation for the meal planner is a fixed,
   simple percentage split** (documented in `ASSUMPTIONS.md`), not
   personalized to circadian/metabolic factors.

## Ethical considerations

- The system is designed to **never** diagnose, treat, cure, or medically
  manage a disease (see `src/agent/prompts.py::SAFETY_RULES` and the
  Settings > Safety tab).
- Health-condition notes, if entered, are stored only as free text for the
  user's own reference and are never interpreted or acted upon by any
  part of the system.
- The system avoids universal "healthy"/"unhealthy" food labels, instead
  describing a food's nutrition profile relative to the user's own stated
  goals (Section 10 of the original brief).
- All disclaimers (health, allergen) are shown consistently across every
  page that produces nutrition-related output, not just once at sign-up.
- No user data is sent to any external service unless the user explicitly
  configures an LLM API key; in default DEMO_MODE, everything is entirely
  local.

## Future scope

- Replace the demo food dataset with a licensed, verified dataset (USDA
  FoodData Central or IFCT 2017) for production-grade nutrition accuracy.
- Collect labeled user-preference/acceptance data to allow formal
  precision@k/recall@k evaluation of the recommendation engine.
- Benchmark OCR accuracy against a labeled test set of real photographed
  nutrition labels, and consider a cloud OCR provider as an optional
  higher-accuracy backend (behind the existing OCR abstraction layer).
- Add barcode scanning as a second, faster path to food identification
  (complementary to the label-photo OCR pipeline).
- Extend the ML component with a second, regression-based task once a
  verified, sufficiently large nutrition dataset is available (e.g.
  predicting a nutrient value from partial label data).
- Add row-level personalization/adaptation using more logged history once
  enough real usage data exists (Section 16 of the original brief).
