from random import choice, randint
from math import floor, sqrt, atan, pi, sin, cos
import pygame
import numpy as np


def directions_from_input(paddle_rect, other_paddle_rect, ball_rect, table_size):
	keys = pygame.key.get_pressed()

	if keys[pygame.K_UP]:
		return "up"
	elif keys[pygame.K_DOWN]:
		return "down"
	else:
		return None


class Defender:
	def predict_y(self, old, new):
		if old[0]-new[0] == 0:
			return self.pos[1]

		m = (old[1]-new[1])/(old[0]-new[0])
		l = m*self.edges[new[0]-old[0] >= 0]+(new[1]-m*new[0])
		p = floor(l/self.table_size[1])
		return self.table_size[1]*(p%2)+((-1)**p)*(l%self.table_size[1])

	def movement(self, desired):
		"""Takes a predicted position for the ball and returns the correct movement in order to hit it"""
		desired = desired-self.size[1]/2 #adjusts for the paddle size
		
		if desired < self.pos[1]:
			return "up"
		elif desired > self.pos[1]:
			return "down"
		else:
			return "stay"

	def __call__(self, frect, enemy, ball, table_size, *args):
		self.table_size = table_size
		self.size = frect.size
		self.pos = frect.pos
		self.enemy = enemy.pos

		self.edges = [min(25, table_size[0]-25), max(25, table_size[0]-25)]

		ball.pos = [i+j/2 for i, j in zip(ball.pos, ball.size)]
		self.ball = ball.pos

		if not hasattr(self, "ball_prev"):
			#senario when the function is first called, this only happens for one tick so the behavior is not to important
			self.ball_prev = ball.pos
			return self.movement(ball.pos[1])

		elif (self.ball[0]-self.ball_prev[0] > 0) == (self.pos[0] > self.table_size[0]/2):
			y = self.predict_y(self.ball_prev, self.ball)

		else:
			y = self.table_size[1]/2

		self.ball_prev = ball.pos

		return self.movement(y)


