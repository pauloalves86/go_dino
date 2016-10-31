import os
import time
from typing import Dict, List, Callable

import cv2
import numpy as np
import pyautogui
from PIL import Image
from mss import mss


def play_game(get_command_callback: Callable[[int, int, int], str], verbose=0) -> int:
    with mss() as screenshotter:
        get_game_landscape_and_set_focus_or_die(screenshotter)
        reset_game()
        landscape = get_game_landscape_and_set_focus_or_die(screenshotter, .95)

        start_game()
        gameover_template = cv2.imread(os.path.join('templates', 'dino_gameover.png'), 0)
        start = time.time()
        last_distance = landscape['width']
        x1, x2, y1, y2 = compute_region_of_interest(landscape)
        speed = 0
        last_compute_speed = time.time()
        last_speeds = [3] * 30
        last_command_time = time.time()

        while True:
            buffer = screenshotter.get_pixels(landscape)
            image = Image.frombytes('RGB', (landscape['width'], landscape['height']), buffer).convert('L')
            image = np.array(image)
            image += np.abs(247 - image[0, x2])
            roi = image[y1:y2, x1:x2]
            score = int(time.time() - start)
            distance, size = compute_distance_and_size(roi, x2)
            speed = compute_speed(distance, last_distance, speed, last_speeds, last_compute_speed)
            last_compute_speed = time.time()
            # Check GAME OVER
            if distance == last_distance or distance == 0:
                res = cv2.matchTemplate(image, gameover_template, cv2.TM_CCOEFF_NORMED)
                if np.where(res >= 0.7)[0]:
                    reset_game()
                    return score
            last_distance = distance

            if verbose > 0:
                print('Distance: {:3d} Size {:2d} Speed: {:3d} Score: {:4.0f}'.format(distance, size, speed,
                                                                                      score) + ' ' * 10, end='\r')
            if time.time() - last_command_time < 0.6:
                continue
            command = get_command_callback(distance, size, speed)
            if command:
                last_command_time = time.time()
                pyautogui.press(command)


def find_game_position(screenshotter, threshold) -> Dict:
    dino_template = cv2.imread(os.path.join('templates', 'dino.png'), 0)
    w, h = dino_template.shape[::-1]
    landscape_template = cv2.imread(os.path.join('templates', 'dino_landscape.png'), 0)
    lw, lh = landscape_template.shape[::-1]
    landscape = {}
    for monitor in screenshotter.enum_display_monitors()[1:-1]:
        buffer = screenshotter.get_pixels(monitor)
        image = Image.frombytes('RGB', (monitor['width'], monitor['height']), buffer).convert('L')
        image = np.array(image)
        res = cv2.matchTemplate(image, dino_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        if len(loc[0]):
            pt = next(zip(*loc[::-1]))
            landscape = dict(monitor, height=lh, left=pt[0], top=pt[1] - lh + h, width=lw)
            break
    return landscape


def reject_outliers(values: List[float]) -> np.array:
    values = np.array(values)
    fator = 1.5
    q1, q3 = np.percentile(values, [25, 75], interpolation='higher')
    iqr = q3 - q1
    low_pass = q1 - (iqr * fator)
    high_pass = q3 + (iqr * fator)
    outliers = np.argwhere(values < low_pass)
    values = np.delete(values, outliers)
    outliers = np.argwhere(values > high_pass)
    values = np.delete(values, outliers)
    return values


def compute_distance_and_size(roi: np.array, max_distance: int) -> (int, int):
    misses = 0
    obstacle_found = False
    size = 0
    distance = max_distance
    roi_mean_color = np.floor(roi.mean())
    for i, column in enumerate(roi.T):
        if len(np.where(column < roi_mean_color)[0]) > 0:
            misses = 0
            if not obstacle_found:
                distance = i
            obstacle_found = True
            size += 1
        elif obstacle_found:
            misses += 1
            if misses >= 5:
                break
    return distance, size


def compute_region_of_interest(landscape: Dict) -> (int, int, int, int):
    ground_height = 12
    y1 = landscape['height'] - 44
    y2 = landscape['height'] - ground_height
    x1 = 44 + 24
    x2 = landscape['width'] - 1
    return x1, x2, y1, y2


def compute_speed(distance: int, last_distance: int,
                  speed: int, last_speeds: List[float], last_compute_speed: float) -> int:
    if distance < last_distance:
        dt = (time.time() - last_compute_speed) * 10 + 1
        last_speeds.append((last_distance - distance) / dt)
        if len(last_speeds) > 30:
            last_speeds.pop(0)
        try:
            speed = int(np.max([np.mean(reject_outliers(last_speeds)), speed]))
        except ValueError:
            print(last_speeds)
            print(reject_outliers(last_speeds))
            print(np.mean(reject_outliers(last_speeds)))
            exit(1)
    return speed


def start_game():
    pyautogui.press('space')
    time.sleep(1.5)


def reset_game():
    pyautogui.hotkey('ctrl', 'r')
    time.sleep(1)


def get_game_landscape_and_set_focus_or_die(screenshotter, threshold=0.7) -> Dict:
    landscape = find_game_position(screenshotter, threshold)
    if not landscape:
        print("Can't find the game!")
        exit(1)
    pyautogui.click(landscape['left'], landscape['top'] + landscape['height'])
    return landscape
