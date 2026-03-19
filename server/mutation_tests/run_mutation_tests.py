import os
import subprocess
from pathlib import Path

# Ensure working directory = server/
os.chdir(Path(__file__).resolve().parents[1])

features = [
    # "account_authentication_cosmic-ray.toml",
    # "listings_cosmic-ray.toml",
    # "search_cosmic-ray.toml",
    "offer_cosmic-ray.toml",
]

# Create reports directory
reports_dir = Path("mutation_tests/reports")
reports_dir.mkdir(parents=True, exist_ok=True)

for feature in features:
    feature_path = Path(feature)
    name = feature_path.stem
    session = f"{name}.sqlite"

    txt_report = reports_dir / f"{name}_mutation_report.txt"
    html_report = reports_dir / f"{name}_mutation_report.html"

    print(f"\nRunning mutation tests for {feature}")

    # Initialize mutation session and overwrite existing session file
    subprocess.run(
        [
            "cosmic-ray",
            "init",
            "--force",
            feature,
            session,
        ],
        check=True,
    )

    # Execute mutation tests
    subprocess.run(
        [
            "cosmic-ray",
            "exec",
            feature,
            session,
        ],
        check=True,
    )

    # Save TXT report
    with open(txt_report, "w", encoding="utf-8") as f:
        subprocess.run(
            [
                "cosmic-ray",
                "dump",
                session,
            ],
            stdout=f,
            check=True,
        )

    # Save HTML report
    with open(html_report, "w", encoding="utf-8") as f:
        subprocess.run(
            [
                "cr-html",
                session,
            ],
            stdout=f,
            check=True,
        )

    print(f"TXT report saved to: {txt_report}")
    print(f"HTML report saved to: {html_report}")

# listing
# "src/db/listing/listing_db.py",
# "src/domain_models/listing.py",

# auth
#         "src/db/account/account_db.py",
        # "src/domain_models/account.py",


# import subprocess
# import os
# from pathlib import Path

# # Ensure working directory = server/
# os.chdir(Path(__file__).resolve().parents[1])

# features = [
#     "account_authentication_cosmic-ray.toml",
#     # "listings_cosmic-ray.toml",
#     # "search_cosmic-ray.toml"
#     # "src/auth",
#     # "src/utils",
#     # "src/business_logic"
# ]

# # Create reports directory
# reports_dir = Path("mutation_tests/reports")
# reports_dir.mkdir(parents=True, exist_ok=True)

# for feature in features:
#     name = feature.split("/")[-1]
#     session = f"{name}.sqlite"

#     txt_report = reports_dir / f"{name}_mutation_report.txt"
#     html_report = reports_dir / f"{name}_mutation_report.html"

#     print(f"\nRunning mutation tests for {feature}")

#     # Initialize mutation session
#     subprocess.run([
#         "cosmic-ray", "init",
#         feature,
#         session
#     ], check=True)

#     # Execute mutation tests
#     subprocess.run([
#         "cosmic-ray", "exec",
#         feature,
#         session
#     ], check=True)

#     # Save TXT report
#     with open(txt_report, "w") as f:
#         subprocess.run([
#             "cosmic-ray", "dump",
#             session
#         ], stdout=f, check=True)

#     # Save HTML report
#     with open(html_report, "w") as f:
#         subprocess.run([
#             "cr-html",
#             session
#         ], stdout=f, check=True)

#     print(f"TXT report saved to: {txt_report}")
#     print(f"HTML report saved to: {html_report}")