class Player:
	names = ["Josh", "Bill", "Lucy", "Erwyn", "Stadler", "Matilda", "Emily", "Ted", "Collins", "Christine", "Evan", "Charlie", "Nick", "Maria"]

	def __init__(self, *args, **kwargs):
		self.ball_size = (15, 15)
		self.max_angle = 45

		self.paddle_speed = 1
		self.ball_speeds = []
		self.tick = 0
		self.enemy_dys = [0]

		self.debug = False
		self.verbose = False
		self.name = choice(Player.names)
		self.leaving = "middle"

		self.pos = [0, 0]
		self.table_size = (440, 220)

		self.__dict__.update(kwargs)

	@property
	def x(self):
		return self.pos[0]
	@x.setter
	def x(self):
		self.pos[0] = x
	@property
	def y(self):
		return self.pos[1]
	@y.setter
	def y(self):
		self.pos[1] = y

	def middle(self):
		return self.table_size[1]/2
	def track(self, ball):
		return ball
	def avg(self, ball):
		return (self.y+ball)/2

	def predict_y(self, old, new):
		if old[0]-new[0] == 0:
			return self.y

		dy = self.edges[1][1]-self.edges[1][0]

		m = (old[1]-new[1])/(old[0]-new[0])
		l = m*self.edges[0][new[0]-old[0] >= 0]+(new[1]-m*new[0])-self.edges[1][0]
		p = floor(l/dy)
		y = dy*(p%2)+((-1)**p)*(l%dy)+self.edges[1][0]
		return y

	def movement(self, desired):
		"""Takes a predicted position for the ball and returns the correct movement in order to hit it"""
		if desired < self.y:
			return "up"
		elif desired > self.y:
			return "down"
		else:
			return "stay"

	def speed_of(self, old, new):
		return sqrt(sum((i-j)**2 for i, j in zip(old, new)))

	def tracking(self):
		ball_speed = round(self.speed_of(self.ball_prev, self.ball), 4)
		if ball_speed > self.ball_speeds[-1]:
			self.ball_speeds.append(ball_speed)

	def on_score(self):
		self.ball_speeds = []
		self.tick = 0

	def on_bounce(self):
		self.tracking()
		if abs(self.ball[0]-self.x) > self.table_size[0]/2 and -self.size[1]/2<=self.ball[1]-(self.enemy[1]-self.size[1]/2)<=self.size[1]/2:
			self.enemy_dys.append(self.ball[1]-(self.enemy[1]-37.5))

	def is_point(self):
		if len(self.ball_speeds) < 1:
			return False, None

		x = self.edges[0][self.ball_dir]
		y = self.predict_y(self.ball_prev, self.ball)

		if self.x == x:
			target = "self"
		else:
			target = "enemy"

		dy = {"self":abs(self.y-y), "enemy":abs(self.enemy[1]-y)}[target]

		ball_speed = abs(self.ball[0]-self.ball_prev[0])

		if ball_speed == 0:
			return False, None

		if abs(x-self.ball[0])/ball_speed < dy/self.paddle_speed:
			return True, target
		else:
			return False, None

	def get_angle(self, rel):
		return (1-2*(self.x < self.table_size[0]/2))*max([min([rel/70, 0.5]), -0.5])*pi/2

	def predict_speed(self):
		if len(self.ball_speeds) < 1:
			return 2
		else:
			return self.ball_speeds[-1]*sum(x/y for x, y in zip(self.ball_speeds, self.ball_speeds[1:]))/len(self.ball_speeds-1)

	def update_tracking(self, frect, enemy, ball, table_size, *args):
		self.pos = (int(frect.pos[0]+frect.size[0]/2), int(frect.pos[1]+frect.size[1]/2))
		self.enemy = (int(enemy.pos[0]+enemy.size[0]/2), int(enemy.pos[1]+enemy.size[1]/2))
		self.ball = (ball.pos[0]+ball.size[0]/2, ball.pos[1]+ball.size[1]/2)

		if self.tick == 0:
			self.edges = ((min(self.x+frect.size[0]/2, table_size[0]-self.x-frect.size[0]/2)+frect.size[0]/2+ball.size[0]/2, max(self.x+frect.size[0]/2, table_size[0]-self.x-frect.size[0]/2)-frect.size[0]/2-ball.size[0]/2),
						  (ball.size[1]/2, table_size[1]-ball.size[1]/2))
			self.table_size = table_size
			self.size = frect.size
			self.ball_prev = self.ball
		elif self.tick == 1:
			self.ball_dir = self.ball[0]-self.ball_prev[0] >= 0
			self.paddle_speed = max(self.speed_of(self.self_prev, self.pos), 0.1)
			self.ball_speeds.append(round(self.speed_of(self.ball_prev, self.ball), 4))
		else:
			self.ball_dir = self.ball[0]-self.ball_prev[0] >= 0
			if self.ball_dir != self.ball_dir_prev:
				if abs(self.ball[0]-self.ball_prev[0])>self.table_size[0]/3:
					self.on_score()
				else:
					self.on_bounce()

	def end_tick(self):
		if self.tick > 0: self.ball_dir_prev = self.ball_dir
		self.ball_prev = self.ball
		self.self_prev = self.pos
		self.tick += 1

	def best_y(self):
		safety_factor = 0.1
		checks = 45

		predicted_y = self.predict_y(self.ball_prev, self.ball)
		intercepts = np.linspace(max(predicted_y-self.size[1]/2*(1-safety_factor), 0), min(predicted_y+self.size[1]/2*(1-safety_factor), self.table_size[1]), checks)

		angles = np.array([*map(self.get_angle, predicted_y-intercepts)])
		ball_velo = np.array([n-o for n, o in zip(self.ball, self.ball_prev)])

		#Rotate the ball velocity by each angle in angles
		new_velos = [np.array(((np.cos(theta), -np.sin(theta)), (np.sin(theta), np.cos(theta)))).dot(ball_velo) for theta in angles]
		return_y = [self.predict_y((self.x, predicted_y), np.array((self.x, predicted_y))+velo) for velo in new_velos]
		best = max(range(len(intercepts)), key=lambda i: abs(return_y[i]-self.enemy[1])/self.paddle_speed - self.table_size[0]/new_velos[i][0])

		if abs(return_y[best]-self.enemy[1])/self.paddle_speed > self.table_size[0]/new_velos[best][0]:
			#find the intercept that maximizes hom much longer it takes the enemy to move to the ball from how long it takes the ball to get to their side
			return min(predicted_y+self.size[1]/2, max(predicted_y-self.size[1]/2, intercepts[best]))
		else:
			best = max(range(len(intercepts)), key=lambda i: abs(return_y[i]-self.enemy[1])/self.paddle_speed - self.table_size[0]/new_velos[i][0])
			return predicted_y

	def leaving_behavior(self):
		if self.leaving == "middle":
			desired_y = self.middle()
		elif self.leaving == "track":
			desired_y = self.track(predicted)
		elif self.leaving == "avg":
			desired_y = self.avg(predicted)
		elif self.leaving == "predict":
			predicted_y = self.predict_y(self.ball_prev, self.ball)
			theta = -self.get_angle(predicted_y-self.enemy[1])
			rotation = np.array(((np.cos(theta), -np.sin(theta)), (np.sin(theta), np.cos(theta))))
			ball_velo = np.array([n-o for n, o in zip(self.ball, self.ball_prev)])
			new_velo = rotation.dot(ball_velo)
			desired_y = self.predict_y((self.x, predicted_y), np.array((self.x, predicted_y))+new_velo)

		return desired_y

	def __call__(self, *args):
		if self.tick == 0:
			self.update_tracking(*args)
			self.end_tick()
			return None

		self.update_tracking(*args)
		towards_self = (self.ball[0]-self.ball_prev[0] > 0) == (self.x > self.table_size[0]/2)
		if towards_self:
			desired_y = self.best_y()
		else:
			desired_y = self.leaving_behavior()

		self.end_tick()
		return self.movement(desired_y)

def static(*args):
	return None

def chaser(paddle_frect, other_paddle_frect, ball_frect, table_size):
	return ["up", "down"][paddle_frect.pos[1] < ball_frect.pos[1]]


if __name__ != '__main__':
	pong_ai = Player(leaving="middle")
	defender = Defender()