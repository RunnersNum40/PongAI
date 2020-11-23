from random import choice, randint
from math import floor, sqrt, atan

def directions_from_input(paddle_rect, other_paddle_rect, ball_rect, table_size):
	keys = pygame.key.get_pressed()

	if keys[pygame.K_UP]:
		return "up"
	elif keys[pygame.K_DOWN]:
		return "down"
	else:
		return None


def angle():
	pass



class Player:
	names = ["Josh", "Bill", "Lucy", "Erwyn", "Stadler", "Matilda", "Emily", "Ted", "Collins", "Christine", "Evan", "Charlie", "Nick", "Maria"]

	def __init__(self, *args, **kwargs):
		self.ball_size = (15, 15)
		self.max_angle = 45

		self.paddle_speed = 1
		self.ball_speeds = []
		self.tick = 0

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
		return ball[1]
	def avg(self, ball):
		return (self.y+ball[1])/2

	def predict_y(self, old, new, table_size):
		if old[0]-new[0] == 0:
			return self.y

		m = (old[1]-new[1])/(old[0]-new[0])
		l = m*[min(self.x, table_size[0]-self.x), max(self.x, table_size[0]-self.x)][new[0]-old[0] > 0]+(new[1]-m*new[0])
		p = floor(l/table_size[1])
		return table_size[1]*(p%2)+((-1)**p)*(l%table_size[1])

	def movement(self, desired):
		"""Takes a predicted position for the ball and returns the correct movement in order to hit it"""
		desired = desired-self.size[1]/2 #adjusts for the paddle size
		
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

	def __call__(self, frect, enemy, ball, table_size, *args):
		if not hasattr(self, "table_size") and self.debug:
			print(self.name, frect.pos)

		self.table_size = table_size
		self.size = frect.size
		self.pos = frect.pos

		ball.pos = [i+j/2 for i, j in zip(ball.pos, ball.size)]
		self.ball = ball.pos


		if not hasattr(self, "ball_prev"):
			#senario when the function is first called, this only happens for one tick so the behavior is not to important
			self.ball_prev = ball.pos
			return self.movement(ball.pos[1])

		towards_self = (ball.pos[0]-self.ball_prev[0] > 0) == (self.x > self.table_size[0]/2)
		predicted = self.predict_y(self.ball_prev, ball.pos, self.table_size)
		if self.debug: print(self.name, "Predicted", predicted, ["Leaving", "Approaching"][towards_self])


		if self.tick == 1:
			self.paddle_speed = self.speed_of(self.self_prev, self.pos)
			self.ball_speeds.append(round(self.speed_of(self.ball_prev, self.ball), 4))
		elif self.tick > 0:
			self.tracking()




		if towards_self:
			desired_y = predicted

		else:
			if self.leaving == "middle":
				desired_y = self.middle()
			elif self.leaving == "track":
				desired_y = self.track(predicted)
			elif self.leaving == "avg":
				desired_y = self.avg(predicted)

		self.ball_prev = ball.pos
		self.self_prev = self.pos

		self.tick += 1

		return self.movement(desired_y)

pong_ai = Player(default="middle")

def chaser(paddle_frect, other_paddle_frect, ball_frect, table_size):
	if paddle_frect.pos[1]+paddle_frect.size[1]/2 < ball_frect.pos[1]+ball_frect.size[1]/2:
		return "down"
	else:
		return "up"

if __name__ == '__main__':
	import timeit
	positions = [(randint(1, 440), randint(1, 220)) for x in range(1000)]
	pairs = [(choice(positions), choice(positions)) for x in range(1100)]
	pairs = [pair for pair in pairs if pair[0][0] != pair[1][0]]
	num = 10000
	print(0.0001/sum(timeit.repeat("Player.predict_y(*choice(pairs), (440, 220))", number=num, repeat=10, setup="from __main__ import Player, pairs\nfrom random import choice"))*(10*num))