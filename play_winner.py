import os
import pickle

import neat
from neat import nn
from neat.config import Config

import dino_api


class GetCommand(object):
    def __init__(self, net: nn.FeedForwardNetwork):
        self.net = net

    def __call__(self, distance: int, size: int, speed: int) -> str:
        value = self.net.activate([distance, size, speed])[0]
        if value >= 0.5:
            return 'up'
        return ''


def main():
    local_dir = os.path.dirname(__file__)
    config = Config(neat.DefaultGenome, neat.DefaultReproduction,
                    neat.DefaultSpeciesSet, neat.DefaultStagnation,
                    os.path.join(local_dir, 'train_config.txt'))
    with open('winner.pkl', 'rb') as f:
        winner = pickle.load(f)
    print('\nBest genome:\n{!s}'.format(winner))
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    print('Score:', dino_api.play_game(GetCommand(winner_net)))


if __name__ == '__main__':
    main()
