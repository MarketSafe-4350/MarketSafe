import os
import subprocess
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[2])

features = [
    "tests/mutation_tests/configs/account_authentication_cosmic-ray.toml",
    "tests/mutation_tests/configs/listings_cosmic-ray.toml",
    "tests/mutation_tests/configs/search_cosmic-ray.toml",
    "tests/mutation_tests/configs/offer_cosmic-ray.toml",
    "tests/mutation_tests/configs/rating_cosmic-ray.toml",
]


reports_dir = Path("tests/mutation_tests/reports")
reports_dir.mkdir(parents=True, exist_ok=True)

for feature in features:
    feature_path = Path(feature)
    name = feature_path.stem
    session = f"{name}.sqlite"

    txt_report = reports_dir / f"{name}_mutation_report.txt"
    html_report = reports_dir / f"{name}_mutation_report.html"

    print(f"\nRunning mutation tests for {feature}")

    subprocess.run(
        ["cosmic-ray", "init", "--force", feature, session],
        check=True,
    )
    subprocess.run(
        ["cr-filter-pragma", session],
        check=True,
    )

    subprocess.run(
        ["cosmic-ray", "exec", feature, session],
        check=True,
    )

    with open(txt_report, "w", encoding="utf-8") as f:
        subprocess.run(
            ["cr-report", session],
            stdout=f,
            check=True,
        )

    with open(html_report, "w", encoding="utf-8") as f:
        subprocess.run(
            ["cr-html", session],
            stdout=f,
            check=True,
        )

    print(f"TXT report saved to: {txt_report}")
    print(f"HTML report saved to: {html_report}")
