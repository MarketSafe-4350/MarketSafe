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

for module in modules:
    name = module.split("/")[-1]
    session = f"{name}.sqlite"

    print(f"\nRunning mutation tests for {module}")

    subprocess.run([
        "cosmic-ray", "init",
        "cosmic-ray.toml",
        session
    ], check=True)

    subprocess.run([
        "cosmic-ray", "exec",
        "cosmic-ray.toml",
        session
    ], check=True)

    subprocess.run([
        "cosmic-ray", "report",
        session
    ])