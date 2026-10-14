import csv
import subprocess
import sys
from pathlib import Path

import pytest

from body_mass import average_body_mass, clean_rows


ROOT = Path(__file__).resolve().parent


def test_cleaning_only_requires_target_columns():
    rows = [
        {"Species": "Adelie", "Sex": "FEMALE", "Body Mass (g)": "3000", "Comments": "NA"},
        {"Species": "Adelie", "Sex": "NA", "Body Mass (g)": "NA"},
        {"Species": "Adelie", "Sex": "MALE", "Body Mass (g)": ""},
        {"Species": "", "Sex": "MALE", "Body Mass (g)": "4000"},
    ]
    cleaned, audit = clean_rows(rows)
    assert cleaned == [{"species": "Adelie", "sex": "FEMALE", "body_mass_g": 3000.0}]
    assert audit == dict(input_rows=4, excluded_rows=3, retained_rows=1,
                         missing_species=1, missing_sex=1, missing_body_mass=2)
    assert rows[1]["Sex"] == "NA"


@pytest.mark.parametrize("sex,mass", [("UNKNOWN", "3000"), ("MALE", "oops"),
                                      ("MALE", "nan"), ("MALE", "-1")])
def test_unexpected_values_raise(sex, mass):
    with pytest.raises(ValueError):
        clean_rows([{"Species": "Adelie", "Sex": sex, "Body Mass (g)": mass}])


def test_average_is_grouped_and_not_rounded():
    result = average_body_mass([
        dict(species="A", sex="FEMALE", body_mass_g=value) for value in (3000, 3000, 3001)
    ] + [dict(species="A", sex="MALE", body_mass_g=4000)])
    assert result == [dict(species="A", sex="FEMALE", mean_body_mass_g=pytest.approx(9001 / 3)),
                      dict(species="A", sex="MALE", mean_body_mass_g=4000)]


def test_raw_data_counts_and_known_means():
    with (ROOT / "penguins_raw.csv").open(newline="") as source:
        cleaned, audit = clean_rows(csv.DictReader(source))
    assert audit == dict(input_rows=344, excluded_rows=11, retained_rows=333,
                         missing_species=0, missing_sex=11, missing_body_mass=2)
    expected = {
        ("Adelie Penguin (Pygoscelis adeliae)", "FEMALE"): 3368.8356164383563,
        ("Adelie Penguin (Pygoscelis adeliae)", "MALE"): 4043.4931506849316,
        ("Chinstrap penguin (Pygoscelis antarctica)", "FEMALE"): 3527.205882352941,
        ("Chinstrap penguin (Pygoscelis antarctica)", "MALE"): 3938.970588235294,
        ("Gentoo penguin (Pygoscelis papua)", "FEMALE"): 4679.741379310345,
        ("Gentoo penguin (Pygoscelis papua)", "MALE"): 5484.836065573771,
    }
    actual = {(r["species"], r["sex"]): r["mean_body_mass_g"]
              for r in average_body_mass(cleaned)}
    assert actual == pytest.approx(expected)


def test_cli_writes_csv_and_reports_exclusions(tmp_path):
    output = tmp_path / "body_mass.csv"
    process = subprocess.run([sys.executable, str(ROOT / "body_mass.py"), "--output", str(output)],
                             cwd=tmp_path, capture_output=True, text=True, check=True)
    assert "excluded: 11; retained: 333" in process.stdout
    assert "No values filled" in process.stdout
    with output.open(newline="") as source:
        reader = csv.DictReader(source)
        assert reader.fieldnames == ["species", "sex", "mean_body_mass_g"]
        rows = list(reader)
    assert len(rows) == 6
    assert float(rows[0]["mean_body_mass_g"]) == pytest.approx(3368.8356164383563)
