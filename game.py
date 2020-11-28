import pygame, sys, time, random, os
from pygame.locals import *
import math
import configparser


white = [255, 255, 255]
black = [0, 0, 0]
clock = pygame.time.Clock()

class fRect:
	'''
	pygame's Rect class can only be used to represent whole integer vertices, so we create a rectangle class that can have floating point coordinates
	'''
	def __init__(self, pos, size):
		self.pos = (pos[0], pos[1])
		self.size = (size[0], size[1])
	def move(self, x, y):
		return fRect((self.pos[0]+x, self.pos[1]+y), self.size)

	def move_ip(self, x, y, move_factor = 1):
		self.pos = (self.pos[0] + x*move_factor, self.pos[1] + y*move_factor)

	def get_rect(self):
		return Rect(self.pos, self.size)

	def copy(self):
		return fRect(self.pos, self.size)

	def intersect(self, other_frect):
		# two rectangles intersect iff both x and y projections intersect
		for i in range(2):
			if self.pos[i] < other_frect.pos[i]: # projection of self begins to the left
				if other_frect.pos[i] >= self.pos[i] + self.size[i]:
					return 0
			elif self.pos[i] > other_frect.pos[i]:
				if self.pos[i] >= other_frect.pos[i] + other_frect.size[i]:
					return 0
		return 1#self.size > 0 and other_frect.size > 0

	def __str__(self):
		return "fRect\nPos: {},   Size: {}".format(self.pos, self.size)

class Paddle:
	def __init__(self, pos, size, speed, max_angle, facing, timeout):
		self.frect = fRect((pos[0]-size[0]/2, pos[1]-size[1]/2), size)
		self.speed = speed
		self.size = size
		self.facing = facing
		self.max_angle = max_angle
		self.timeout = timeout

	def factor_accelerate(self, factor):
		self.speed = factor*self.speed

	def move(self, table_size, direction):
		# direction = self.move_getter(self.frect.copy(), enemy_frect.copy(), ball_frect.copy(), tuple(table_size))
		#direction = timeout(self.move_getter, (self.frect.copy(), enemy_frect.copy(), ball_frect.copy(), tuple(table_size)), {}, self.timeout)
		if direction == "up":
			self.frect.move_ip(0, -self.speed)
		elif direction == "down":
			self.frect.move_ip(0, self.speed)

		to_bottom = (self.frect.pos[1]+self.frect.size[1])-table_size[1]

		if to_bottom > 0:
			self.frect.move_ip(0, -to_bottom)
		to_top = self.frect.pos[1]
		if to_top < 0:
			self.frect.move_ip(0, -to_top)


	def get_face_pts(self):
		return ((self.frect.pos[0] + self.frect.size[0]*self.facing, self.frect.pos[1]),
				(self.frect.pos[0] + self.frect.size[0]*self.facing, self.frect.pos[1] + self.frect.size[1]-1)
				)

	def get_angle(self, y):
		center = self.frect.pos[1]+self.size[1]/2
		rel_dist_from_c = ((y-center)/self.size[1])
		rel_dist_from_c = min(0.5, rel_dist_from_c)
		rel_dist_from_c = max(-0.5, rel_dist_from_c)
		sign = 1-2*self.facing

		return sign*rel_dist_from_c*self.max_angle*math.pi/180

