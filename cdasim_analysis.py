#!/usr/bin/env python3

import re
from pathlib import Path
from datetime import datetime


ANALYSIS_LOG = f"Cdasim_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def write_analysis(message: str) -> None:
    with open(ANALYSIS_LOG, "a", encoding="utf-8") as out:
        out.write(message + "\n")


def read_log_lines(log_file_path: str):
    path = Path(log_file_path)
    if not path.exists():
        write_analysis(f"log missing: {log_file_path}")
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def parse_log_timestamp(line: str):
    match = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line)
    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S,%f")
    except ValueError:
        return None


def Check_Vehicle_Spawn(carla_log_lines, vehicle_name: str) -> bool:
    pattern = re.compile(
        rf"Successfully spawned CARLA actor for SUMO vehicle\s+'{re.escape(vehicle_name)}'"
    )

    for line in carla_log_lines:
        if pattern.search(line):
            write_analysis(f"vehicle {vehicle_name} spawn successful")
            return True

    write_analysis(f"vehicle {vehicle_name} spawn unsuccessful")
    return False


def CheckXmlRpcServer(carla_log_lines) -> bool:
    target_phrase = "Multi-XML-RPC manager actor connection status: true"

    for line in carla_log_lines:
        if target_phrase in line:
            write_analysis("xml rpc server connect successful")
            return True

    write_analysis("xml rpc server connect unsuccessful")
    return False


def Count_Added_Vehicles_In_Carla_Log(carla_log_lines) -> int:
    pattern = re.compile(
        r"Received VehicleUpdates interaction.*added=(\d+), updated=(\d+), removed=(\d+)"
    )
    total_added = 0

    for line in carla_log_lines:
        match = pattern.search(line)
        if match:
            total_added += int(match.group(1))

    write_analysis(f"total added vehicles reported in carla log: {total_added}")
    return total_added



def Check_TimeSync_Sent(carma_log_lines, vehicle_name: str) -> bool:
    pattern = re.compile(
        rf"Sending Common instance\s+{re.escape(vehicle_name)}\b.*time sync message for time"
    )

    for line in carma_log_lines:
        if pattern.search(line):
            write_analysis(f"vehicle {vehicle_name} time sync message sent")
            return True

    write_analysis(f"vehicle {vehicle_name} time sync message not sent")
    return False


def Check_V2X_Message_Sent(carma_log_lines, vehicle_name: str) -> bool:
    pattern = re.compile(
        rf"Sending V2X message reception event for\s+{re.escape(vehicle_name)}\b"
    )

    for line in carma_log_lines:
        if pattern.search(line):
            write_analysis(f"vehicle {vehicle_name} v2x message sent")
            return True

    write_analysis(f"vehicle {vehicle_name} v2x message not sent")
    return False


def Check_Common_Instance_Registration(mosaic_log_lines, vehicle_name: str) -> bool:
    pattern = re.compile(
        rf"New Common instance '{re.escape(vehicle_name)}' received"
    )

    for line in mosaic_log_lines:
        if pattern.search(line):
            write_analysis(f"common instance registration found for {vehicle_name}")
            return True

    write_analysis(f"common instance registration not found for {vehicle_name}")
    return False


def Check_Carma_Instance_Registered(carma_log_lines, vehicle_name: str) -> bool:
    pattern = re.compile(
        rf"New CARMA instance\s+'{re.escape(vehicle_name)}'\s+registered with CARMA Instance Manager"
    )

    for line in carma_log_lines:
        if pattern.search(line):
            write_analysis(f"vehicle {vehicle_name} carma instance registered")
            return True

    write_analysis(f"vehicle {vehicle_name} carma instance not registered")
    return False


