# Copyright 2026 Leidos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import py_trees

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import Idle
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.scenarioconfigs.scenario_configuration import ScenarioConfiguration


class Trb2027(BasicScenario):
    def __init__(
        self,
        world,
        ego_vehicles,
        config: ScenarioConfiguration,
        randomize: bool = False,
        debug_mode: bool = False,
        criteria_enable: bool = True,
        timeout=60,
    ) -> None:
        """
        :param world: CARLA world in which the scenario is running
        :param list[carla.Vehicle] ego_vehicles: CARLA vehicle objects created based on scenario XML configuration
        :param ScenarioConfiguration config: Specifications from scenario XML configuration
        :param bool randomize:
        :param bool debug_mode:
        :param bool criteria_enable:
        :param float timeout: Threshold (in seconds) after which test automatically fails

        :return: None
        :rtype: None
        """
        # Must be defined before super() call because BasicScenario
        # references is in its __init__() function.
        self.timeout = timeout

        super(Trb2027, self).__init__(
            "Trb2027",
            ego_vehicles,
            config,
            world,
            debug_mode=debug_mode,
            criteria_enable=criteria_enable,
        )

        self.world_map = CarlaDataProvider.get_map()
        self.other_actors_dict = {}

    def _initialize_actors(self, config: ScenarioConfiguration) -> None:
        """
        Note: this function overrides the one in BasicScenario (parent
        class), so this override is responsible for adding the actors
        defined in the scenario XML configuration.

        :param ScenarioConfiguration config: Specifications from
        scenario XML configuration
        :return: None
        """
        actors = CarlaDataProvider.request_new_actors(config.other_actors)

        self.other_actors_dict = {
            actor_config.rolename: actor
            for actor_config, actor in zip(config.other_actors, actors)
        }

    def _setup_scenario_trigger(self, _: ScenarioConfiguration) -> None:
        """
        Set up the scenario start trigger

        Note: this function overrides the abstract one in the
        BasicScenario parent class. The base class's implementation adds
        a trigger that prevents the scenario from starting until the
        ego vehicle drives some distance. We don't want that trigger
        for this scenario because the fire truck is a static prop, not
        a driven actor. Follow this link for more information:
        https://carla-scenariorunner.readthedocs.io/en/latest/creating_new_scenario/

        :return: None
        """
        pass

    def _create_behavior(self):
        """
        Setup the behavior for Trb2027

        Note: this function overrides the abstract one in the
        BasicScenario parent class.

        The fire truck is spawned by _initialize_actors() above (driven
        by the <other_actor> entry in the paired scenario XML) and has no
        active behavior of its own for this demo -- it just sits in place
        as a static prop for the Cooperative Perception detection. This
        root behavior only keeps the scenario alive.

        :return: Behavior tree root
        """
        root = py_trees.composites.Sequence(name="root_sequence")
        root.add_child(Idle(1, name="fire_truck_static"))

        return root

    def _create_test_criteria(self) -> list:
        """
        Setup the evaluation criteria for Trb2027

        Note: this function overrides the one in BasicScenario (parent class).

        :return: List of test criteria
        """
        return []

    def __del__(self):
        self.remove_all_actors()
