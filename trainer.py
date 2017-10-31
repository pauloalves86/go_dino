import os
import pickle
from functools import partial
from typing import List

import neat
from neat import nn, population, statistics
from neat.config import Config

import dino_api


def get_command(net: nn.FeedForwardNetwork, distance: int, size: int, speed: int) -> str:
    value = net.activate([distance, size, speed])[0]
    # print('activation: {:.4f}'.format(value), end='\r')
    if value >= 0.5:
        return 'up'
    return ''


def eval_fitness(genomes: List, config):
    for i, g in genomes:
        net = nn.FeedForwardNetwork.create(g, config)
        g.fitness = dino_api.play_game(partial(get_command, net))


def main():
    local_dir = os.path.dirname(__file__)
    config = Config(neat.DefaultGenome, neat.DefaultReproduction,
                    neat.DefaultSpeciesSet, neat.DefaultStagnation,
                    os.path.join(local_dir, 'train_config.txt'))
    config.save_best = True
    config.checkpoint_time_interval = 3

    initial_pop = []
    # initial_pop = [138, 74, 40, 84, 97, 133, 127, 60, 102, 70, 0, 1, 2]
    for root, dirs, files in os.walk('best'):
        for file_name in files:
            with open(os.path.join('best', file_name), 'rb') as f:
                initial_pop.append(pickle.load(f))
    if not initial_pop:
        initial_pop = None

    pop = population.Population(config, initial_pop)
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.Checkpointer(5))
    pop.run(eval_fitness, 100)

    # Log statistics.
    # statistics.save_stats(pop.statistics)
    # statistics.save_species_count(pop.statistics)
    # statistics.save_species_fitness(pop.statistics)

    # print('Number of evaluations: {0}'.format(pop.total_evaluations))

    # Show output of the most fit genome against training data.
    # with open('best/best_genome_70', 'rb') as f:
    #     winner = pickle.load(f)
    # winner = pop.statistics.best_genome()
    # with open('winner_genome.pkl', 'wb') as f:
    #     pickle.dump(winner, f)
    # print('\nBest genome:\n{!s}'.format(winner))
    # print('\nOutput:')
    # winner_net = nn.create_feed_forward_phenotype(winner)
    # print('Score:', dino_api.play_game(partial(get_command, winner_net)))


if __name__ == '__main__':
    main()
