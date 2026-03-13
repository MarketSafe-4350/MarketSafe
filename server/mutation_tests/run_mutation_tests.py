import subprocess
import os
from pathlib import Path

# Ensure working directory = server/
os.chdir(Path(__file__).resolve().parents[1])

modules = [
    "src/auth",
    # "src/utils",
    # "src/business_logic"
]

# Create reports directory
reports_dir = Path("mutation_tests/reports")
reports_dir.mkdir(parents=True, exist_ok=True)

for module in modules:
    name = module.split("/")[-1]
    session = f"{name}.sqlite"

    txt_report = reports_dir / f"{name}_mutation_report.txt"
    html_report = reports_dir / f"{name}_mutation_report.html"

    print(f"\nRunning mutation tests for {module}")

    # Initialize mutation session
    subprocess.run([
        "cosmic-ray", "init",
        "cosmic-ray.toml",
        session
    ], check=True)

    # Execute mutation tests
    subprocess.run([
        "cosmic-ray", "exec",
        "cosmic-ray.toml",
        session
    ], check=True)

    # Save TXT report
    with open(txt_report, "w") as f:
        subprocess.run([
            "cosmic-ray", "dump",
            session
        ], stdout=f, check=True)

    # Save HTML report
    with open(html_report, "w") as f:
        subprocess.run([
            "cr-html",
            session
        ], stdout=f, check=True)

    print(f"TXT report saved to: {txt_report}")
    print(f"HTML report saved to: {html_report}")


    



# import subprocess
# import os
# from pathlib import Path

# # Ensure working directory = server/
# os.chdir(Path(__file__).resolve().parents[1])

# modules = [
#     "src/auth",
#     # "src/utils",
#     # "src/business_logic"
# ]

# for module in modules:
#     name = module.split("/")[-1]
#     session = f"{name}.sqlite"

#     print(f"\nRunning mutation tests for {module}")

#     subprocess.run([
#         "cosmic-ray", "init",
#         "cosmic-ray.toml",
#         session
#     ], check=True)

#     subprocess.run([
#         "cosmic-ray", "exec",
#         "cosmic-ray.toml",
#         session
#     ], check=True)

#     subprocess.run([
#         "cosmic-ray", "dump",
#         session
#     ])