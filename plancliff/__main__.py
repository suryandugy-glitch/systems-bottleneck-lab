"""Run deterministic synthetic data experiments and flag measured query cliffs."""
import argparse
import json
import sqlite3
import statistics
import time


def experiment(size: int, repeats: int, skew: float, indexed: bool = True) -> dict:
    if size < 1 or repeats < 1 or not 0 <= skew <= 1:
        raise ValueError("size/repeats must be positive and skew must be in [0,1]")
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, tenant INTEGER, payload TEXT)")
    con.executemany(
        "INSERT INTO events (tenant, payload) VALUES (?,?)",
        ((0 if i < int(size * skew) else 1 + i % 97, "x" * 24) for i in range(size)),
    )
    if indexed:
        con.execute("CREATE INDEX ix_events_tenant ON events(tenant)")
    con.execute("ANALYZE")
    sql = "SELECT COUNT(*), SUM(LENGTH(payload)) FROM events WHERE tenant = ?"
    plan = [row[3] for row in con.execute("EXPLAIN QUERY PLAN " + sql, (0,))]
    con.execute(sql, (0,)).fetchone()  # warm up
    observations = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        con.execute(sql, (0,)).fetchone()
        observations.append((time.perf_counter_ns() - start) / 1e6)
    con.close()
    return {"rows": size, "skew": skew, "indexed": indexed,
            "p50_ms": round(statistics.median(observations), 5), "plan": plan}


def detect_cliffs(results: list[dict], threshold: float = 3.0) -> list[dict]:
    if threshold <= 1:
        raise ValueError("threshold must exceed 1")
    cliffs = []
    for previous, current in zip(results, results[1:]):
        old = previous["p50_ms"]
        ratio = current["p50_ms"] / old if old > 0 else float("inf")
        if ratio >= threshold or previous["plan"] != current["plan"]:
            cliffs.append({"from_rows": previous["rows"], "to_rows": current["rows"],
                           "latency_ratio": round(ratio, 2),
                           "plan_changed": previous["plan"] != current["plan"]})
    return cliffs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="100,1000,5000")
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--skew", type=float, default=0.8)
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--no-index", action="store_true")
    args = parser.parse_args()
    sizes = sorted(set(int(x) for x in args.sizes.split(",")))
    results = [experiment(n, args.repeats, args.skew, not args.no_index) for n in sizes]
    print(json.dumps({"results": results, "cliffs": detect_cliffs(results, args.threshold)}, indent=2))


if __name__ == "__main__":
    main()
