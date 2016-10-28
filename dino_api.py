import cv2
import time
from PIL import Image
import numpy as np
import pyautogui
from itertools import count
from mss import mss


def play_game(get_command_callback) -> int:
    with mss() as screenshotter:
        landscape = find_game_position(screenshotter)
        if landscape:
            pyautogui.moveTo(landscape['left'], landscape['top'] + landscape['height'])
            pyautogui.click()
            pyautogui.press('space')
            time.sleep(0.5)

            start = time.time()
            fps_timer = time.time()
            fps = 0
            fps_min = 999
            fps_max = 0
            loop_counter = count()
            gameover_template = cv2.imread('dino_gameover.png', 0)
            speed = 0
            last_distance = landscape['width']
            ground_height = 12
            y1 = landscape['height'] - 44 - ground_height
            y2 = landscape['height'] - ground_height
            x1 = 44 + 22
            x2 = landscape['width'] - 1
            last_compute_speed = time.time()
            last_speeds = []
            while True:
                buffer = screenshotter.get_pixels(landscape)
                image = Image.frombytes('RGB', (landscape['width'], landscape['height']), buffer).convert('L')
                image = np.array(image)
                if image[0, x2] < 127:
                    image = 255 - image
                roi = image[y1:y2, x1:x2]

                misses = 0
                obstacle_found = False
                size = 0
                distance = x2
                for i, column in enumerate(roi.T):
                    if column.mean() <= 200:
                        misses = 0
                        if not obstacle_found:
                            distance = i
                        obstacle_found = True
                        size += 1
                    elif obstacle_found:
                        misses += 1
                        if misses >= 5:
                            break

                score = np.floor((time.time() - start) * 10)
                if distance < last_distance:
                    now = time.time()
                    dt = (now - last_compute_speed) * 10
                    last_compute_speed = now
                    last_speeds.append((last_distance - distance) / dt)
                    if len(last_speeds) > 30:
                        last_speeds.pop(0)
                    speed = int(np.max([np.mean(reject_outliers(last_speeds)), speed]))
                elif distance == last_distance and speed != 0:
                    # Check GAME OVER
                    res = cv2.matchTemplate(image, gameover_template, cv2.TM_CCOEFF_NORMED)
                    if np.where(res >= 0.7)[0]:
                        pyautogui.hotkey('ctrl', 'r')
                        return score
                last_distance = distance

                command = get_command_callback(distance, size, speed)
                if command:
                    pyautogui.press(command)

                counter = next(loop_counter)
                now = time.time()
                delta_time = now - fps_timer
                if delta_time >= .5:
                    fps = counter / delta_time
                    if fps < fps_min:
                        fps_min = fps
                    elif fps > fps_max:
                        fps_max = fps
                    fps_timer = now
                    loop_counter = count()


def find_game_position(screenshotter):
    dino_template = cv2.imread('dino.png', 0)
    w, h = dino_template.shape[::-1]
    landscape_template = cv2.imread('dino_landscape.png', 0)
    lw, lh = landscape_template.shape[::-1]
    landscape = {}
    for monitor in screenshotter.enum_display_monitors()[1:-1]:
        buffer = screenshotter.get_pixels(monitor)
        image = Image.frombytes('RGB', (monitor['width'], monitor['height']), buffer).convert('L')
        image = np.array(image)
        res = cv2.matchTemplate(image, dino_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.7
        loc = np.where(res >= threshold)
        if len(loc[0]):
            pt = next(zip(*loc[::-1]))
            landscape = {'height': lh, 'left': pt[0], 'monitor': monitor['monitor'], 'top': pt[1] - lh + h, 'width': lw}
            break
    return landscape


def reject_outliers(sr, iq_range=0.8):
    if len(sr) == 1:
        return sr
    sr = np.array(sr)
    pcnt = (1 - iq_range) / 2
    qlow, median, qhigh = np.percentile(sr, [pcnt, 0.5, 1 - pcnt])
    iqr = qhigh - qlow
    return sr[np.where(np.abs(sr - median) <= iqr)]