class Ball:
	def __init__(self, table_size, size, paddle_bounce, wall_bounce, dust_error, init_speed_mag):
		rand_ang = (.4+.4*random.random())*math.pi*(1-2*(random.random()>.5))+.5*math.pi
		#rand_ang = -110*math.pi/180
		speed = (init_speed_mag*math.cos(rand_ang), init_speed_mag*math.sin(rand_ang))
		pos = (table_size[0]/2, table_size[1]/2)
		#pos = (table_size[0]/2 - 181, table_size[1]/2 - 105)
		self.frect = fRect((pos[0]-size[0]/2, pos[1]-size[1]/2), size)
		self.speed = speed
		self.size = size
		self.paddle_bounce = paddle_bounce
		self.wall_bounce = wall_bounce
		self.dust_error = dust_error
		self.init_speed_mag = init_speed_mag
		self.prev_bounce = None

	def get_center(self):
		return (self.frect.pos[0] + .5*self.frect.size[0], self.frect.pos[1] + .5*self.frect.size[1])


	def get_speed_mag(self):
		return math.sqrt(self.speed[0]**2+self.speed[1]**2)

	def factor_accelerate(self, factor):
		self.speed = (factor*self.speed[0], factor*self.speed[1])



	def move(self, paddles, table_size, move_factor):
		moved = 0
		walls_Rects = [Rect((-100, -100), (table_size[0]+200, 100)),
					   Rect((-100, table_size[1]), (table_size[0]+200, 100))]

		for wall_rect in walls_Rects:
			if self.frect.get_rect().colliderect(wall_rect):
				c = 0
				#print "in wall. speed: ", self.speed
				while self.frect.get_rect().colliderect(wall_rect):
					self.frect.move_ip(-.1*self.speed[0], -.1*self.speed[1], move_factor)
					c += 1 # this basically tells us how far the ball has traveled into the wall
				r1 = 1+2*(random.random()-.5)*self.dust_error
				r2 = 1+2*(random.random()-.5)*self.dust_error

				self.speed = (self.wall_bounce*self.speed[0]*r1, -self.wall_bounce*self.speed[1]*r2)
				while c > 0 or self.frect.get_rect().colliderect(wall_rect):
					self.frect.move_ip(.1*self.speed[0], .1*self.speed[1], move_factor)
					c -= 1 # move by roughly the same amount as the ball had traveled into the wall
				moved = 1
				#print "out of wall, position, speed: ", self.frect.pos, self.speed

		self.bounced = False
		for paddle in paddles:
			if self.frect.intersect(paddle.frect):
				self.bounced = True
				if (paddle.facing == 1 and self.get_center()[0] < paddle.frect.pos[0] + paddle.frect.size[0]/2) or \
				(paddle.facing == 0 and self.get_center()[0] > paddle.frect.pos[0] + paddle.frect.size[0]/2):
					continue
				
				c = 0
				
				while self.frect.intersect(paddle.frect) and not self.frect.get_rect().colliderect(walls_Rects[0]) and not self.frect.get_rect().colliderect(walls_Rects[1]):
					self.frect.move_ip(-.1*self.speed[0], -.1*self.speed[1], move_factor)
					
					c += 1
				theta = paddle.get_angle(self.frect.pos[1]+.5*self.frect.size[1])
				

				v = self.speed

				v = [math.cos(theta)*v[0]-math.sin(theta)*v[1],
							 math.sin(theta)*v[0]+math.cos(theta)*v[1]]

				v[0] = -v[0]

				v = [math.cos(-theta)*v[0]-math.sin(-theta)*v[1],
							  math.cos(-theta)*v[1]+math.sin(-theta)*v[0]]


				# Bona fide hack: enforce a lower bound on horizontal speed and disallow back reflection
				if  v[0]*(2*paddle.facing-1) < 1: # ball is not traveling (a) away from paddle (b) at a sufficient speed
					v[1] = (v[1]/abs(v[1]))*math.sqrt(v[0]**2 + v[1]**2 - 1) # transform y velocity so as to maintain the speed
					v[0] = (2*paddle.facing-1) # note that minimal horiz speed will be lower than we're used to, where it was 0.95 prior to increase by *1.2

				#a bit hacky, prevent multiple bounces from accelerating
				#the ball too much
				if not paddle is self.prev_bounce:
					self.speed = (v[0]*self.paddle_bounce, v[1]*self.paddle_bounce)
				else:
					self.speed = (v[0], v[1])
				self.prev_bounce = paddle
				#print "transformed speed: ", self.speed

				while c > 0 or self.frect.intersect(paddle.frect):
					#print "move_ip()"
					self.frect.move_ip(.1*self.speed[0], .1*self.speed[1], move_factor)
					#print "ball position forward trace: ", self.frect.pos
					c -= 1
				#print "pos final: (" + str(self.frect.pos[0]) + "," + str(self.frect.pos[1]) + ")"
				#print "speed x y: ", self.speed[0], self.speed[1]

				moved = 1
				#print "out of paddle, speed: ", self.speed

		# if we didn't take care of not driving the ball into a wall by backtracing above it could have happened that
		# we would end up inside the wall here due to the way we do paddle bounces
		# this happens because we backtrace (c++) using incoming velocity, but correct post-factum (c--) using new velocity
		# the velocity would then be transformed by a wall hit, and the ball would end up on the dark side of the wall

		if not moved:
			self.frect.move_ip(self.speed[0], self.speed[1], move_factor)
			#print "moving "
		#print "poition: ", self.frect.pos

def render(screen, paddles, ball, score, table_size):
	screen.fill(black)

	pygame.draw.rect(screen, paddles[0].color, paddles[0].frect.get_rect())
	pygame.draw.rect(screen, paddles[1].color, paddles[1].frect.get_rect())

	pygame.draw.circle(screen, white, (int(ball.get_center()[0]), int(ball.get_center()[1])),  int(ball.frect.size[0]/2), 0)


	pygame.draw.line(screen, white, [screen.get_width()/2, 0], [screen.get_width()/2, screen.get_height()])

	score_font = pygame.font.Font(None, 32)
	screen.blit(score_font.render(str(score[0]), True, white), [int(0.4*table_size[0])-8, 0])
	screen.blit(score_font.render(str(score[1]), True, white), [int(0.6*table_size[0])-8, 0])

	pygame.display.flip()

def check_point(score, ball, table_size):
	if ball.frect.pos[0]+ball.size[0]/2 < 0:
		score[1] += 1
		ball = Ball(table_size, ball.size, ball.paddle_bounce, ball.wall_bounce, ball.dust_error, ball.init_speed_mag)
		return (ball, score)
	elif ball.frect.pos[0]+ball.size[0]/2 >= table_size[0]:
		ball = Ball(table_size, ball.size, ball.paddle_bounce, ball.wall_bounce, ball.dust_error, ball.init_speed_mag)
		score[0] += 1
		return (ball, score)

	return (ball, score)

