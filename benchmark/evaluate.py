from pathlib import Path
import pandas as pd
from finance_controller import run_controller

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_PATH = PROJECT_ROOT / "benchmark" / "ground_truth.csv"


def main():
    ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
    payment_ids = ground_truth["payment_id"].tolist()
    actual_results = run_controller(payment_ids)
    actual_by_id = {result["payment_id"]: result["status"] for result in actual_results}
    ground_truth["actual_status"] = ground_truth["payment_id"].map(actual_by_id)
    missing = ground_truth["actual_status"].isna()

    if missing.any():
        missing_ids = ground_truth.loc[missing, "payment_id"].tolist()
        raise RuntimeError(
            f"Controller returned no result for payment IDs: {missing_ids}"
        )

    ground_truth["correct"] = (ground_truth["expected_status"] == ground_truth["actual_status"])
    correct = int(ground_truth["correct"].sum())
    total = len(ground_truth)
    incorrect = total - correct
    accuracy = (correct / total * 100) if total else 0.0

    print()
    print("FiRecon — Deterministic Controller Benchmark")
    print("-" * 48)
    print(f"Benchmark cases:      {total}")
    print(f"Correct decisions:    {correct}")
    print(f"Incorrect decisions:  {incorrect}")
    print(f"Decision accuracy:    {accuracy:.1f}%")
    print()

    if incorrect:
        mismatches = ground_truth.loc[~ground_truth["correct"], ["payment_id", "scenario", "expected_status","actual_status", "expected_reason",],]
        print("Mismatched cases:")
        print(mismatches.to_string(index=False))
        print()


if __name__ == "__main__":
    main()