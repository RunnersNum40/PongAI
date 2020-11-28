import neat
import pong_gym
import numpy as np
import os
import multiprocessing

def fit(genome, config):
    env = pong_gym.Pong("training.ini")
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    agent = neat.nn.FeedForwardNetwork.create(genome, config)
    fitness = 0

    state = env.reset()
    for x in range(10000):
        action = agent.activate(state)
        action = max(range(3), key=lambda n: action[n])

        state, reward, done, _ = env.step(action)
        # print(state)
        if done:
            break
        fitness += reward

    return fitness/(max(env.game.score)*env.score_reward)


def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    # p = neat.Population(config)
    p = neat.Checkpointer.restore_checkpoint("save/neatwork-689")

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    p.add_reporter(neat.Checkpointer(generation_interval=10, filename_prefix="save/neatwork-"))

    # Run for up to 300 generations.
    pe = neat.ParallelEvaluator(multiprocessing.cpu_count(), fit)
    winner = p.run(pe.evaluate, 300)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # # Show output of the most fit genome against training data.
    # print('\nOutput:')
    # winner_net = neat.nn.FeedForwardNetwork.create(winner, config)

    # env = pong_gym.Pong("game.ini")
    # state = env.reset()
    # for x in range(10000):
    #     action = winner_net.activate(state)
    #     action = max(range(3), key=lambda n: action[n])

    #     state, reward, done, _ = env.step(action)
    #     # print(state)
    #     if done:
    #         break
    #     genome.fitness += reward


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config')
    run(config_path)