import unittest

from oym.cost import ClaudeProfile, break_even, claude_cost_per_1k, self_host_monthly

PRICE = {"input": 0.10, "cache_write_5m": 0.125, "cache_read": 0.01, "output": 0.50}


class CostTests(unittest.TestCase):
    def profile(self):
        return ClaudeProfile(input=0, cache_write=1000, cache_read=2000, output=100, thinking=60,
                             cli_cost_per_1k=0, n_tasks=10, source_run="x")

    def test_claude_api_cost(self):
        # 1000 fresh x 0.10 + 2000 cached x 0.01 + 100 out x 0.50 = 170 per M tokens -> $0.17 per 1k
        self.assertAlmostEqual(claude_cost_per_1k(self.profile(), PRICE), 0.17)
        self.assertAlmostEqual(claude_cost_per_1k(self.profile(), PRICE, 0.5), 0.085)
        # without the 60 thinking tokens: 100 + 20 + 20 = 140 -> $0.14 per 1k
        self.assertAlmostEqual(claude_cost_per_1k(self.profile(), PRICE, thinking=False), 0.14)

    def test_self_host_always_pays_for_one_gpu(self):
        bill, gpus = self_host_monthly(1, items_per_second=1.0, gpu_hourly=1.0, hours=730, max_util=0.6)
        self.assertEqual((bill, gpus), (730.0, 1))
        cap = 1.0 * 3600 * 730 * 0.6
        self.assertEqual(self_host_monthly(cap + 1, 1.0, 1.0)[1], 2)

    def test_break_even(self):
        # renting costs $1 per 1k; owning costs a flat $100/month -> break-even near 100k/month
        v = break_even(1.0, lambda vol: 100.0)
        self.assertTrue(100_000 <= v < 105_100)
        self.assertIsNone(break_even(1.0, lambda vol: vol))  # owning always dearer


if __name__ == "__main__":
    unittest.main()
