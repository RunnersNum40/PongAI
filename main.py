from game import init_game
import AIs

ai = AIs.Player(debug=False, leaving="middle")

game = init_game(100)

move = "stay"
state = "playing"
while state != "ended":
	things = game.tick(move)
	if type(things) == type("ended") and things == "ended":
		print(game.score)
		state = "ended"
		break

	move = ai(*things[1:])