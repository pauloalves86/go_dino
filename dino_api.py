import os
import time
from typing import Dict, List, Callable

import cv2
import numpy as np
import pyautogui
from PIL import Image
from mss import mss


class Board(object):
    def __init__(self):
        self.landscape_template = cv2.imread(os.path.join('templates', 'dino_landscape.png'), 0)
        self.gameover_template = cv2.imread(os.path.join('templates', 'dino_gameover.png'), 0)

        self.shooter = mss()
        self.get_game_landscape_and_set_focus_or_die()
        self.reset_game()
        self.landscape = self.get_game_landscape_and_set_focus_or_die(.95)

        ground_height = 12
        self.y1 = self.landscape['height'] - 44
        self.y2 = self.landscape['height'] - ground_height
        self.x1 = 44 + 24
        self.x2 = self.landscape['width'] - 1

    def play_game(self, get_command_callback: Callable[[int, int, int], str]) -> int:
        self.start_game()

        start = last_compute_speed = last_command_time = time.time()
        last_distance = self.landscape['width']
        speed = 0
        last_speeds = [3] * 30

        while True:
            buffer = self.shooter.grab(self.landscape)
            image = Image.frombytes('RGB', buffer.size, buffer.rgb).convert('L')
            image = np.array(image)
            image += np.abs(247 - image[0, self.x2])
            roi = image[self.y1:self.y2, self.x1:self.x2]
            score = int((time.time() - start) * 10)
            distance, size = self.compute_distance_and_size(roi, self.x2)
            speed = self.compute_speed(distance, last_distance, speed, last_speeds, last_compute_speed)
            last_compute_speed = time.time()
            # Check GAME OVER
            if distance == last_distance or distance == 0:
                res = cv2.matchTemplate(image, self.gameover_template, cv2.TM_CCOEFF_NORMED)
                if np.max(res) > 0.5:
                    return score
            last_distance = distance
            if time.time() - last_command_time < 0.6:
                continue
            command = get_command_callback(distance, size, speed)
            if command:
                last_command_time = time.time()
                pyautogui.press(command)

    def find_game_position(self, threshold) -> Dict:
        monitor = self.shooter.monitors[0]
        buffer = self.shooter.grab(monitor)
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
            lw, lh = self.landscape_template.shape[::-1]
            return dict(monitor, height=lh, left=pt[0], top=pt[1] - lh + h, width=lw)
        return {}

    @staticmethod
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

    @staticmethod
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

    def compute_speed(self, distance: int, last_distance: int,
                      speed: int, last_speeds: List[float], last_compute_speed: float) -> int:
        if distance < last_distance:
            dt = (time.time() - last_compute_speed) * 10 + 1
            last_speeds.append((last_distance - distance) / dt)
            if len(last_speeds) > 30:
                last_speeds.pop(0)
            speed = int(np.max([np.mean(self.reject_outliers(last_speeds)), speed]))
        return speed

    @staticmethod
    def start_game():
        pyautogui.press('up')
        time.sleep(.3)
        pyautogui.press('up')
        time.sleep(.3)
        pyautogui.press('up')
        time.sleep(1.)

    @staticmethod
    def reset_game():
        pyautogui.hotkey('ctrl', 'r')
        time.sleep(4.)

    def get_game_landscape_and_set_focus_or_die(self, threshold=0.7) -> Dict:
        tries = 0
        landscape = None
        while not landscape:
            landscape = self.find_game_position(threshold)
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
