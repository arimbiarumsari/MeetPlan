import unittest

from recommender import ParticipantAvailability, rank_meeting_slots


class RankMeetingSlotsTest(unittest.TestCase):
    def test_busy_is_a_hard_constraint_and_best_slot_ranks_first(self):
        participants = [
            ParticipantAvailability(
                "Bintang",
                {"2026-09-18T09:00": "available", "2026-09-18T13:00": "busy"},
            ),
            ParticipantAvailability(
                "Arimbi",
                {
                    "2026-09-18T09:00": "tentative",
                    "2026-09-18T13:00": "available",
                },
            ),
            ParticipantAvailability(
                "Aston",
                {
                    "2026-09-18T09:00": "available",
                    "2026-09-18T13:00": "available",
                },
            ),
        ]

        result = rank_meeting_slots(participants)

        self.assertEqual([item["slot"] for item in result], ["2026-09-18T09:00"])
        self.assertEqual(result[0]["score"], 0.833)
        self.assertEqual(result[0]["tentative_count"], 1)

    def test_missing_response_is_not_assumed_available(self):
        participants = [
            ParticipantAvailability("Bintang", {"slot-a": "available"}),
            ParticipantAvailability("Arimbi", {}),
        ]

        self.assertEqual(rank_meeting_slots(participants), [])

    def test_invalid_state_is_rejected(self):
        participants = [
            ParticipantAvailability("Bintang", {"slot-a": "maybe"}),
        ]

        with self.assertRaisesRegex(ValueError, "invalid availability state"):
            rank_meeting_slots(participants)


if __name__ == "__main__":
    unittest.main()
