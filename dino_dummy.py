from functools import partial

from asciimatics.screen import Screen

from dino_api import Board


def main(screen):
    board = Board()
    board.play_game(partial(dummy_play, screen))


def dummy_play(screen, distance: int, size: int, speed: int) -> str:
    action = 'up' if distance - speed < 102 else ''
    screen.print_at('Distance: {:3d}'.format(distance), 0, 0, bg=1 if action else 0)
    screen.print_at('Size:     {:3d}'.format(size), 0, 1)
    screen.print_at('Speed:    {:3d}'.format(speed), 0, 2)
    screen.refresh()
    return action


if __name__ == '__main__':
    Screen.wrapper(main)