def Check_V2X_Message_Id_Paired(carma_log_lines, vehicle_name: str) -> int:
    processing_ids = set()
    sending_ids = set()

    processing_pattern = re.compile(
        rf"Processing V2X message reception event for\s+{re.escape(vehicle_name)}\s+of msg id\s+(\d+)"
    )
    sending_pattern = re.compile(
        rf"Sending V2X message reception event for\s+{re.escape(vehicle_name)}\s+of msg id\s+(\d+)"
    )

    for line in carma_log_lines:
        match = processing_pattern.search(line)
        if match:
            processing_ids.add(match.group(1))

        match = sending_pattern.search(line)
        if match:
            sending_ids.add(match.group(1))

    paired_ids = processing_ids & sending_ids
    processing_only = processing_ids - sending_ids
    sending_only = sending_ids - processing_ids

    write_analysis(f"vehicle {vehicle_name} v2x paired msg id count: {len(paired_ids)}")
    write_analysis(f"vehicle {vehicle_name} v2x processing-only msg id count: {len(processing_only)}")
    write_analysis(f"vehicle {vehicle_name} v2x sending-only msg id count: {len(sending_only)}")

    return len(paired_ids)


def Write_V2X_Message_Id_Details(carma_log_lines, vehicle_name: str) -> None:
    processing_ids = set()
    sending_ids = set()

    processing_pattern = re.compile(
        rf"Processing V2X message reception event for\s+{re.escape(vehicle_name)}\s+of msg id\s+(\d+)"
    )
    sending_pattern = re.compile(
        rf"Sending V2X message reception event for\s+{re.escape(vehicle_name)}\s+of msg id\s+(\d+)"
    )

    for line in carma_log_lines:
        match = processing_pattern.search(line)
        if match:
            processing_ids.add(match.group(1))

        match = sending_pattern.search(line)
        if match:
            sending_ids.add(match.group(1))

    paired_ids = sorted(processing_ids & sending_ids, key=int)
    processing_only = sorted(processing_ids - sending_ids, key=int)
    sending_only = sorted(sending_ids - processing_ids, key=int)

    write_analysis(f"vehicle {vehicle_name} paired v2x msg ids: {paired_ids}")
    write_analysis(f"vehicle {vehicle_name} processing-only v2x msg ids: {processing_only}")
    write_analysis(f"vehicle {vehicle_name} sending-only v2x msg ids: {sending_only}")


def Compare_Carma_And_Comm_Message_IDs(carma_log_lines, comm_log_lines, vehicle_name: str):
    carma_ids = set()
    comm_ids = set()

    carma_pattern = re.compile(
        rf"Sending V2X message reception event for\s+{re.escape(vehicle_name)}\s+of msg id\s+(\d+)"
    )
    comm_pattern = re.compile(r"insertV2XMessage:\s+id=(\d+)")

    for line in carma_log_lines:
        match = carma_pattern.search(line)
        if match:
            carma_ids.add(match.group(1))

    for line in comm_log_lines:
        match = comm_pattern.search(line)
        if match:
            comm_ids.add(match.group(1))

    matched_ids = carma_ids & comm_ids
    missing_in_comm = carma_ids - comm_ids

    write_analysis(f"matched carma->comm v2x msg ids count: {len(matched_ids)}")
    write_analysis(f"missing carma v2x ids in communicationdetails count: {len(missing_in_comm)}")

    if missing_in_comm:
        write_analysis(f"missing ids in communicationdetails: {sorted(missing_in_comm, key=int)}")

    return matched_ids


def Compare_Carma_And_Comm_Message_ID_Delays(
    carma_log_lines,
    comm_log_lines,
    vehicle_name: str,
    delay_threshold_sec: float = 0.1
):
    carma_id_to_time = {}
    comm_id_to_time = {}

    carma_pattern = re.compile(
        rf"Sending V2X message reception event for\s+{re.escape(vehicle_name)}\s+of msg id\s+(\d+)"
    )
    comm_pattern = re.compile(r"insertV2XMessage:\s+id=(\d+)")

    for line in carma_log_lines:
        match = carma_pattern.search(line)
        if match:
            msg_id = match.group(1)
            if msg_id not in carma_id_to_time:
                ts = parse_log_timestamp(line)
                if ts is not None:
                    carma_id_to_time[msg_id] = ts

    for line in comm_log_lines:
        match = comm_pattern.search(line)
        if match:
            msg_id = match.group(1)
            if msg_id not in comm_id_to_time:
                ts = parse_log_timestamp(line)
                if ts is not None:
                    comm_id_to_time[msg_id] = ts

    shared_ids = sorted(set(carma_id_to_time.keys()) & set(comm_id_to_time.keys()), key=int)

    delayed_count = 0

    for msg_id in shared_ids:
        delay_sec = (comm_id_to_time[msg_id] - carma_id_to_time[msg_id]).total_seconds()

        if delay_sec > delay_threshold_sec:
            delayed_count += 1
            write_analysis(
                f"v2x msg id {msg_id} delay too high: {delay_sec:.3f} sec "
                f"(carma -> communicationdetails)"
            )

    write_analysis(
        f"v2x msg ids over {delay_threshold_sec:.3f} sec delay count: {delayed_count}"
    )

    return delayed_count


