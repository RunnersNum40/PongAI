def directions_from_input(paddle_rect, other_paddle_rect, ball_rect, table_size):
	keys = pygame.key.get_pressed()

	if keys[pygame.K_UP]:
		return "up"
	elif keys[pygame.K_DOWN]:
		return "down"
	else:
		return None



from random import choice


class Player:
	names = ["Josh", "Bill", "Lucy", "Erwyn", "Stadler", "Matilda", "Emily", "Ted", "Collins", "Christine", "Evan", "Charlie", "Nick", "Maria"]

	def __init__(self, *args, **kwargs):
		self.ball_size = (15, 15)
		self.paddle_speed = 1
		self.max_angle = 45

		self.paddle_bounce = 1.2
		self.wall_bounce = 1.00
		self.dust_error = 0.00
		self.init_speed_mag = 2
		self.timeout = 0.0003
		self.clock_rate = 80
		self.turn_wait_rate = 3
		self.score_to_win = 50


		self.debug = False
		self.verbose = False
		self.name = choice(Player.names)
		self.leaving = "middle"
		self.pos = [0, 0]
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
		return [self.x, self.table_size[1]/2]
	def track(self, ball):
		return [self.x, ball[1]]
	def avg(self, ball):
		return [self.x, (self.y+ball[1])/2]

	def predict(self, old, new):
		if self.debug: print(self.name, "Predicting, ", old, new)
		if old[0] == new[0]:
			return self.middle()

		if (new[0]-old[0] > 0) == (self.x > self.table_size[0]/2):
			if self.debug: print(self.name, "Approaching")
			vdir = (old[1]-new[1])/(old[0]-new[0])

			if old[1]-new[1] == 0:
				return [self.x, new[1]]
			elif old[1]-new[1] > 0:
				target_y = 0
			else:
				target_y = 1

			x, y = new

			while new[0] != self.x:
				dy = [0.0, float(self.table_size[1])][target_y]-y
				dx = dy/vdir

				if (new[0]-old[0] > 0) == (dx+x > self.x):
					return [self.x, y+(self.x-x)*vdir]

				x, y = x+dx, [0.0, float(self.table_size[1])][target_y]
				target_y = 1-target_y
				vdir *= -1

			return [self.x, new[1]]

		else:
			if self.debug: print(self.name, "Leaving")
			if self.leaving == "middle":
				postion = self.middle()
			elif self.leaving == "track":
				postion = self.track(new)
			elif self.leaving == "avg":
				postion = self.avg(new)
			return postion

	def movement(self, predicted):
		"""Takes a predicted position for the ball and returns the correct movement in order to hit it"""
		predicted = [predicted[0], predicted[1]-self.size[1]/2] #adjusts for the paddle size
		
		if predicted[1] < self.y:
			return "up"
		elif predicted[1] > self.y:
			return "down"
		else:
			return "stay"


	def __call__(self, frect, enemy, ball, table_size, *args):
		if not hasattr(self, "table_size") and self.debug:
			print(self.name, frect.pos)
		self.table_size = table_size
		self.size = frect.size
		self.pos = frect.pos

		ball.pos = [i+j/2 for i, j in zip(ball.pos, ball.size)]

		if not hasattr(self, "ball_prev"):
			#senario when the function is first called, this only happens for one tick so the behavior is not to important
			self.ball_prev = ball.pos
			return self.movement(ball.pos)

		else:
			predicted = self.predict(self.ball_prev, ball.pos)
			if self.debug: print(self.name, "Predicted", predicted)
			self.ball_prev = ball.pos
			return self.movement(predicted)

pong_ai = Player(default="avg")

def chaser(paddle_frect, other_paddle_frect, ball_frect, table_size):
	if paddle_frect.pos[1]+paddle_frect.size[1]/2 < ball_frect.pos[1]+ball_frect.size[1]/2:
		return "down"
	else:
		return "up"