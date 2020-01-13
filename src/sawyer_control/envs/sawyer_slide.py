from collections import OrderedDict
from gym.spaces import Box, Tuple
from sawyer_control.envs.sawyer_env_base import SawyerEnvBase
from sawyer_control.core.serializable import Serializable
from wsg_50_common.srv import Move
from sawyer_control.srv import tactile
import numpy as np
import cv2
import rospy

class SawyerSlideEnv(SawyerEnvBase):

    def __init__(self,
                 action_mode='position',
                 goal_low=None,
                 goal_high=None,
                 reset_free=False,
                 **kwargs
                 ):
        Serializable.quick_init(self, locals())
        SawyerEnvBase.__init__(self, action_mode=action_mode, **kwargs)
        self.tactile = rospy.ServiceProxy('tactile_service', tactile, persistent=True)
        self.gripper_pos = rospy.ServiceProxy('/wsg_50_driver/move', Move, persistent=True)
        self.gripper_pos_scale = 30


    def _set_observation_space(self):
        # Tuple of (end eff force, tactile sensor readings array)
        # 14 x 6 tactile sensor reading (maybe need to double for both fingers??)
        # TODO: make the force reading bounds correct
        self.observation_space = Tuple(Box(low=0, high=100, shape=(3,)), 
                                        Box(low=0, high=3895, shape=(84,)))


    def _set_action_space(self):
        # x, y, z, finger_pos
        low = np.array([-1.,-1.,-1.,0.])
        high = np.ones(4)
        self.action_space = BSox(low, high, dtype=np.float32)


    def _position_act(self, action):
        # gripper position
        self.set_gripper_pos(action[3] * self.gripper_pos_scale)

        # end eff pose
        ee_pos = self._get_endeffector_pose()
        endeffector_pos = ee_pos[:3]
        target_ee_pos = (endeffector_pos + action[:3])
        target_ee_pos = np.clip(target_ee_pos, self.config.POSITION_SAFETY_BOX_LOWS, self.config.POSITION_SAFETY_BOX_HIGHS)
        target_ee_pos = np.concatenate((target_ee_pos, [self.config.POSITION_CONTROL_EE_ORIENTATION.x, self.config.POSITION_CONTROL_EE_ORIENTATION.y, self.config.POSITION_CONTROL_EE_ORIENTATION.z, self.config.POSITION_CONTROL_EE_ORIENTATION.w]))
        angles = self.request_ik_angles(target_ee_pos, self._get_joint_angles())
        self.send_angle_action(angles, target_ee_pos)


    def _get_obs(self):
        # get the reading from the end effector force and tactile sensor
        # TODO format the output into the Box 
        return self.tactile()

    def reset(self):
        self._reset_robot()
        return self._get_obs()

    def get_diagnostics(self, paths, prefix=''):
        return OrderedDict()

    def compute_rewards(self, actions, obs, goals):
        # TODO: compute rewards
        raise NotImplementedError('Use sliding distance????')


    # TODO: test custom ROS functions
    def _reset_robot(self):
        if not self.reset_free:
            self.open_gripper()
            for _ in range(5):
                self._position_act(self.pos_control_reset_position - self._get_endeffector_pose())

    def open_gripper():
        self.set_gripper_pos(50.0)
    
    def set_gripper_pos(pos):
        self.gripper_pos(float(pos), 20.0)