def init_game(file_name, side):
	config = configparser.ConfigParser()
	config.read(file_name)
	config = config["game-states"]

	table_size = tuple(map(int, config["table_size"].strip(" ").strip("(").strip(")").split(",")))
	paddle_size = tuple(map(int, config["paddle_size"].strip(" ").strip("(").strip(")").split(",")))
	ball_size = tuple(map(int, config["ball_size"].strip(" ").strip("(").strip(")").split(",")))
	paddle_speed = config.getfloat("paddle_speed")
	max_angle = config.getfloat("max_angle")

	paddle_bounce = config.getfloat("paddle_bounce")
	wall_bounce = config.getfloat("wall_bounce")
	dust_error = config.getfloat("dust_error")
	init_speed_mag = config.getfloat("init_speed_mag")
	timeout = config.getfloat("timeout")
	clock_rate = config.getfloat("clock_rate")
	turn_wait_rate = config.getfloat("turn_wait_rate")
	score_to_win = config.getint("score_to_win")

	display = config.getboolean("display")
	status = config.getboolean("status")

	screen = None
	if display:
		pygame.init()
		screen = pygame.display.set_mode(table_size)
		pygame.display.set_caption('PongAIvAI')

	paddles = [Paddle((20, table_size[1]/2), paddle_size, paddle_speed, max_angle,  1, timeout),
			   Paddle((table_size[0]-20, table_size[1]/2), paddle_size, paddle_speed, max_angle, 0, timeout)]
	ball = Ball(table_size, ball_size, paddle_bounce, wall_bounce, dust_error, init_speed_mag)

	paddles[side].color = (255, 0, 0)
	paddles[1-side].color = (255, 255, 255)

	import AIs
	return Game(screen, paddles, ball, table_size, clock_rate, turn_wait_rate, score_to_win, display, status, getattr(AIs, config["ai"]), side)


class Game:
	def __init__(self, screen, paddles, ball, table_size, clock_rate, turn_wait_rate, score_to_win, display, status, ai, side):
		self.screen = screen
		self.paddles = paddles
		self.ball = ball
		self.table_size = table_size
		self.clock_rate = clock_rate
		self.turn_wait_rate = turn_wait_rate
		self.score_to_win = score_to_win
		self.display = display
		self.status = status
		self.score = [0, 0]
		self.ai = ai
		self.side = side

	def tick(self, move):
		if max(self.score) >= self.score_to_win:
			return self.end()

		self.old_score = self.score[:]
		self.ball, self.score = check_point(self.score, self.ball, self.table_size)
		try:
			self.paddles[self.side].move(tuple(self.table_size), move)
		except:
			pass
		try:
			self.paddles[1-self.side].move(tuple(self.table_size), self.ai(self.paddles[1-self.side].frect.copy(), self.paddles[self.side].frect.copy(), self.ball.frect.copy(), tuple(self.table_size)))
		except:
			pass

		inv_move_factor = int((self.ball.speed[0]**2+self.ball.speed[1]**2)**.5)
		if inv_move_factor > 0:
			for i in range(inv_move_factor):
				self.ball.move(self.paddles, self.table_size, 1./inv_move_factor)
		else:
			self.ball.move(self.paddles, self.table_size, 1)

		if self.display:
			if self.score != self.old_score:
				font = pygame.font.Font(None, 32)
				if self.score[self.side] != self.old_score[self.side]:
					self.screen.blit(font.render("AI scores!", True, white, black), [0, 32])
				else:
					self.screen.blit(font.render("Chaser scores!", True, white, black), [int(self.table_size[0]/2+20), 32])


				pygame.display.flip()
				if self.display: clock.tick(self.turn_wait_rate)

			render(self.screen, self.paddles, self.ball, self.score, self.table_size)

			pygame.event.pump()
			keys = pygame.key.get_pressed()
			if keys[K_q]:
				return 

		elif self.status:
			if self.score != self.old_score:
				if self.score[self.side] != self.old_score[self.side]:
					print("AI scores!", self.score)
				else:
					print("Chaser scores!", self.score)

		if self.display: clock.tick(self.clock_rate)

		return "playing", self.paddles[self.side].frect.copy(), self.paddles[1-self.side].frect.copy(), self.ball.frect.copy(), tuple(self.table_size)

	def end(self):
		if self.display: 
			font = pygame.font.Font(None, 64)
			if self.score[0] > self. score[1]:
				self.screen.blit(font.render("AI wins!", True, white, black), [24, 32])
			else:
				self.screen.blit(font.render("Chaser wins!", True, white, black), [24, 32])
			pygame.display.flip()
			clock.tick(2)

			pygame.event.pump()
			while any(pygame.key.get_pressed()):
				pygame.event.pump()
				if self.display: clock.tick(30)

		if self.status: print(self.score)
		return "ended"

	def __del__(self):
		pygame.quit()


if __name__ == '__main__':
	init_game()
