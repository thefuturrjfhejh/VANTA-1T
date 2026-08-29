import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vanta_model", ROOT / "model" / "vanta_model.py")
assert SPEC and SPEC.loader
vanta = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = vanta
SPEC.loader.exec_module(vanta)


class VantaModelTests(unittest.TestCase):
    def setUp(self):
        self.model = vanta.ModelSpec()
        self.hardware = vanta.HardwareSpec()

    def test_routed_parameter_estimate_is_trillion_scale(self):
        self.assertGreater(self.model.routed_parameter_estimate, 1_000_000_000_000)
        self.assertLess(self.model.routed_parameter_estimate, 1_030_000_000_000)

    def test_stretch_weights_fit_four_48gb_stacks_at_8k(self):
        result = vanta.evaluate(
            self.model, self.hardware, vanta.VANTA_STRETCH, 8_192, 1, 8
        )
        self.assertTrue(result["fits"])
        self.assertGreater(result["hbm_headroom_gb"], 0)

    def test_stretch_beats_fifty_percent_memory_reduction(self):
        result = vanta.evaluate(
            self.model, self.hardware, vanta.VANTA_STRETCH, 8_192, 1, 8
        )
        self.assertGreater(result["weight_reduction_vs_mxfp4_pct"], 50)

    def test_quality_is_never_labeled_measured(self):
        report = vanta.build_report()
        self.assertIn("no silicon", report["status"])
        self.assertIn("unknown", " ".join(report["assumptions"]).lower())

    def test_kv_cache_scales_linearly(self):
        one = vanta.kv_cache_gb(self.model, 131_072, 1, 8)
        four = vanta.kv_cache_gb(self.model, 131_072, 4, 8)
        self.assertAlmostEqual(four, one * 4, places=8)

    def test_headline_values_remain_stable(self):
        headline = vanta.build_report()["headline"]
        self.assertAlmostEqual(headline["mxfp4_resident_weight_gb"], 563.74, places=2)
        self.assertAlmostEqual(headline["vanta_stretch_resident_weight_gb"], 180.06, places=2)
        self.assertAlmostEqual(headline["weight_reduction_vs_mxfp4_pct"], 68.06, places=2)


if __name__ == "__main__":
    unittest.main()
