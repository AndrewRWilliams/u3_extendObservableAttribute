# coding=utf-8
# Copyright 2019 The SEED Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 		 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Atari env factory."""

import tempfile
from mlagents_envs.environment import UnityEnvironment
from absl import flags
from absl import logging
import gymnasium as gym
from pathlib import Path
import uuid


import subprocess
from typing import Dict, List, Optional, Any, Tuple
from mlagents_envs.side_channel.side_channel import (
    SideChannel,
    IncomingMessage,
    OutgoingMessage,
)
import mlagents_envs
from mlagents_envs.logging_util import get_logger
from mlagents_envs.exception import (
    UnityEnvironmentException,
    UnityActionException,
    UnityTimeOutException,
    UnityCommunicatorStoppedException,
)
from mlagents_envs.base_env import BaseEnv

# from mlagents_envs.envs.unity_gym_env import UnityToGymWrapper
from unity_gym_env_pettingzoo_rewrite import UnityToPettingzooWrapper


FLAGS = flags.FLAGS

# Environment settings.
flags.DEFINE_string("game", "ButtonGame", "Game name.")
flags.DEFINE_integer("num_action_repeats", 1, "Number of action repeats.")
flags.DEFINE_integer(
    "max_random_noops",
    30,
    "Maximal number of random no-ops at the beginning of each " "episode.",
)


# Create the StringLogChannel class
class U3SideChannel(SideChannel):
    def __init__(self) -> None:
        super().__init__(uuid.UUID("621f0a70-4f87-11ea-a6bf-784f4387d1f7"))

    def on_message_received(self, msg: IncomingMessage) -> None:
        """
        Note: We must implement this method of the SideChannel interface to
        receive messages from Unity
        """
        # We simply read a string from the message and print it.
        message = str(msg.get_raw_bytes()[4:], "utf_8")
        self.environment.lastEnvironment = message
        # print('Unity output: {}'.format(message[0:100]))

    def send_string(self, data: str) -> None:
        # Add the string to an OutgoingMessage
        msg = OutgoingMessage()
        msg.write_string(data)
        # We call this method to queue the data we want to send
        super().queue_message_to_send(msg)

    def set_environment(self, environment):
        self.environment = environment


class U3Environment(UnityEnvironment):
    def __init__(
        self,
        file_name: Optional[str] = None,
        worker_id: int = 0,
        base_port: Optional[int] = None,
        seed: int = 0,
        no_graphics: bool = False,
        timeout_wait: int = 60,
        args: Optional[List[str]] = None,
        side_channels: Optional[List[SideChannel]] = None,
    ):
        super(U3Environment, self).__init__(
            file_name=file_name,
            worker_id=worker_id,
            base_port=base_port,
            seed=seed,
            no_graphics=no_graphics,
            timeout_wait=timeout_wait,
            side_channels=side_channels,
        )

    """def executable_launcher(self, file_name, no_graphics, args):
		launch_string = self.validate_environment_path(file_name)
		if launch_string is None:
			self._close(0)
			raise UnityEnvironmentException(
				f"Couldn't launch the {file_name} environment. Provided filename does not match any environments."
			)
		else:
			logger.debug("This is the launch string {}".format(launch_string))
			# Launch Unity environment
			subprocess_args = ['export LD_LIBRARY_PATH=/usr/lib/mesa-diverted/x86_64-linux-gnu;', 'xvfb-run', '--auto-servernum', '--server-args="-screen 0 100x100x24"', launch_string]
			if no_graphics:
				subprocess_args += ["-nographics", "-batchmode"]
			subprocess_args += [UnityEnvironment.PORT_COMMAND_LINE_ARG, str(self.port)]
			subprocess_args += args

			try:
				self.proc1 = subprocess.Popen(
					" ".join(subprocess_args),
					# start_new_session=True means that signals to the parent python process
					# (e.g. SIGINT from keyboard interrupt) will not be sent to the new process on POSIX platforms.
					# This is generally good since we want the environment to have a chance to shutdown,
					# but may be undesirable in come cases; if so, we'll add a command-line toggle.
					# Note that on Windows, the CTRL_C signal will still be sent.
					start_new_session=True, shell=True
				)
			except PermissionError as perm:
				# This is likely due to missing read or execute permissions on file.
				raise UnityEnvironmentException(
					f"Error when trying to launch environment - make sure "
					f"permissions are set correctly. For example "
					f'"chmod -R 755 {launch_string}"'
				) from perm"""


class U3Wrapper(UnityToPettingzooWrapper):
    def __init__(
        self,
        unity_env: BaseEnv,
        sideChannel: U3SideChannel,
        uint8_visual: bool = False,
        flatten_branched: bool = False,
        allow_multiple_obs: bool = False,
    ):
        self.sideChannel = sideChannel
        self.sideChannel.set_environment(self)
        self.lastEnvironment = ""
        super(U3Wrapper, self).__init__(
            unity_env=unity_env,
            uint8_visual=uint8_visual,
            flatten_branched=flatten_branched,
            allow_multiple_obs=allow_multiple_obs,
        )

    def seed(self, seed: Any = None) -> None:
        """Sets the seed for this env's random number generator(s).
        Currently not implemented.
        """
        self.sideChannel.send_string("seed{}".format(seed))
        return

    def setTraining(self, isTraining: bool) -> None:
        """Sets the seed for this env's random number generator(s).
        Currently not implemented.
        """
        if isTraining:
            self.sideChannel.send_string("training1")
        else:
            self.sideChannel.send_string("training0")

        return

    def setStatic(self, isStatic: bool) -> None:
        """Sets the seed for this env's random number generator(s).
        Currently not implemented.
        """
        if isStatic:
            self.sideChannel.send_string("static1")
        else:
            self.sideChannel.send_string("static0")

        return

    def setElement(self, elementName: str, elementData: str) -> None:
        """Sets the seed for this env's random number generator(s).
        Currently not implemented.
        """
        self.sideChannel.send_string(
            "element{}|{}".format(elementName, elementData)
        )

        return

    def clearElements(self) -> None:
        """Sets the seed for this env's random number generator(s).
        Currently not implemented.
        """
        self.sideChannel.send_string("reset")

        return


def create_environment(task):
    # logging.info('Creating environment: %s', FLAGS.game)

    # print(FLAGS)
    # print(task)
    # print(FLAGS.run_mode)

    # full_game_name = '{}'.format(FLAGS.game)
    # import os
    # modeOffset = FLAGS.run_mode == 'actor'
    # path = Path(__file__).parent.absolute()
    environmentChannel = U3SideChannel()
    unity_env = U3Environment(side_channels=[environmentChannel])
    env = U3Wrapper(
        unity_env, environmentChannel, flatten_branched=True, uint8_visual=True
    )
    env.seed(task)

    return env