def Count_Sumo_VehicleUpdates_Interactions(traffic_log_lines) -> int:
    target_phrase = "Got new interaction VehicleUpdates with time"
    count = sum(1 for line in traffic_log_lines if target_phrase in line)
    write_analysis(f"sumo vehicleupdates interaction count: {count}")
    return count


def Count_Sumo_VehicleFederateAssignment_Interactions(traffic_log_lines) -> int:
    target_phrase = "Got new interaction VehicleFederateAssignment with time"
    count = sum(1 for line in traffic_log_lines if target_phrase in line)
    write_analysis(f"sumo vehiclefederateassignment interaction count: {count}")
    return count


def Check_Sumo_Simulation_Time_Started(traffic_log_lines) -> bool:
    target_phrase = "Simulation Time:"
    found = any(target_phrase in line for line in traffic_log_lines)

    if found:
        write_analysis("sumo simulation time started")
    else:
        write_analysis("sumo simulation time not started")

    return found


def Check_Federation_Started(mosaic_log_lines) -> bool:
    target_phrase = "Start federation with id"
    found = any(target_phrase in line for line in mosaic_log_lines)

    write_analysis(f"federation started: {'yes' if found else 'no'}")
    return found


def Count_Initialized_Federates(mosaic_log_lines) -> int:
    target_phrase = "Federate "
    count = sum(
        1 for line in mosaic_log_lines
        if "is initializing" in line and target_phrase in line
    )

    write_analysis(f"initialized federate count: {count}")
    return count


def Count_Added_Federates(mosaic_log_lines) -> int:
    target_phrase = "Add ambassador/federate with id"
    count = sum(1 for line in mosaic_log_lines if target_phrase in line)

    write_analysis(f"added federate count: {count}")
    return count



def Count_Common_Instance_Registrations(mosaic_log_lines, vehicle_name: str) -> int:
    pattern = re.compile(
        rf"New Common instance '{re.escape(vehicle_name)}' received"
    )
    count = sum(1 for line in mosaic_log_lines if pattern.search(line))

    write_analysis(f"common registration count for {vehicle_name}: {count}")
    return count


def Count_V2X_Receiver_Starts(mosaic_log_lines) -> int:
    target_phrase = "CarmaV2xMessageReceiver started listening on UDP port"
    count = sum(1 for line in mosaic_log_lines if target_phrase in line)

    write_analysis(f"v2x receiver start count: {count}")
    return count


# =========================
# SUMMARY
# =========================

