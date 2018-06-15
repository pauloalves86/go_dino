import os
import time
from typing import Dict, List, Callable

import cv2
import numpy as np
import pyautogui
from PIL import Image
from mss import mss


def play_game(get_command_callback: Callable[[int, int, int], str]) -> int:
    with mss() as screenshotter:
        get_game_landscape_and_set_focus_or_die(screenshotter)
        reset_game()
        landscape = get_game_landscape_and_set_focus_or_die(screenshotter, .95)

        start_game()
        gameover_template = cv2.imread(os.path.join('templates', 'dino_gameover.png'), 0)
        gameover_template2 = cv2.imread(os.path.join('templates', 'dino_gameover2.png'), 0)
        start = time.time()
        last_distance = landscape['width']
        x1, x2, y1, y2 = compute_region_of_interest(landscape)
        speed = 0
        last_compute_speed = time.time()
        last_speeds = [3] * 30
        last_command_time = time.time()

        while True:
            buffer = screenshotter.grab(landscape)
            image = Image.frombytes('RGB', buffer.size, buffer.rgb).convert('L')
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
                if np.max(res) < 0.7:
                    res = cv2.matchTemplate(image, gameover_template2, cv2.TM_CCOEFF_NORMED)
                if np.max(res) >= 0.7:
                    reset_game()
                    return score
            last_distance = distance
            if time.time() - last_command_time < 0.6:
                continue
            command = get_command_callback(distance, size, speed)
            if command:
                last_command_time = time.time()
                pyautogui.press(command)


def find_game_position(screenshotter, threshold) -> Dict:
    monitor = screenshotter.monitors[0]
    buffer = screenshotter.grab(monitor)
    image = Image.frombytes('RGB', buffer.size, buffer.rgb).convert('L')
    image = np.array(image)
    dino_template = cv2.imread(os.path.join('templates', 'dino.png'), 0)
    res = cv2.matchTemplate(image, dino_template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    if len(loc[0]) == 0:
        dino_template = cv2.imread(os.path.join('templates', 'dino2.png'), 0)
        res = cv2.matchTemplate(image, dino_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
    if len(loc[0]):
        pt = next(zip(*loc[::-1]))
        w, h = dino_template.shape[::-1]
        landscape_template = cv2.imread(os.path.join('templates', 'dino_landscape.png'), 0)
        lw, lh = landscape_template.shape[::-1]
        return dict(monitor, height=lh, left=pt[0], top=pt[1] - lh + h, width=lw)
    return {}


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
    obstacle_found = False
    distance = max_distance
    roi_mean_color = np.floor(roi.mean())
    last_column = distance
    for column in np.unique(np.where(roi < roi_mean_color)[1]):
        if not obstacle_found:
            distance = column
            obstacle_found = True
        elif column > last_column + 4:
            break
        last_column = column
    return distance, last_column - distance


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
        speed = int(np.max([np.mean(reject_outliers(last_speeds)), speed]))
    return speed


def start_game():
    pyautogui.press('space')
    time.sleep(1.5)


def reset_game():
    pyautogui.hotkey('ctrl', 'r')
    time.sleep(2.5)


def get_game_landscape_and_set_focus_or_die(screenshotter, threshold=0.7) -> Dict:
    tries = 0
    landscape = None
    while not landscape:
        landscape = find_game_position(screenshotter, threshold)
        if landscape or tries == 10:
            break
        else:
            tries += 1
        time.sleep(1)
    if not landscape:
        print("Can't find the game!")
        exit(1)
    pyautogui.click(landscape['left'], landscape['top'] + landscape['height'])
    return landscape
