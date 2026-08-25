#  Copyright (C) 2018-2024 LEIDOS.
# 
#  Licensed under the Apache License, Version 2.0 (the "License"); you may not
#  use this file except in compliance with the License. You may obtain a copy of
#  the License at
# 
#  http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations under
#  the License.


FROM busybox:latest

ARG BUILD_DATE="NULL"
ARG VERSION="NULL"
ARG VCS_REF="NULL"
ARG CONFIG_NAME="cdasim-config:unspecified"

LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.name=${CONFIG_NAME}
LABEL org.label-schema.description="Docker Compose configuration for CDASim"
LABEL org.label-schema.vendor="Leidos"
LABEL org.label-schema.version=${VERSION}
LABEL org.label-schema.url="https://highways.dot.gov/research/research-programs/operations/CARMA"
LABEL org.label-schema.vcs-url="https://github.com/usdot-fhwa-stol/carma-config"
LABEL org.label-schema.vcs-ref=${VCS_REF}
LABEL org.label-schema.build-date=${BUILD_DATE}

COPY docker-compose.yml /root/carma-simulation/config/docker-compose.yml
VOLUME /opt/carma-simulation/config
RUN mkdir -p /opt/carma-simulation/config

CMD ["cp", "-a", "/root/carma-simulation/config/.", "/opt/carma-simulation/config/"]
