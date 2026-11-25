"""Find minimal lock-order cycles implied by acquisition sequences."""
import argparse
import json


def graph_from_traces(traces: list[list[str]]) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = {}
    for trace in traces:
        if not isinstance(trace, list) or any(not isinstance(x, str) or not x for x in trace):
            raise ValueError("each trace must be a list of nonempty lock names")
        for index, lock in enumerate(trace):
            edges.setdefault(lock, set())
            for later in trace[index + 1:]:
                if later != lock:
                    edges[lock].add(later)
                    edges.setdefault(later, set())
    return edges


def cycles(edges: dict[str, set[str]]) -> list[list[str]]:
    """Return one canonical witness for each distinct simple directed cycle."""
    found = set()
    for start in sorted(edges):
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            for neighbor in sorted(edges[node]):
                if neighbor == start and len(path) > 1:
                    found.add(tuple(path + [start]))
                elif neighbor not in path and neighbor >= start:
                    stack.append((neighbor, path + [neighbor]))
    return [list(cycle) for cycle in sorted(found)]


def analyze(traces: list[list[str]]) -> dict:
    graph = graph_from_traces(traces)
    return {"locks": sorted(graph), "edges": {k: sorted(v) for k, v in sorted(graph.items())},
            "potential_deadlocks": cycles(graph)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_file", help='JSON object with "traces": [["A","B"],...]')
    args = parser.parse_args()
    with open(args.trace_file, encoding="utf-8") as source:
        data = json.load(source)
    print(json.dumps(analyze(data["traces"]), indent=2))


if __name__ == "__main__":
    main()
