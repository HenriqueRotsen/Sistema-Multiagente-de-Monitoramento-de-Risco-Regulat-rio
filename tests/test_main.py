"""Testes do modo de monitoramento contínuo."""
import unittest
from unittest.mock import Mock, patch

from main import RegulatoryMonitoringSystem


class TestContinuousMonitoring(unittest.TestCase):
    def setUp(self):
        self.system = RegulatoryMonitoringSystem.__new__(RegulatoryMonitoringSystem)
        self.system.run_monitoring_cycle = Mock(return_value={"errors": []})

    @patch("main.time.sleep", side_effect=KeyboardInterrupt)
    def test_run_forever_runs_immediately_then_waits(self, mock_sleep):
        with self.assertRaises(KeyboardInterrupt):
            self.system.run_forever(interval_seconds=3600)

        self.system.run_monitoring_cycle.assert_called_once_with()
        mock_sleep.assert_called_once_with(3600)

    def test_run_forever_rejects_non_positive_interval(self):
        with self.assertRaises(ValueError):
            self.system.run_forever(interval_seconds=0)

    @patch("main.time.sleep", side_effect=KeyboardInterrupt)
    def test_run_forever_waits_after_unexpected_cycle_failure(self, mock_sleep):
        self.system.run_monitoring_cycle.side_effect = RuntimeError("falha")

        with self.assertLogs("main", level="ERROR"):
            with self.assertRaises(KeyboardInterrupt):
                self.system.run_forever(interval_seconds=30)

        mock_sleep.assert_called_once_with(30)


if __name__ == "__main__":
    unittest.main()
