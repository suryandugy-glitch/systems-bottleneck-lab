# Systems Bottleneck Lab

Three reproducible developer-infrastructure experiments, designed for deep systems research and hackathon demos. All tools run with Python 3.11+ and the standard library; no cloud account or API key is needed.

| Tool | Bottleneck | What the prototype actually proves |
|---|---|---|
| **PlanCliff** | SQLite query plans can become slow when cardinality or data skew changes | Sweeps dataset sizes and skew, saves query plans and p50 latency, flags measured regressions |
| **TailForge** | A distributed request is often held back by its slowest dependency | Simulates fan-out, retries and hedged requests with reproducible workloads; compares p50/p95/p99 and work amplification |
| **LockGraph** | Lock acquisition order can create deadlock risk before production | Analyzes lock traces into a directed graph, finds cycles and prints witness paths |

## Quick start

```bash
python -m plancliff --sizes 100,1000,5000 --repeats 20
python -m tailforge --requests 10000 --seed 7
python -m lockgraph examples/locks.json
python -m unittest discover -s tests -v
```

## Research questions

**PlanCliff:** How do indexes, scale and data distributions change the SQLite planner's chosen path? Benchmarks are subject to OS caching and noisy clocks; a flagged cliff is a hypothesis to investigate, not proof of a planner bug.

**TailForge:** At what fan-out and tail distribution do hedged requests improve end-user latency enough to justify extra backend work? The discrete-event model deliberately excludes queuing, congestion and correlated failures.

**LockGraph:** Which lock-order cycles are structurally possible in observed traces? A cycle is a *potential* deadlock, not proof a deadlock occurred; the tool doesn't model release timing or try-lock semantics.

## Suggested next research steps

1. Add PostgreSQL EXPLAIN support and column-distribution generators to PlanCliff.
2. Add queueing, capacity and correlated latency to TailForge, then validate against a real HTTP benchmark.
3. Instrument real Python and Java lock events in LockGraph, track releases, and use a model checker for feasible interleavings.

## Responsible scope

These are transparent, testable research prototypes, **not** production-grade database, distributed-systems or static-analysis engines. The examples use synthetic inputs only. See each module's docstrings and tests before interpreting results.

MIT licensed. Contributions should include a reproducible failing case and a regression test.
