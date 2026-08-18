"""youtube_channel_fetcher.py의 순수 함수(네트워크 호출 없음)에 대한 단위 테스트.

실행:
    python -m unittest discover -s tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_channel_fetcher import parse_iso8601_duration_to_seconds


class TestParseIso8601DurationToSeconds(unittest.TestCase):
    def test_minutes_and_seconds(self):
        self.assertEqual(parse_iso8601_duration_to_seconds("PT13M8S"), 13 * 60 + 8)

    def test_hours_minutes_seconds(self):
        self.assertEqual(parse_iso8601_duration_to_seconds("PT1H2M3S"), 3600 + 120 + 3)

    def test_seconds_only_shorts(self):
        self.assertEqual(parse_iso8601_duration_to_seconds("PT45S"), 45)

    def test_hours_only(self):
        self.assertEqual(parse_iso8601_duration_to_seconds("PT2H"), 7200)

    def test_zero_duration(self):
        self.assertEqual(parse_iso8601_duration_to_seconds("PT0S"), 0)

    def test_invalid_string_returns_zero(self):
        self.assertEqual(parse_iso8601_duration_to_seconds("invalid"), 0)


if __name__ == "__main__":
    unittest.main()