def Write_Summary(
    vehicle_name: str,
    spawn_ok: bool,
    xmlrpc_ok: bool,
    xmlrpc_false_count: int,
    xmlrpc_true_count: int,
    xmlrpc_recovered: bool,
    actor_not_connected_count: int,
    vehicleupdates_count: int,
    total_added_vehicles: int,
    sync_start_count: int,
    successful_actor_updates: int,
    existing_mapping_skips: int,
    add_without_sim_count: int,
    update_without_sim_count: int,
    sim_unit_problem: bool,
    carma_registered: bool,
    time_sync_ok: bool,
    time_sync_count: int,
    v2x_ok: bool,
    v2x_count: int,
    duplicate_registration_count: int,
    v2x_paired_count: int,
    comm_insert_count: int,
    comm_send_count: int,
    comm_v2x_healthy: bool,
    matched_comm_ids_count: int,
    delayed_v2x_count: int,
    comm_non_simulated_count: int,
    comm_duplicate_vehicle_count: int,
    sumo_connected: bool,
    sumo_retry_count: int,
    sumo_api_logged: bool,
    sumo_sim_started: bool,
    sumo_vehicleupdates_count: int,
    sumo_assignment_count: int,
    sumo_ignored_external_count: int,
    sumo_ignored_carma1_count: int,
    sumo_ignored_carma_source_count: int,
    sumo_ignored_msger_source_count: int,
    sumo_missing_assignment_issue: bool,
    federation_started: bool,
    initialized_federates: int,
    added_federates: int,
    no_mapping_spawners: bool,
    common_registration_count: int,
    common_registration_spam: bool,
    v2x_receiver_count: int,
) -> None:
    write_analysis("----- summary -----")
    write_analysis(f"vehicle checked: {vehicle_name}")
    write_analysis(f"spawn result: {'pass' if spawn_ok else 'fail'}")
    write_analysis(f"xml rpc result: {'pass' if xmlrpc_ok else 'fail'}")
    write_analysis(f"xml rpc false count: {xmlrpc_false_count}")
    write_analysis(f"xml rpc true count: {xmlrpc_true_count}")
    write_analysis(f"xml rpc recovered after failures: {'yes' if xmlrpc_recovered else 'no'}")
    write_analysis(f"actor server not connected warning count: {actor_not_connected_count}")
    write_analysis(f"vehicleupdates interaction count: {vehicleupdates_count}")
    write_analysis(f"total added vehicles reported in carla log: {total_added_vehicles}")
    write_analysis(f"sumo->carla sync start count: {sync_start_count}")
    write_analysis(f"successful actor update count: {successful_actor_updates}")
    write_analysis(f"existing actor mapping skip count: {existing_mapping_skips}")
    write_analysis(f"add vehicle without simulation unit count: {add_without_sim_count}")
    write_analysis(f"update vehicle without simulation unit count: {update_without_sim_count}")
    write_analysis(f"simulation unit issue: {'yes' if sim_unit_problem else 'no'}")
    write_analysis(f"carma instance registered: {'yes' if carma_registered else 'no'}")
    write_analysis(f"time sync sent: {'yes' if time_sync_ok else 'no'}")
    write_analysis(f"time sync sent count: {time_sync_count}")
    write_analysis(f"v2x message sent: {'yes' if v2x_ok else 'no'}")
    write_analysis(f"v2x message sent count: {v2x_count}")
    write_analysis(f"duplicate registration count: {duplicate_registration_count}")
    write_analysis(f"v2x paired msg id count: {v2x_paired_count}")

    write_analysis(f"communicationdetails inserted v2x count: {comm_insert_count}")
    write_analysis(f"communicationdetails ns3 send v2x count: {comm_send_count}")
    write_analysis(f"communicationdetails v2x healthy: {'yes' if comm_v2x_healthy else 'no'}")
    write_analysis(f"matched carma->comm v2x ids count: {matched_comm_ids_count}")
    write_analysis(f"v2x msg ids over 0.100 sec delay count: {delayed_v2x_count}")
    write_analysis(f"communicationdetails non-simulated node warnings: {comm_non_simulated_count}")
    write_analysis(f"communicationdetails duplicate vehicle warnings: {comm_duplicate_vehicle_count}")

    write_analysis(f"sumo connection result: {'pass' if sumo_connected else 'fail'}")
    write_analysis(f"sumo connection retry warning count: {sumo_retry_count}")
    write_analysis(f"sumo api version logged: {'yes' if sumo_api_logged else 'no'}")
    write_analysis(f"sumo simulation time started: {'yes' if sumo_sim_started else 'no'}")
    write_analysis(f"sumo vehicleupdates interaction count: {sumo_vehicleupdates_count}")
    write_analysis(f"sumo vehiclefederateassignment interaction count: {sumo_assignment_count}")
    write_analysis(f"sumo ignored external vehicle count: {sumo_ignored_external_count}")
    write_analysis(f"sumo ignored external vehicle count for {vehicle_name}: {sumo_ignored_carma1_count}")
    write_analysis(f"sumo ignored external vehicle count from carma: {sumo_ignored_carma_source_count}")
    write_analysis(f"sumo ignored external vehicle count from carma-messenger: {sumo_ignored_msger_source_count}")
    write_analysis(f"sumo missing VehicleFederateAssignment issue: {'yes' if sumo_missing_assignment_issue else 'no'}")

    write_analysis(f"federation started: {'yes' if federation_started else 'no'}")
    write_analysis(f"initialized federate count: {initialized_federates}")
    write_analysis(f"added federate count: {added_federates}")
    write_analysis(f"mapping config has no spawners: {'yes' if no_mapping_spawners else 'no'}")
    write_analysis(f"common registration count for {vehicle_name}: {common_registration_count}")
    write_analysis(f"common registration spam detected: {'yes' if common_registration_spam else 'no'}")
    write_analysis(f"v2x receiver start count: {v2x_receiver_count}")


