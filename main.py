from game import init_game
import AIs
import os
import pygame

thisfolder = os.path.dirname(os.path.abspath(__file__))
initfile = os.path.join(thisfolder, 'game.ini')

game = init_game(initfile, 0)
ai = AIs.Player(leaving="predict")

move = "stay"
state = "playing"
ticks = 0
while state != "ended":
	things = game.tick(move)
	if type(things) == type("ended") and things == "ended":
		state = "ended"
		break
	ticks += 1
	move = ai(*things[1:])