import unittest

from lab.domain import adapt_event, build_events, validate_event


class EventContractTests(unittest.TestCase):
    def test_fixture_has_seventeen_v1_and_three_v2_events(self):
        events = build_events(20)
        self.assertEqual(len(events), 20)
        self.assertEqual(sum("consent" in event for event in events), 17)
        self.assertEqual(sum("consent_v2" in event for event in events), 3)
        self.assertEqual(len({event["event_id"] for event in events}), 20)

    def test_hardened_contract_rejects_v2_with_reason(self):
        consent, reason = validate_event(build_events(20)[-1])
        self.assertIsNone(consent)
        self.assertIn("consent_v2", reason)

    def test_reviewed_adapter_accepts_v2_and_preserves_value(self):
        event = build_events(20)[-1]
        consent, reason = adapt_event(event)
        self.assertIsNone(reason)
        self.assertTrue(consent)

    def test_contract_rejects_non_boolean_consent(self):
        event = build_events(20)[0]
        event["consent"] = "yes"
        consent, reason = validate_event(event)
        self.assertIsNone(consent)
        self.assertEqual(reason, "field consent must be boolean")


if __name__ == "__main__":
    unittest.main()
