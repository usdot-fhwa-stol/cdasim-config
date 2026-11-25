# Basic CDASim Configuration Image

This image provides the Docker Compose configuration used by Scenario Runner
for the CDASim portion of an XIL scenario.

The Compose project contains only these services:

- `cdasim`
- `carla-sensor-lib`
- `xml-rpc-server`

Vehicle, CARMA Street, and CARMA Cloud services are configured by their own
components and are intentionally not included here.

The configuration is stored at `/opt/carma-simulation/config` in the configuration
container. The Docker Compose file is available at
`/opt/carma-simulation/config/docker-compose.yml`.

Run `./build-image.sh` to build a release image, or
`./build-image.sh --develop` to build a development image.
