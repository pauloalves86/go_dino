import os
import pickle
from functools import partial
from typing import List

from neat import nn, population, statistics
from neat.config import Config

import dino_api


def get_command(net: nn.FeedForwardNetwork, distance: int, size: int, speed: int) -> str:
    value = net.serial_activate([distance, size, speed])[0]
    # print('activation: {:.4f}'.format(value), end='\r')
    if value >= 0.5:
        return 'up'
    return ''


def eval_fitness(genomes: List):
    for g in genomes:
        net = nn.create_feed_forward_phenotype(g)
        g.fitness = dino_api.play_game(partial(get_command, net), 1)


def main():
    local_dir = os.path.dirname(__file__)
    config = Config(os.path.join(local_dir, 'train_config.txt'))
    config.save_best = True
    pop = population.Population(config)
    pop.run(eval_fitness, 100)

    # Log statistics.
    statistics.save_stats(pop.statistics)
    statistics.save_species_count(pop.statistics)
    statistics.save_species_fitness(pop.statistics)

    print('Number of evaluations: {0}'.format(pop.total_evaluations))

    # Show output of the most fit genome against training data.
    winner = pop.statistics.best_genome()
    with open('winner_genome.pkl', 'wb') as f:
        pickle.dump(winner, f)
    print('\nBest genome:\n{!s}'.format(winner))
    print('\nOutput:')
    winner_net = nn.create_feed_forward_phenotype(winner)
    print('Score:', dino_api.play_game(partial(get_command, winner_net)))


if __name__ == '__main__':
    main()
