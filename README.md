# penguins-codex

penguins_raw.csv downloaded unmodified from github.com/allisonhorst/palmerpenguins (inst/extdata) on 14 Oct 2026.

Run `python body_mass.py` to create `body_mass.csv` next to the script.
Optional `--input` and `--output` arguments accept alternative paths.
The script uses only the Python standard library.

Cleaning excludes rows with `NA` or empty species, sex, or body mass; it
does not fill values or exclude rows for missing unrelated fields. For this
file, 11 of 344 rows are excluded because sex is missing, including 2 that
also lack body mass, leaving 333 rows. The script reports these counts.
Original species names and sex labels are preserved. Unexpected sex labels
or invalid masses cause an error. Means are in grams, with no explicit rounding.

Install test dependencies with `python -m pip install -r requirements-dev.txt`,
then run `python -m pytest -q`.
