"""Benchmark sensitivitas solver CSP untuk kebutuhan laporan Milestone 2.

Contoh:
    uv run python -m src.csp.benchmark
    uv run python -m src.csp.benchmark --weeks 1 2 4 --csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass

from .instances import build_instance
from .solver import solve


@dataclass(frozen=True)
class BenchmarkRow:
    weeks: int
    doctors: int
    nurses: int
    variables: int
    configuration: str
    status: str
    nodes: int
    backtracks: int
    ac3_pruned: int
    time_ms: float

    def as_dict(self) -> dict[str, object]:
        return {
            "weeks": self.weeks,
            "doctors": self.doctors,
            "nurses": self.nurses,
            "variables": self.variables,
            "configuration": self.configuration,
            "status": self.status,
            "nodes": self.nodes,
            "backtracks": self.backtracks,
            "ac3_pruned": self.ac3_pruned,
            "time_ms": f"{self.time_ms:.3f}",
        }


CONFIGURATIONS = {
    "all_heuristics": {},
    "without_ac3": {"use_ac3": False},
    "without_mrv": {"use_mrv": False},
    "without_forward_checking": {"use_fc": False},
}


def _staff_for_weeks(weeks: int) -> tuple[int, int]:
    """Scale staff while keeping the generated instances feasible."""
    return 3 + weeks, 6 + 2 * weeks


def run_benchmark(weeks_values: list[int], max_nodes: int = 200_000) -> list[BenchmarkRow]:
    """Run deterministic sensitivity scenarios and return structured results."""
    if not weeks_values or any(weeks <= 0 for weeks in weeks_values):
        raise ValueError("weeks harus berisi bilangan positif")

    rows: list[BenchmarkRow] = []
    for weeks in weeks_values:
        doctors, nurses = _staff_for_weeks(weeks)
        for name, options in CONFIGURATIONS.items():
            model = build_instance(doctors, nurses, weeks)
            result = solve(model, max_nodes=max_nodes, **options)
            stats = result.stats
            rows.append(
                BenchmarkRow(
                    weeks=weeks,
                    doctors=doctors,
                    nurses=nurses,
                    variables=len(model.variables),
                    configuration=name,
                    status=stats.status,
                    nodes=stats.nodes,
                    backtracks=stats.backtracks,
                    ac3_pruned=stats.ac3_pruned,
                    time_ms=stats.time_s * 1000,
                )
            )
    return rows


def _print_table(rows: list[BenchmarkRow]) -> None:
    headers = [
        "weeks",
        "variables",
        "configuration",
        "status",
        "nodes",
        "backtracks",
        "ac3_pruned",
        "time_ms",
    ]
    print("\t".join(headers))
    for row in rows:
        values = row.as_dict()
        print("\t".join(str(values[header]) for header in headers))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark sensitivitas CSP Milestone 2")
    parser.add_argument("--weeks", nargs="+", type=int, default=[1, 2, 4])
    parser.add_argument("--max-nodes", type=int, default=200_000)
    parser.add_argument("--csv", action="store_true", help="cetak CSV ke stdout")
    args = parser.parse_args(argv)

    try:
        rows = run_benchmark(args.weeks, args.max_nodes)
    except ValueError as error:
        parser.error(str(error))
    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].as_dict()))
        writer.writeheader()
        writer.writerows(row.as_dict() for row in rows)
    else:
        _print_table(rows)
    return 0 if all(row.status == "solved" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
