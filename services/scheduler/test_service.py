import unittest

from service import MODEL_VERSION, readiness_report, recommend_payload


class SchedulerServiceTest(unittest.TestCase):
    def test_response_contains_model_and_request_metadata(self):
        result = recommend_payload(
            {
                "participants": [
                    {"name": "Bintang", "slots": {"slot-a": "available"}},
                    {"name": "Arimbi", "slots": {"slot-a": "tentative"}},
                ]
            }
        )
        self.assertEqual(result["model_version"], MODEL_VERSION)
        self.assertEqual(result["participant_count"], 2)
        self.assertEqual(result["recommendation_count"], 1)
        self.assertEqual(result["recommendations"][0]["score"], 0.75)

    def test_duplicate_participant_names_are_rejected(self):
        payload = {
            "participants": [
                {"name": "Bintang", "slots": {"slot-a": "available"}},
                {"name": "Bintang", "slots": {"slot-a": "available"}},
            ]
        }
        with self.assertRaisesRegex(ValueError, "names must be unique"):
            recommend_payload(payload)

    def test_candidate_slots_must_be_unique_non_empty_strings(self):
        payload = {
            "participants": [
                {"name": "Bintang", "slots": {"slot-a": "available"}},
            ],
            "candidate_slots": ["slot-a", "slot-a"],
        }
        with self.assertRaisesRegex(ValueError, "must not contain duplicates"):
            recommend_payload(payload)

    def test_readiness_self_check_is_ready(self):
        self.assertEqual(
            readiness_report(),
            {"status": "ready", "service": "scheduler", "model_version": MODEL_VERSION},
        )


if __name__ == "__main__":
    unittest.main()
