import os
import pickle
from typing import List

import neat
from neat import nn, population
from neat.config import Config

from dino_api import Board


class GetCommand(object):
    def __init__(self, net: nn.FeedForwardNetwork):
        self.net = net

    def __call__(self, distance: int, size: int, speed: int) -> str:
        value = self.net.activate([distance, size, speed])[0]
        if value >= 0.5:
            return 'up'
        return ''


def eval_fitness(genomes: List, config):
    board = Board()
    for i, g in genomes:
        net = nn.FeedForwardNetwork.create(g, config)
        g.fitness = board.play_game(GetCommand(net))


def main():
    local_dir = os.path.dirname(__file__)
    config = Config(neat.DefaultGenome, neat.DefaultReproduction,
                    neat.DefaultSpeciesSet, neat.DefaultStagnation,
                    os.path.join(local_dir, 'train_config.txt'))
    config.save_best = True
    config.checkpoint_time_interval = 3

    pop = population.Population(config)
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.StatisticsReporter())
    pop.add_reporter(neat.Checkpointer(2))
    winner = pop.run(eval_fitness, 100)
    with open('winner.pkl', 'wb') as f:
        pickle.dump(winner, f)


if __name__ == '__main__':
    main()
