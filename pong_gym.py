import gym
from gym import spaces, logger

import os
import game
import numpy as np
import configparser



class Pong(gym.Env):
	def __init__(self, ini_file):
		super(Pong, self).__init__()

		thisfolder = os.path.dirname(os.path.abspath(__file__))
		self.ini_file = os.path.join(thisfolder, ini_file)
		self.read_config(self.ini_file)

		#0=right, 1=left
		self.side = 0

		self.score_reward = 10
		self.bounce_reward = 1

		self.reset()

		self.action_space = spaces.Discrete(3)

		low = np.array([0]*6, dtype=np.float32)
		high = np.array([1]*6, dtype=np.float32)
		self.observation_space = spaces.Box(low, high, shape=low.shape, dtype=np.float32)

	def read_config(self, file_name):
		config = configparser.ConfigParser()
		config.read(file_name)
		config = config["game-states"]

		self.table_size = tuple(map(int, config["table_size"].strip(" ").strip("(").strip(")").split(",")))
		self.paddle_size = tuple(map(int, config["paddle_size"].strip(" ").strip("(").strip(")").split(",")))
		self.ball_size = tuple(map(int, config["ball_size"].strip(" ").strip("(").strip(")").split(",")))
		self.paddle_speed = config.getfloat("paddle_speed")
		self.max_angle = config.getfloat("max_angle")

		self.paddle_bounce = config.getfloat("paddle_bounce")
		self.wall_bounce = config.getfloat("wall_bounce")
		self.dust_error = config.getfloat("dust_error")
		self.init_speed_mag = config.getfloat("init_speed_mag")
		self.timeout = config.getfloat("timeout")
		self.clock_rate = config.getfloat("clock_rate")
		self.turn_wait_rate = config.getfloat("turn_wait_rate")
		self.score_to_win = config.getint("score_to_win")


	def reset(self):
		self.game = game.init_game(self.ini_file, self.side)
		self.side = 1-self.side
		self.state = (0, 0), self.game.paddles[1-self.game.side].frect.copy(), self.game.paddles[self.game.side].frect.copy()
		self.old_ball_pos = [0.5, 0.5]
		return self.normalize()


	def normalize(self):
		ball_pos = [(p+s/2)/t for p, s, t in zip(self.game.ball.frect.pos, self.game.ball.frect.size, self.table_size)]
		# print(self.game.ball.frect.pos)
		ball_pos[0] = self.game.side-ball_pos[0]*self.game.side

		own_pos = [(p+s/2)/t for p, s, t in zip(self.state[1].pos, self.state[1].size, self.table_size)]
		enemy_pos = [(p+s/2)/t for p, s, t in zip(self.state[2].pos, self.state[2].size, self.table_size)]
		# print(self.state[1].pos)


		self.old_ball_pos, old_ball_pos = ball_pos, self.old_ball_pos

		return np.array([*ball_pos, *old_ball_pos, own_pos[1], enemy_pos[1]], dtype=np.float32)

	def step(self, action):
		err_msg = "%r (%s) invalid" % (action, type(action))
		assert self.action_space.contains(action), err_msg

		move = ["up", "stay", "down"][round(action)]

		self.state = self.game.tick(move)
		done = self.state == "ended"

		if done:
			return np.array([0]*10), 0, done, {}

		reward = 0
		if self.game.score != self.game.old_score:
			if self.game.score[1-self.game.side] != self.game.old_score[1-self.game.side]:
				reward += self.score_reward
				# print("Score")
			else:
				reward -= self.score_reward
				# print("Scored on")

		if self.game.ball.bounced:
			if self.game.ball.prev_bounce == self.game.paddles[1-self.side]:
				reward += self.bounce_reward
				# print("Bounced")
			else:
				reward -= self.bounce_reward
				# print("Opponent bounced")

		# if reward != 0: print("Reward:", reward)

		return self.normalize(), reward, done, {}

	def render(self):
		self.game.display = True


if __name__ == '__main__':
	game = Pong("training.ini")