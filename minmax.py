import numpy as np
import math

def angle(dy, angle):
	"""Find the new angle of a ball given the relative distance of the ball and paddle"""
	if 1.5708/2<angle<=4.7124:
		s = -1
	else:
		s = 1

	theta = s*dy*0.011219974

	v = [math.cos(angle), math.sin(angle)]
	v = [math.cos(theta)*v[0]-math.sin(theta)*v[1],
		 math.sin(theta)*v[0]+math.cos(theta)*v[1]]
	v[0] = -v[0]
	v = [math.cos(-theta)*v[0]-math.sin(-theta)*v[1],
		  math.cos(-theta)*v[1]+math.sin(-theta)*v[0]]

	return math.atan2(v[1], v[0])

class State:
	"""Object represntation of the game state"""
	def __init__(self, paddle1, paddle2, ball, reduced_table=((27.5, 412.5), (7.5, 272.5))):
		self.paddle1 = paddle1
		self.paddle2 = paddle2
		self.ball = Ball(*ball, reduced_table)
		self.table = reduced_table

		#0 = scoring on right side, 1 = left side
		if 1.5708/2<self.ball.angle<=4.7124:
			self.side = 1
		else:
			self.side = 0

		self.ticks = int(abs(self.ball.pos[0]-self.table[0][not self.side])/(abs(math.cos(self.ball.angle))*self.ball.speed))

	def is_win(self):
		"""Check if value is high or low enough"""
		return (self.value>0) == (self.side==0)

	def evaluate(self):
		"""Return a static evaluate of the state.
		The result is the number of ticks between when the ball hits the side and when the paddle could arrive at that position.
		The sign of the result depends on the side the ball is traveling towards"""
		if self.side == 1:
			paddle_y = self.paddle2
			dx = self.table[0][1]-self.ball.pos[0]
		else:
			paddle_y = self.paddle1
			dx = self.ball.pos[0]-self.table[0][0]

		dy = max(abs(self.ball.hit[1]-paddle_y)-35, 0)
		return (dy-self.ticks)*(1-2*self.side)

	def children(self):
		if self.side:
			paddle_y = self.paddle1
		else:
			paddle_y = self.paddle2

		lower = max(int(self.ball.hit[1]-30), 35)#, paddle_y-self.ticks*0.9)
		upper = min(int(self.ball.hit[1]+30), 245)#, paddle_y+self.ticks*0.9)

		possible = np.arange(lower, upper)
		angles = np.array([angle(self.ball.hit[1]-p, self.ball.angle) for p in possible])

		if self.side:
			return [State(y, self.paddle2, (self.ball.hit, a, self.ball.speed*1.2), self.table) for y, a in zip(possible, angles)]
		else:
			return [State(self.paddle1, y, (self.ball.hit, a, self.ball.speed*1.2), self.table) for y, a in zip(possible, angles)]

	def __eq__(self, val):
		return self.value == val

	def __gt__(self, val):
		return self.value > val

	def __lt__(self, val):
		return self.value < val

	def __str__(self):
		return "Paddle1: {},   Paddle2: {},   Ball: ({}),   Bounded in: {},   Value:   {}".format(self.paddle1, self.paddle2, self.ball, self.table, self.evaluate())


class Ball:
	def __init__(self, pos, angle, speed, reduced_table):
		self.pos = pos
		self.angle = angle%6.2832
		self.speed = speed
		self.table = reduced_table

		self.hit = self.predict(self.pos, self.angle, self.table)

	@staticmethod
	def predict(pos, angle, table):
		#Between 90 and 270 means headed to the left
		if 1.5708/2<angle<=4.7124:
			x = 27.5
		else:
			x = 412.5

		m = math.tan(angle)
		l = m*x+pos[1]-m*pos[0]-7.5
		p = math.floor(l/265)

		return x, 265*(p%2)+((-1)**p)*(l%265)+7.5

	def __str__(self):
		return "Position: {},   Angle: {},   Speed: {}".format(self.pos, self.angle, self.speed)

