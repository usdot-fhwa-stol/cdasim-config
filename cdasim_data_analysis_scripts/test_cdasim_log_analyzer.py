#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

import cdasim_log_analyzer as analyzer


class CdasimLogAnalyzerStructuredEventTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_analysis_log = analyzer.ANALYSIS_LOG
        analyzer.ANALYSIS_LOG = Path(self.temp_dir.name) / "analysis.log"

    def tearDown(self):
        analyzer.ANALYSIS_LOG = self.original_analysis_log
        self.temp_dir.cleanup()

    def test_spawn_request_and_result_are_paired_by_actor_id(self):
        lines = [
            "CDAS_EVENT event=carla_spawn_request actor_type=vehicle.tesla.model3 "
            "actor_id=carma_2 location=[1.0, 2.0, 0.0] rotation=[0.0, 90.0, 0.0] "
            "attributes={role_name=carma_2}\n",
            "CDAS_EVENT event=carla_spawn_result actor_id=carma_2 carla_id=42 "
            "result_type=Integer accepted=true\n",
        ]

        calls = analyzer.Parse_Carla_Spawn_Actor_Calls(lines)

        self.assertEqual(1, len(calls))
        self.assertEqual("carma_2", calls[0]["id"])
        self.assertEqual("42", calls[0]["carla_id"])
        self.assertEqual([1.0, 2.0, 0.0], calls[0]["location"])

    def test_vehicle_update_and_timestep_events_are_parsed(self):
        lines = [
            "CDAS_EVENT event=carla_vehicle_updates_published added=1 updated=0 removed=0\n",
            "CDAS_EVENT event=carla_next_timestep time_ns=100000000\n",
            "CDAS_EVENT event=carla_vehicle_updates_received time_ns=100000000 "
            "added=0 updated=1 removed=0\n",
        ]

        blocks = analyzer.Parse_Carla_To_Sumo_VehicleUpdates_By_Timestep(lines)
        received = analyzer.Parse_Carla_Received_VehicleUpdates(lines)

        self.assertEqual(100000000, blocks[0]["time"])
        self.assertEqual(1, blocks[0]["vehicleupdates"][0]["added"])
        self.assertEqual(1, received[0]["updated"])

    def test_structured_v2x_events_preserve_sender_receiver_and_time(self):
        lines = [
            "2026-10-07 12:00:00,000 INFO CDAS_EVENT event=v2x_message_inserted "
            "message_id=91 sender=carma_1 external_id=1 channel=CCH time_ns=200\n",
            "2026-10-07 12:00:00,001 INFO CDAS_EVENT event=v2x_message_received "
            "message_id=91 receiver=rsu_1234 time_ns=250\n",
        ]

        sent = analyzer.Parse_Comm_Sent_By_Node(lines, "carma_1")
        received = analyzer.Parse_Comm_Received_By_Node(lines, "rsu_1234")
        nodes = analyzer.Parse_Comm_Node_Names(lines)

        self.assertEqual(200, sent[91]["send_time_ns"])
        self.assertEqual(250, received[91]["recv_time_ns"])
        self.assertEqual(["carma_1", "rsu_1234"], nodes)

    def test_legacy_v2x_events_remain_supported(self):
        lines = [
            "2026-10-07 12:00:00,000 INFO insertV2XMessage: id=91 from node "
            "ID[int=carma_1 , ext=1] channel:CCH time=200\n",
            "2026-10-07 12:00:00,001 INFO Receive V2XMessage : Id(91) on Node "
            "rsu_1234 at Time=250\n",
        ]

        self.assertIn(91, analyzer.Parse_Comm_Sent_By_Node(lines, "carma_1"))
        self.assertIn(91, analyzer.Parse_Comm_Received_By_Node(lines, "rsu_1234"))

    def test_registration_and_time_sync_events_are_found(self):
        mosaic_lines = [
            "CDAS_EVENT event=common_instance_received instance_id=carma_3\n",
        ]
        carma_lines = [
            "CDAS_EVENT event=carma_instance_registered instance_id=carma_3\n",
            "CDAS_EVENT event=common_time_sync_sent instance_id=carma_3 "
            "target=/127.0.0.1 port=1517 time_ns=100\n",
            "CDAS_EVENT event=common_registration_duplicate instance_id=carma_3\n",
        ]

        self.assertTrue(analyzer.Check_Common_Instance_Registration(mosaic_lines, "carma_3"))
        self.assertTrue(analyzer.Check_Carma_Instance_Registered(carma_lines, "carma_3"))
        self.assertTrue(analyzer.Check_TimeSync_Sent(carma_lines, "carma_3"))
        self.assertEqual(1, analyzer.Count_Duplicate_Registrations(carma_lines, "carma_3"))

    def test_lifecycle_events_are_found(self):
        mosaic_lines = [
            "CDAS_EVENT event=federation_started federation_id=Town10\n",
            "CDAS_EVENT event=federate_initializing federate_id=carla\n",
            "CDAS_EVENT event=federate_added federate_id=carla\n",
            "CDAS_EVENT event=mapping_no_spawners configured=false\n",
            "CDAS_EVENT event=v2x_receiver_started port=1516\n",
        ]
        sumo_lines = [
            "CDAS_EVENT event=sumo_connection_established host=localhost port=8813\n",
            "CDAS_EVENT event=sumo_api_version api_version=20 sumo_version=1.20.0\n",
            "CDAS_EVENT event=sumo_simulation_time time_ms=100 wall_time_ms=1 "
            "next_time_ns=200000000 ambassador_id=sumo\n",
        ]

        self.assertTrue(analyzer.Check_Federation_Started(mosaic_lines))
        self.assertEqual(1, analyzer.Count_Initialized_Federates(mosaic_lines))
        self.assertEqual(1, analyzer.Count_Added_Federates(mosaic_lines))
        self.assertTrue(analyzer.Check_No_Mapping_Spawners(mosaic_lines))
        self.assertEqual(1, analyzer.Count_V2X_Receiver_Starts(mosaic_lines))
        self.assertTrue(analyzer.Check_Sumo_Connected(sumo_lines))
        self.assertTrue(analyzer.Check_Sumo_Api_Logged(sumo_lines))
        self.assertTrue(analyzer.Check_Sumo_Simulation_Time_Started(sumo_lines))


if __name__ == "__main__":
    unittest.main()
