import dino_api


def main():
    dino_api.play_game(lambda distance, size, speed: 'up' if distance < 95 else '', verbose=1)


if __name__ == '__main__':
    main()
