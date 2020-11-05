import os


def main():
    file_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")

    with open(file=file_path, mode="r") as f:
        lines = [line.split("==")[0] for line in f.read().split("\n")]

    with open(file=file_path, mode="w") as f:
        for line in lines:
            f.write(f"{line}\n")


if __name__ == "__main__":
    main()
