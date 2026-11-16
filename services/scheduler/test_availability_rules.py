import unittest

from availability_rules import (
    AvailabilityPolicy,
    AvailabilityRule,
    HardConstraintRule,
    WeightedAvailabilityRule,
)


class AvailabilityRulesTest(unittest.TestCase):
    def test_inheritance_and_polymorphic_evaluate(self):
        rules: tuple[AvailabilityRule, ...] = (
            WeightedAvailabilityRule("available", 1.0),
            HardConstraintRule("busy"),
        )

        self.assertTrue(all(isinstance(rule, AvailabilityRule) for rule in rules))
        self.assertEqual(rules[0].evaluate("available").score, 1.0)
        self.assertFalse(rules[1].evaluate("busy").accepted)

    def test_encapsulation_exposes_read_only_states(self):
        rule = WeightedAvailabilityRule("tentative", 0.5)

        self.assertEqual(rule.states, frozenset({"tentative"}))
        with self.assertRaises(AttributeError):
            rule.states.add("busy")

    def test_policy_scores_all_supported_states(self):
        policy = AvailabilityPolicy()

        self.assertEqual(policy.evaluate("available").score, 1.0)
        self.assertEqual(policy.evaluate("tentative").score, 0.5)
        self.assertFalse(policy.evaluate("busy").accepted)
        self.assertFalse(policy.evaluate(None).accepted)


if __name__ == "__main__":
    unittest.main()
