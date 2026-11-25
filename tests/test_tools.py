import unittest

from lockgraph.__main__ import analyze
from plancliff.__main__ import detect_cliffs, experiment
from tailforge.__main__ import percentile, simulate


class TestPlanCliff(unittest.TestCase):
    def test_measures_sqlite_query(self):
        result = experiment(100, 3, 0.8)
        self.assertEqual(result["rows"], 100)
        self.assertTrue(result["plan"])

    def test_cliff_detector(self):
        a = {"rows": 10, "p50_ms": 1, "plan": ["SCAN"]}
        b = {"rows": 100, "p50_ms": 4, "plan": ["SEARCH"]}
        self.assertEqual(len(detect_cliffs([a, b])), 1)


class TestTailForge(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(percentile([1, 2, 3], 50), 2)

    def test_hedge_never_slower_in_model(self):
        output = simulate(500, 6, 30, 7)
        self.assertLessEqual(output["hedged"]["p99_ms"], output["baseline"]["p99_ms"])
        self.assertGreaterEqual(output["work_amplification"], 1)
        self.assertEqual(output, simulate(500, 6, 30, 7))


class TestLockGraph(unittest.TestCase):
    def test_detects_cycle(self):
        report = analyze([["A", "B"], ["B", "A"]])
        self.assertEqual(report["potential_deadlocks"], [["A", "B", "A"]])

    def test_acyclic_trace(self):
        self.assertFalse(analyze([["A", "B", "C"]])["potential_deadlocks"])


if __name__ == "__main__":
    unittest.main()