def Write_Root_Cause_Hints(
    vehicle_name: str,
    spawn_ok: bool,
    xmlrpc_ok: bool,
    xmlrpc_recovered: bool,
    actor_not_connected_count: int,
    sim_unit_problem: bool,
    add_without_sim_count: int,
    update_without_sim_count: int,
    sync_start_count: int,
    successful_actor_updates: int,
    time_sync_ok: bool,
    v2x_ok: bool,
    duplicate_registration_count: int,
    comm_v2x_healthy: bool,
    sumo_retry_count: int,
    sumo_connected: bool,
    sumo_missing_assignment_issue: bool,
    sumo_ignored_carma1_count: int,
    sumo_ignored_msger_source_count: int,
    no_mapping_spawners: bool,
    common_registration_spam: bool,
    initialized_federates: int,
    added_federates: int,
) -> None:
    write_analysis("----- root cause hints -----")

    if not xmlrpc_ok:
        write_analysis("possible issue: actor xml rpc server did not become healthy")

    if xmlrpc_recovered:
        write_analysis("possible issue: actor xml rpc server had delayed startup / temporary readiness issue")

    if actor_not_connected_count > 0:
        write_analysis("possible issue: SUMO->CARLA sync was skipped during part of startup because actor server was not connected")

    if sim_unit_problem and (add_without_sim_count > 0 or update_without_sim_count > 0):
        write_analysis("possible issue: application side is missing or not attaching a simulation unit")

    if sync_start_count > 0 and successful_actor_updates > 0:
        write_analysis("actor synchronization eventually became healthy after initialization")

    if time_sync_ok:
        write_analysis("carma time sync messaging is active")

    if v2x_ok:
        write_analysis("carma v2x message flow is active")

    if duplicate_registration_count > 0:
        write_analysis("possible issue: carma vehicle registration is being repeated many times")

    if comm_v2x_healthy:
        write_analysis("communicationdetails indicates the network-layer v2x pipeline is active")

    if sumo_retry_count > 0 and sumo_connected:
        write_analysis("sumo needed at least one retry before TraCI connection succeeded")

    if sumo_missing_assignment_issue:
        write_analysis("possible issue: external vehicles are reaching SUMO before VehicleFederateAssignment is established")

    if sumo_ignored_carma1_count > 0:
        write_analysis(f"possible issue: vehicle {vehicle_name} was ignored by SUMO because no prior VehicleFederateAssignment was seen")

    if sumo_ignored_msger_source_count > 0:
        write_analysis("possible issue: carma-messenger vehicles were ignored by SUMO because no prior VehicleFederateAssignment was seen")

    if no_mapping_spawners:
        write_analysis("note: mapping config contains no spawners; only externally injected vehicles will appear")

    if common_registration_spam:
        write_analysis(f"possible issue: repeated Common registration for {vehicle_name} may indicate registration/assignment handshake loop")

    if initialized_federates != added_federates:
        write_analysis("possible issue: some initialized federates may not have been fully added to federation")

    if not spawn_ok and (not xmlrpc_ok or sim_unit_problem or sumo_missing_assignment_issue):
        write_analysis("possible issue: vehicle spawn failed because prerequisites were not healthy early in startup")


