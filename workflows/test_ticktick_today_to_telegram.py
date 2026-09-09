import unittest
from datetime import date

from workflows.ticktick_today_to_telegram import _message, _task_date


class TickTickTodayTests(unittest.TestCase):
    def test_converts_utc_date_to_tehran_date(self):
        self.assertEqual(_task_date("2026-09-08T20:30:00.000+0000"), date(2026, 9, 9))

    def test_formats_task_message(self):
        message = _message([{"title": "A & B"}])
        self.assertIn("<b>TickTick Today</b>", message)
        self.assertIn("• A &amp; B", message)


if __name__ == "__main__":
    unittest.main()
