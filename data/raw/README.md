# data/raw/

This folder is where you place an **unmodified, original** dataset file if
you replace the bundled demo dataset with a real, verified one (e.g. a USDA
FoodData Central export or IFCT 2017 tables).

Nothing in this project ships a real dataset here by default -- the
application runs in DEMO_MODE using `data/sample/foods_sample.csv` instead.
This keeps the project runnable out-of-the-box without any external
downloads, accounts, or licenses, while making it obvious where a real
dataset would go and how to wire it in (see `data/sample/README.md`,
section "How to replace this with a real, verified dataset").

Preprocessing scripts should always read from this folder and write cleaned
output to `data/processed/`, never modify files here in place.