def get_latest_log_dir(base_path="/opt/carma-simulation/logs") -> Path:
    base = Path(base_path)

    if not base.exists():
        raise FileNotFoundError(f"Base log path not found: {base_path}")
    dirs = [d for d in base.iterdir() if d.is_dir()]

    if not dirs:
        raise RuntimeError("No log directories found")

    latest_dir = max(dirs, key=lambda d: d.stat().st_mtime)

    return latest_dir


if __name__ == "__main__":
    vehicle_name = "carma_1"

    log_dir = get_latest_log_dir()

    write_analysis(f"using log directory: {log_dir}")

    carla_log_path = log_dir / "Carla.log"
    application_log_path = log_dir / "Application.log"
    carma_log_path = log_dir / "Carma.log"
    comm_log_path = log_dir / "CommunicationDetails.log"
    traffic_log_path = log_dir / "Traffic.log"
    mosaic_log_path = log_dir / "Mosaic.log"

    with open(ANALYSIS_LOG, "w", encoding="utf-8") as out:
        out.write("Combined CARLA / Application / CARMA / CommunicationDetails / SUMO / MOSAIC log analysis\n")

    carla_log_lines = read_log_lines(carla_log_path)
    application_log_lines = read_log_lines(application_log_path)
    carma_log_lines = read_log_lines(carma_log_path)
    comm_log_lines = read_log_lines(comm_log_path)
    traffic_log_lines = read_log_lines(traffic_log_path)
    mosaic_log_lines = read_log_lines(mosaic_log_path)
    spawn_ok = Check_Vehicle_Spawn(carla_log_lines, vehicle_name)
    xmlrpc_ok = CheckXmlRpcServer(carla_log_lines)
    total_added_vehicles = Count_Added_Vehicles_In_Carla_Log(carla_log_lines)
    carma_registered = Check_Carma_Instance_Registered(carma_log_lines, vehicle_name)
    time_sync_ok = Check_TimeSync_Sent(carma_log_lines, vehicle_name)
    v2x_ok = Check_V2X_Message_Sent(carma_log_lines, vehicle_name)
    common_registration_found = Check_Common_Instance_Registration(mosaic_log_lines, vehicle_name)
    v2x_paired_count = Check_V2X_Message_Id_Paired(carma_log_lines, vehicle_name)
    Write_V2X_Message_Id_Details(carma_log_lines, vehicle_name)
    matched_comm_ids = Compare_Carma_And_Comm_Message_IDs(
        carma_log_lines,
        comm_log_lines,
        vehicle_name
    )
    delayed_v2x_count = Compare_Carma_And_Comm_Message_ID_Delays(
        carma_log_lines,
        comm_log_lines,
        vehicle_name,
        delay_threshold_sec=0.1
    )
    sumo_sim_started = Check_Sumo_Simulation_Time_Started(traffic_log_lines)
    sumo_vehicleupdates_count = Count_Sumo_VehicleUpdates_Interactions(traffic_log_lines)
    sumo_assignment_count = Count_Sumo_VehicleFederateAssignment_Interactions(traffic_log_lines)
    federation_started = Check_Federation_Started(mosaic_log_lines)
    initialized_federates = Count_Initialized_Federates(mosaic_log_lines)
    added_federates = Count_Added_Federates(mosaic_log_lines)
    common_registration_count = Count_Common_Instance_Registrations(mosaic_log_lines, vehicle_name)
    v2x_receiver_count = Count_V2X_Receiver_Starts(mosaic_log_lines)

    Write_Summary(
        vehicle_name,
        spawn_ok,
        xmlrpc_ok,
        total_added_vehicles,
        carma_registered,
        time_sync_ok,
        v2x_ok,
        common_registration_found,
        v2x_paired_count,
        len(matched_comm_ids),
        delayed_v2x_count,
        sumo_sim_started,
        sumo_vehicleupdates_count,
        sumo_assignment_count,
        federation_started,
        initialized_federates,
        added_federates,
        common_registration_count,
        v2x_receiver_count,
    )

    Write_Root_Cause_Hints(
        vehicle_name,
        spawn_ok,
        xmlrpc_ok,
        time_sync_ok,
        v2x_ok,
        common_registration_found,
        initialized_federates,
        added_federates,
    )