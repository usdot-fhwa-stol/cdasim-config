# PyEOS Bundle Folder
This folder serves as a placeholder where users can place the PyEOS bundle, a personal bundle provided by the Econolite team. The bundle file will be mounted to the EVC-SUMO Docker container when the `start_simulation.sh` script is executed.

The first time `start_simulation.sh` is run, EVC-SUMO will prompt for an Econolite login with a username and password. Upon successful login, the credentials will be stored in the Docker volume, and the bundle file will be automatically deleted.