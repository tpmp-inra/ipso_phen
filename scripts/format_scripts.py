# Format all scripts in project with black
import os
import subprocess
from tqdm import tqdm


def main():
    script_list = [
        os.path.join(root, name)
        for root, _, files in os.walk(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "ipso_phen",
            )
        )
        for name in files
        if name.lower().endswith(".py")
    ]
    for script in tqdm(script_list, desc="Formatting scripts"):
        subprocess.run(args=("black", "-q", script))


if __name__ == "__main__":
    main()