#Right is maximizing player, Left is minimizing
def minimax(state, depth, maximizingPlayer=True, alpha=math.inf, beta=-math.inf):
	if depth == 0:
		state.value = state.evaluate()
		return state

	children = state.children()
	if len(children) == 0:
		return minimax(state, depth-1, maximizingPlayer, alpha, beta)

	if maximizingPlayer:
		maxEval = -math.inf
		for child in children:
			child.value = minimax(child, depth-1, alpha, beta, False).value
			maxEval = max(maxEval, child)
			alpha = max(alpha, child.value)
			if beta <= alpha:
				break

		return maxEval

	else:
		minEval = math.inf
		for child in children:
			child.value = minimax(child, depth-1, alpha, beta, True).value
			minEval = min(minEval, child)
			beta = min(beta, child.value)
			if beta <= alpha:
				break

		return minEval

class MinMaxer:
	"""A pong player that minimaxes each move"""
	def __init__(self, depth=2):
		self.depth = depth

	def __call__(self, *args):
		"""Return a move given the board state. Player tries to minimax the outcome with the information it has"""
		self.tracking(*args)

		if self.tick > 0:
			towards_self = (self.ball[0] < self.ball_prev[0]) == self.side
			state = self.to_state()
			if towards_self:
				desired_state = minimax(state, self.depth, not self.side)
			else:
				desired_state = minimax(state, self.depth, self.side)
		else:
			self.store_tick()
			return None

		move = self.state_to_move(desired_state)
		self.store_tick()
		return move

	def state_to_move(self, state):
		"""Take a state and return the desired movement command"""
		#If self is on the left side use the left paddle
		towards_self = (self.ball[0] < self.ball_prev[0]) == self.side
		if towards_self:
			if self.side:
				desired_y = state.paddle1
			else:
				desired_y = state.paddle2
		else:
			# desired_y = state.ball.hit[1]
			desired_y = 140

		if desired_y > self.pos[1]:
			return "down"
		elif desired_y < self.pos[1]:
			return "up"
		else:
			return desired_y

	def to_state(self):
		"""Return a State object representation of the current understanding of the board"""
		if self.pos[0] <= 110:
			paddle1 = self.pos[1]
			paddle2 = self.enemy[1]
		else:
			paddle1 = self.enemy[1]
			paddle2 = self.pos[1]

		ball_change = (self.ball[0]-self.ball_prev[0], self.ball[1]-self.ball_prev[1])
		angle = math.atan2(ball_change[1], ball_change[0])%(2*math.pi)
		speed = math.sqrt(ball_change[0]**2+ball_change[1]**2)

		return State(paddle1, paddle2, (self.ball, angle, speed))

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

	def store_tick(self):
		"""Store the old information"""
		self.pos_prev = self.pos
		self.enemy_prev = self.enemy
		self.ball_prev = self.ball


if __name__ == "__main__":
	# class frect:
	# 	pass
	# player = MinMaxer()
	# one = frect()
	# one.pos = (15, 210)
	# two = frect()
	# two.pos = (425, 105)
	# ball = frect()
	# ball.pos = (212.5, 132.5)
	# print("Go", player(one, two, ball, (440, 280)))
	# ball.pos = (211.5, 132.5)
	# print("Go", player(one, two, ball, (440, 280)))
	# ball.pos = (210.5, 132.5)
	# print("Go", player(one, two, ball, (440, 280)))


	from time import perf_counter_ns as timer
	times = []

	state = State(0, 0, ((220, 140), math.pi/4, 1), ((27.5, 412.5), (7.5, 272.5)))
	for x in range(10):
		# print(state)
		start = timer()
		state = minimax(state, 3, x%2==0)
		times.append(timer()-start)

	print(state)
	print("Avg time: {}ms,   Max time {}ms".format(sum(times)/len(times)/1000000, max(times)/1000000))

	# state = State(71, 165, ((300.1343372201874, 204.29619166034888), 3.0650548976879777, 3.4560000000000075))
	# print(minimax(state, 3, True))
