import math
import numpy as np
from time import perf_counter_ns as timer
import multiprocessing as mp
from functools import partial
times = []

instance = None

def angle(dy, v):
	"""Find the new angle of a ball given the balls velocity and """
	if v[0]>0:
		s = 1
	else:
		s = -1

	theta = max(min(s*dy*0.011219974, 0.5), -0.5)

	v = [-math.cos(theta)*v[0]+math.sin(theta)*v[1],
		 math.sin(theta)*v[0]+math.cos(theta)*v[1]]
	v = [(math.cos(-theta)*v[0]-math.sin(-theta)*v[1])*1.2,
		 (math.cos(-theta)*v[1]+math.sin(-theta)*v[0])*1.2]

	return v


def predict(pos, old_pos):
	start = timer()
	#Between 90 and 270 means headed to the left
	if pos[0] < old_pos[0]:
		x = 27.5
	elif pos[0] > old_pos[0]:
		x = 412.5
	else:
		raise Exception("Ball not moving sideways from: {} to {}".format(*map(tuple, [old_pos, pos])))

	m = (pos[1]-old_pos[1])/(pos[0]-old_pos[0])
	l = m*x+pos[1]-m*pos[0]-7.5
	p = math.floor(l/265)

	265*(p%2)+((-1)**p)*(l%265)+7.5
	print((timer()-start)/1000000)

	return x, 265*(p%2)+((-1)**p)*(l%265)+7.5


def preformance(possible, v, hit, enemy):
	#The possible velocites of the ball depending on intercept
	new_velo = angle(hit[1]-possible, v)
	#Where on the opponents side the ball hits
	result = predict((hit[0]+new_velo[0], hit[1]+new_velo[1]), hit)
	#How much longer the opponent takes to intercept than the ball takes to reach their side
	preformance = abs(enemy-result[1])+35-385/abs(result[0])

	return preformance, result, possible


class Player:
	"""A pong player that minimaxes each move"""
	def __init__(self):
		global instance
		instance = self

	def __call__(self, *args):
		"""Return a move given the board state. Player tries to maximize how far the ball lands from where the opponent can move"""
		self.tracking(*args)

		if self.tick > 0:
			towards_self = (self.ball[0] < self.ball_prev[0]) == self.side
			if towards_self:
				desired_y = self.best_y()
			else:
				desired_y = 140
		else:
			self.store_tick()
			return None

		self.move = self.y_to_move(desired_y)
		self.store_tick()
		return self.move

	def best_y(self):
		preformances, results, possible = self.compute()
		return self.choose(preformances, results, possible)

	def choose(self, preformances, results, possible):
		"""Choose which of the possible ys to use given the results of compute"""
		if min(preformances) > 0:
			#if no hits win this turn aim to hit to the corner opposite the opponent
			ys = list(zip(*results))[1]
			best = max([max(ys), min(ys)], key=lambda y: abs(140-y))
			return possible[ys.index(best)]
		else:
			print("Winning with", min(preformances))
			#If a hit wins return the one that wins by the most
			best = possible[preformances.index(min(preformances))]
			return best

	def compute(self):
		"""Spawn a process and get the results"""
		start = timer()
		v = (self.ball[0]-self.ball_prev[0], self.ball[1]-self.ball_prev[1])
		enemy = self.enemy[1]
		hit = predict(self.ball, self.ball_prev)

		lower = int(max(hit[1]-35, 35))
		upper = int(min(hit[1]+35, 245))

		#The possible positions to intercept the ball at
		possible = [*range(lower, upper)]
		with mp.Pool(mp.cpu_count()) as pool:
			times.append(timer()-start)
			pool_results = pool.map(partial(preformance, hit=hit, v=v, enemy=enemy), possible)
		print(times[-1]/1000000)
		return list(zip(*pool_results))


	def y_to_move(self, desired_y):
		"""Take a y and return the desired movement command"""
		if desired_y > self.pos[1]:
			return "down"
		elif desired_y < self.pos[1]:
			return "up"
		else:
			return desired_y


	def tracking(self, frect, enemy, ball, table_size, *args):
		"""Update the understanding of the board given new information"""

		#Add half the size to each position to compensate for the frect class tracking position from the corner
		self.pos = (int(frect.pos[0]+35), int(frect.pos[1]+35))
		self.enemy = (int(enemy.pos[0]+35), int(enemy.pos[1]+35))
		self.ball = (ball.pos[0]+7.5, ball.pos[1]+7.5)

		if not hasattr(self, "tick"):
			self.tick = 0
			self.side = self.pos[0] <= 220
		else:
			self.tick += 1
			self.ball_dir = math.atan2(self.ball[1]-self.ball_prev[1], self.ball[0]-self.ball_prev[0])

	def store_tick(self):
		"""Store the old information"""
		self.pos_prev = self.pos
		self.enemy_prev = self.enemy
		self.ball_prev = self.ball
		if self.tick > 1:
			self.ball_dir_prev = self.ball_dir

	def __del__(self):
		print("Max time: {},   Avg time: {}".format(max(times)/1000000, sum(times)/len(times)/1000000))



if __name__ == '__main__':
	predict((0, 0), (100, 100))