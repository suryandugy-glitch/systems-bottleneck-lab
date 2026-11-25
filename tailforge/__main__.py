"""Compare baseline and hedged fan-out requests on paired synthetic samples."""
import argparse
import json
import math
import random
import statistics


def percentile(values: list[float], p: float) -> float:
    if not values or not 0 <= p <= 100:
        raise ValueError("nonempty values and percentile 0..100 required")
    v = sorted(values)
    position = (len(v) - 1) * p / 100
    low = int(position)
    high = min(low + 1, len(v) - 1)
    return v[low] + (v[high] - v[low]) * (position - low)


def sample_latency(rng: random.Random, median_ms: float, sigma: float) -> float:
    return rng.lognormvariate(math.log(median_ms), sigma)


def simulate(requests: int, fanout: int, hedge_after_ms: float, seed: int,
             median_ms: float = 20, sigma: float = 1.0) -> dict:
    if requests < 1 or fanout < 1 or hedge_after_ms < 0 or median_ms <= 0 or sigma < 0:
        raise ValueError("invalid simulation parameters")
    rng = random.Random(seed)
    baseline, hedged = [], []
    extra = 0
    for _ in range(requests):
        original = [sample_latency(rng, median_ms, sigma) for _ in range(fanout)]
        effective = []
        for latency in original:
            if latency > hedge_after_ms:
                extra += 1
                retry = sample_latency(rng, median_ms, sigma)
                effective.append(min(latency, hedge_after_ms + retry))
            else:
                effective.append(latency)
        baseline.append(max(original))
        hedged.append(max(effective))
    def stats(items):
        return {"p50_ms": round(statistics.median(items), 3),
                "p95_ms": round(percentile(items, 95), 3),
                "p99_ms": round(percentile(items, 99), 3)}
    return {"seed": seed, "requests": requests, "fanout": fanout,
            "hedge_after_ms": hedge_after_ms, "baseline": stats(baseline),
            "hedged": stats(hedged), "work_amplification": round(1 + extra / (requests * fanout), 4)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=int, default=10000)
    parser.add_argument("--fanout", type=int, default=8)
    parser.add_argument("--hedge-after-ms", type=float, default=50)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--median-ms", type=float, default=20)
    parser.add_argument("--sigma", type=float, default=1)
    args = parser.parse_args()
    print(json.dumps(simulate(args.requests, args.fanout, args.hedge_after_ms,
                              args.seed, args.median_ms, args.sigma), indent=2))


if __name__ == "__main__":
    main()
