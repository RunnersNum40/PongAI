from game import init_game
import AIs
import os
import pygame

ai = AIs.Player(debug=False, leaving="middle")


thisfolder = os.path.dirname(os.path.abspath(__file__))
initfile = os.path.join(thisfolder, 'game.ini')
game = init_game(initfile)

move = "stay"
state = "playing"
while state != "ended":
	# try:
	# 	print(ai.predict_y(ai.ball_prev, ai.ball, ai.table_size))
	# 	pygame.draw.circle(game.screen, [0, 255, 0], list(map(int, ai.predict_x(ai.ball_prev, ai.ball, ai.table_size))), 5, 0)
	# 	pygame.event.pump()
	# except:
	# 	pass
	things = game.tick(move)
	if type(things) == type("ended") and things == "ended":
		state = "ended"
		break

	move = ai(*things[1:])