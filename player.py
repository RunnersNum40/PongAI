import math
from time import perf_counter_ns as timer
import time
import threading
from functools import partial

times = []
v = (0, 0)
enemy = 140
hit = (412.5, 140)
leaving = True

class Pipeline:
	"""
	Class to allow a single element pipeline between producer and consumer.
	"""
	def __init__(self):
		self.message = 0
		self.used = True

	def get_message(self):
		self.used = True
		message = self.message
		return message

	def set_message(self, message):
		self.used = False
		self.message = message


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
	#Between 90 and 270 means headed to the left
	if pos[0] < old_pos[0]:
		x = 27.5
	elif pos[0] > old_pos[0]:
		x = 412.5
	else:
		# raise Exception("Ball not moving sideways from: {} to {}".format(*map(tuple, [old_pos, pos])))
		return pos

	m = (pos[1]-old_pos[1])/(pos[0]-old_pos[0])
	l = m*x+pos[1]-m*pos[0]-7.5
	p = math.floor(l/265)
	return x, 265*(p%2)+((-1)**p)*(l%265)+7.5


def consumer(pipeline):
	global v
	global enemy
	global hit
	global own_y
	global leaving
	while True:
		time.sleep(0.001)
		if not leaving:
			pass
			try:
				lower = int(max(hit[1]-35, 35))
				upper = int(min(hit[1]+35, 245))
				#The possible positions to intercept the ball at
				possible = [*range(lower, upper)]
				new_velos = [angle(hit[1]-p, v) for p in possible]
				results = [predict((hit[0]+new[0], hit[1]+new[1]), hit) for new in new_velos]
				preformances = [(abs(enemy-result[1]))-(385/abs(result[0])) for result in results]
				if min(preformances) > 0:
					#if no hits win this turn aim to hit to the corner opposite the opponent
					ys = list(zip(*results))[1]
					best = possible[ys.index(max([max(ys), min(ys)], key=lambda y: abs(140-y)))]
				else:
					#If a hit wins return the one that wins by the most
					best = possible[preformances.index(min(preformances))]
				pipeline.set_message(max(min(best, hit[1]+35), hit[1]-35))
			except:
				print("Encountered error, moving on")
		else:
			possible = [*range(enemy-10, enemy+10)]
			new_velos = [angle(hit[1]-p, v) for p in possible]
			results = [predict((hit[0]+new[0], hit[1]+new[1]), hit) for new in new_velos]
			avg = sum(r[1] for r in results)/len(results)
			pipeline.set_message(avg)

class Player:
	def __init__(self):
		self.pipeline = Pipeline()
		self.calculator = threading.Thread(target=consumer, args=(self.pipeline,))
		self.calculator.daemon = True
		self.calculator.start()

	def __call__(self, *args):
		"""Return a move given the board state. Player tries to maximize how far the ball lands from where the opponent can move"""
		start = timer()
		global leaving
		self.tracking(*args)

		if self.tick > 0:
			towards_self = (self.ball[0] < self.ball_prev[0]) == self.side
			leaving = not towards_self
			desired_y = self.best_y()
		else:
			self.store_tick()
			return None

		self.move = self.y_to_move(desired_y)
		self.store_tick()
		times.append((timer()-start)/803030)
		return self.move

	def best_y(self):
		global v
		v = (self.ball[0]-self.ball_prev[0], self.ball[1]-self.ball_prev[1])
		global enemy
		enemy = self.enemy[1]
		global hit
		hit = predict(self.ball, self.ball_prev)

		return self.pipeline.get_message()

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
		print("Max time: {},   Avg time: {}".format(max(times), sum(times)/len(times)))

if __name__ == '__main__':
	predict((0, 0), (100, 100))
else:
	pong_ai = Player()