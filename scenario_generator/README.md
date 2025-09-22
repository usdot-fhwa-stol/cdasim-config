CDASim Scenario Generator
The CDASim Scenario Generator automates the deployment of CDASim, CARMA Streets, and vehicle services for simulation runs using Docker Compose. The generate_scenario.py script reads a config.yaml file to produce a sim_launch.sh bash script and associated .env files, eliminating manual configuration.
Prerequisites

Python 3.x with required packages:
Install dependencies: pip install pyyaml jinja2


Docker and Docker Compose installed.
Pre-existing docker-compose.yml files in the directories specified in config.yaml:
cdasim_config_dir (e.g., /path/to/cdasim-config)
street_config_dir (e.g., /path/to/carma-street)
carma_config_dir (e.g., /path/to/carma-config/basic_sim_vehicle)



Setup

Prepare Files:

Place the following in the same directory:
generate_scenario.py
sim_launch_template.sh.j2
config.yaml




Edit config.yaml:

Update config.yaml with valid directory paths and settings. Example:cdasim_config_dir: /path/to/cdasim-config
street_config_dir: /path/to/carma-street
carma_config_dir: /path/to/carma-config/basic_sim_vehicle
num_vehicles: 2
num_streets: 2
env_settings:
  cdasim:
    DOCKER_ORG: usdotfhwastol
    DOCKER_TAG: carma-system-4.10.0
    PROJECT_NAME: cdasim
  vehicles:
    - PROJECT_NAME: vehicle1
      CARMA_CONFIG_PATH: /path/to/carma-config
      DOCKER_ORG: usdotfhwastol
      DOCKER_TAG: carma-system-4.10.0
    - PROJECT_NAME: vehicle2
      CARMA_CONFIG_PATH: /path/to/carma-config
      DOCKER_ORG: usdotfhwastol
      DOCKER_TAG: carma-system-4.10.0
  streets:
    - PROJECT_NAME: street1
      DOCKER_ORG: usdotfhwastol
      DOCKER_TAG: carma-system-4.10.0
    - PROJECT_NAME: street2
      DOCKER_ORG: usdotfhwastol
      DOCKER_TAG: carma-system-4.10.0


Replace placeholder paths (e.g., /path/to/carma-config) with actual paths.
Adjust num_vehicles and num_streets as needed.



Usage

Generate Files:

Run the Python script:python generate_scenario.py


This generates:
sim_launch.sh in the current directory.
.env.cdasim in cdasim_config_dir.
.env.vehicle_1, .env.vehicle_2, etc., in carma_config_dir.
.env.street_1, .env.street_2, etc., in street_config_dir.




Run the Bash Script:

Execute the generated script:chmod +x sim_launch.sh
./sim_launch.sh


The script:
Creates a sim_net network for simulation-wide communication.
Launches CDASim services from cdasim_config_dir.
Launches vehicle services (including CARMA Platform) from carma_config_dir.
Launches CARMA Streets services from street_config_dir.
Returns to the original directory on completion or failure.





Notes

Directory Paths: Ensure paths in config.yaml are valid and writable for .env file creation.
Docker Compose: Predefined docker-compose.yml files must exist in the specified directories.
Error Handling: The sim_launch.sh script checks for directory navigation errors and exits gracefully.
Customization: Add environment variables to env_settings in config.yaml to include them in .env files.

For support or customization, contact the development team.