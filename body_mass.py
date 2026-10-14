"""Calculate species/sex mean body masses from the raw Palmer Penguins CSV."""

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


REQUIRED = ("Species", "Sex", "Body Mass (g)")
OUTPUT_FIELDS = ("species", "sex", "mean_body_mass_g")


def clean_rows(rows):
    """Exclude missing target values only; return clean records and audit counts.

    NA and empty strings represent missing values. Unexpected nonmissing values
    raise an error rather than being silently discarded or changed.
    """
    cleaned = []
    audit = Counter(input_rows=0, excluded_rows=0, retained_rows=0,
                    missing_species=0, missing_sex=0, missing_body_mass=0)
    for line, row in enumerate(rows, start=2):
        audit["input_rows"] += 1
        missing = [row[column] in ("", "NA") for column in REQUIRED]
        for key, absent in zip(
            ("missing_species", "missing_sex", "missing_body_mass"), missing
        ):
            audit[key] += absent
        if any(missing):
            audit["excluded_rows"] += 1
            continue
        if row["Sex"] not in ("MALE", "FEMALE"):
            raise ValueError(f"CSV line {line}: unexpected sex {row['Sex']!r}")
        mass = float(row["Body Mass (g)"])
        if not math.isfinite(mass) or mass <= 0:
            raise ValueError(f"CSV line {line}: invalid body mass {mass!r}")
        cleaned.append({"species": row["Species"], "sex": row["Sex"],
                        "body_mass_g": mass})
        audit["retained_rows"] += 1
    return cleaned, dict(audit)


def average_body_mass(rows):
    """Return sorted species/sex means in grams, without explicit rounding."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["species"], row["sex"]].append(row["body_mass_g"])
    return [dict(species=species, sex=sex, mean_body_mass_g=mean(groups[species, sex]))
            for species, sex in sorted(groups)]


def run(input_path, output_path):
    with Path(input_path).open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError(f"Input must contain columns: {', '.join(REQUIRED)}")
        cleaned, audit = clean_rows(reader)
    result = average_body_mass(cleaned)
    with Path(output_path).open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(result)
    print(f"Input: {audit['input_rows']} rows; excluded: {audit['excluded_rows']}; "
          f"retained: {audit['retained_rows']}. No values filled.")
    print(f"Missing species: {audit['missing_species']}; sex: {audit['missing_sex']}; "
          f"body mass: {audit['missing_body_mass']} (counts may overlap).")
    print(f"Saved {len(result)} group averages to {output_path}")
    return audit


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root / "penguins_raw.csv")
    parser.add_argument("--output", type=Path, default=root / "body_mass.csv")
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()
