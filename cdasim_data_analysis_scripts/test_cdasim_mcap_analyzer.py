#!/usr/bin/env python3

import unittest
from pathlib import Path
from unittest.mock import patch

import cdasim_mcap_analyzer as analyzer


class CdasimMcapAnalyzerVehicleSelectionTest(unittest.TestCase):
    def _rosout_entries(self):
        return [
            analyzer.RosoutEntry(
                index=1,
                receive_timestamp_ns=1,
                stamp_ns=1,
                name="/carla_ros2_bridge",
                level=20,
                msg="[Spawner] Received spawn_point parameter: x=1.0, y=2.0",
            ),
            analyzer.RosoutEntry(
                index=2,
                receive_timestamp_ns=2,
                stamp_ns=2,
                name="/carla_ros2_bridge",
                level=20,
                msg="[Spawner] Spawned vehicle 'carma_2'",
            ),
        ]

    @patch.object(analyzer, "read_rosout_entries")
    def test_cdas_13_accepts_any_vehicle_when_name_is_omitted(self, read_entries):
        read_entries.return_value = (self._rosout_entries(), "rcl_interfaces/msg/Log")

        result = analyzer.evaluate_cdas_13(
            bag_path=Path("unused"),
            storage_id="mcap",
            topic="/rosout",
            vehicle_name=None,
            max_messages=None,
            csv_dir=None,
        )

        self.assertEqual("PASS", result.status)
        self.assertTrue(any("carma_2" in detail for detail in result.details))

    @patch.object(analyzer, "read_rosout_entries")
    def test_cdas_13_can_still_require_a_specific_vehicle(self, read_entries):
        read_entries.return_value = (self._rosout_entries(), "rcl_interfaces/msg/Log")

        result = analyzer.evaluate_cdas_13(
            bag_path=Path("unused"),
            storage_id="mcap",
            topic="/rosout",
            vehicle_name="carma_1",
            max_messages=None,
            csv_dir=None,
        )

        self.assertEqual("FAIL", result.status)


if __name__ == "__main__":
    unittest.main()
