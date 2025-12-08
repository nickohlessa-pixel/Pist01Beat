from pist01beat import Pist01Beat


def main() -> None:
    model = Pist01Beat()
    result = model.predict("HOR", "DEN")

    print("=== Pist01 Beat — Scaffold Check ===")
    print(f"Status: {result.get('status')}")
    print(f"Team A: {result.get('team_a')}")
    print(f"Team B: {result.get('team_b')}")


if __name__ == "__main__":
    main()
