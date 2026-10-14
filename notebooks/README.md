# notebooks/

This project intentionally keeps exploratory data analysis as a plain,
version-control-friendly Python script (`eda_script.py`) rather than a
`.ipynb` notebook, so it's easy to read as a diff and run in CI without a
Jupyter kernel. If your team prefers an interactive notebook for the
viva/demo, you can open this script in Jupyter (`jupyter nbconvert
--to notebook --execute eda_script.py`) or simply paste its cells into a
new `.ipynb` file.

Run it with:
```bash
python notebooks/eda_script.py
```

It prints summary statistics and class balance for the food dataset
that `src/ml/train.py` trains on — useful context for explaining the ML
methodology in `docs/ml_methodology.md` during a viva.
