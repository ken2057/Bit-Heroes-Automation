import json
from window import click_screen_and_sleep, get_game_screen, press_escape
from debug import save_image_dbg, save_print_dbg
from error import *
from const import *
import const
from time import sleep
import os
import cv2
import numpy as np
from PIL import Image, ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)


def find_image_position(
    image_source: Image,
    image_find_path: str,
    threshold=None,
):
    image_path = image_find_path.replace(IMG_PATH+os.sep, '')
    name = '_'.join(image_path.split(os.sep))

    if type(image_source) == str:
        source = np.array(Image.open(image_source).convert('RGBA'))
    else:
        source = np.array(image_source.convert('RGBA'))

    # convert from maximum size to current game resolution
    find_image = Image.open(image_find_path).convert('RGBA')
    old_width, old_height = find_image._size
    find = np.array(find_image)

    heat_map = cv2.matchTemplate(source, find, cv2.TM_CCOEFF_NORMED)
    max_corr = round(np.max(heat_map), 2)

    save_print_dbg(f'matching: {max_corr:.2f}/{threshold}')

    if threshold and not max_corr >= threshold:
        raise ImageNotFoundException(image_path=image_path)

    y, x = np.unravel_index(np.argmax(heat_map), heat_map.shape)

    y += int(old_height / 2)
    x += int(old_width / 2)

    cv2.rectangle(source, (x, y), (x+5, y+5), (255, 0, 0, 255), 5)
    img = Image.fromarray(source, 'RGBA')
    save_image_dbg(f'find_image_position-{name}', img)

    return y, x


def find_image_and_click_then_sleep(
    path: str,
    retry_time=RETRY_TIME_FIND_IMAGE,
    sleep_duration=SLEEP,
    threshold=DEFAULT_THRESHOLD_IMAGE_MATCH,
    find_interval=SLEEP,
    ignore_exception=False,
):
    sleep(0.1)
    y, x = 0, 0
    try:
        y, x = find_image(path, retry_time, threshold,
                          find_interval=find_interval)
    except Exception as ex:
        if ignore_exception:
            return
        raise ex
    click_screen_and_sleep(y, x, sleep_duration)


def find_image(
    path: str,
    retry_time=RETRY_TIME_FIND_IMAGE,
    threshold=DEFAULT_THRESHOLD_IMAGE_MATCH,
    find_interval=SLEEP,
    game_screen=None,
    return_game_screen=False,
):
    y, x = -1, -1
    e = None
    for i in range(retry_time):
        save_print_dbg(f"retry: {i} on {path.replace(IMG_PATH, '')}", end='\t')
        if game_screen == None:
            cur_game_screen = get_game_screen()
        else:
            cur_game_screen = game_screen
        try:
            y, x = find_image_position(cur_game_screen, path, threshold)
            if return_game_screen:
                return y, x, cur_game_screen
            return y, x
        except Exception as ex:
            e = ex
        sleep(find_interval)
    raise e


def go_main_screen():
    old_dbg_name = const.dbg_name.__str__()
    const.dbg_name = 'escape'
    save_print_dbg("**Debug for action 'press escape'")
    [press_escape() for _ in range(3)]
    while True:
        sleep(SLEEP)
        try:
            find_image_and_click_then_sleep(
                COMMON_NO, retry_time=1, sleep_duration=0.5)
            break
        except:
            pass
        press_escape()

    save_print_dbg("**Finished action 'press escape'")
    const.dbg_name = old_dbg_name


def raise_exception_when_runnable(fun, exception: Exception):
    try:
        fun()
        sleep(SLEEP)
        raise exception()
    except exception as ex:
        raise ex
    except KeyboardInterrupt as ex:
        raise ex
    except:
        pass


def enable_auto_on() -> bool:
    img = get_game_screen()
    try:
        find_image(COMMON_AUTO_ON, retry_time=1,
                   threshold=0.9, game_screen=img)
        return True
    except:
        pass

    try:
        y, x = find_image(COMMON_AUTO_OFF, retry_time=1,
                          threshold=0.9, game_screen=img)
        click_screen_and_sleep(y, x)
        return True
    except:
        pass

    return False


def click_town_or_rerun(is_rerun=False) -> bool:
    img = COMMON_RERUN if is_rerun else COMMON_TOWN
    try:
        y, x = find_image(img, retry_time=1, threshold=0.9)
        sleep(1)
        click_screen_and_sleep(y, x)
        return True
    except:
        return False


def check_no_energy(keep_guide=False):
    def find_not_energy():
        try:
            _, _, img = find_image(
                COMMON_NOT_ENOUGH, threshold=0.9, retry_time=3, return_game_screen=True)
            y, x = find_image(COMMON_NO, threshold=0.9,
                              retry_time=3, game_screen=img)
            sleep(SLEEP)
            click_screen_and_sleep(y, x)
        except:
            # in case of warning can't leave guild, click yes
            if keep_guide:
                find_image_and_click_then_sleep(
                    COMMON_YES, threshold=0.9, retry_time=3)
            raise Exception()

    sleep(SLEEP)
    raise_exception_when_runnable(
        lambda: find_not_energy(),
        NoEnergyException
    )


def click_cost_and_play(cost: str, menu_cost=COMMON_COST, play_btn=COMMON_PLAY, keep_guide=False):
    select_cost(cost=cost, menu_cost=menu_cost)
    click_play_and_check_no_energy(play_btn=play_btn, keep_guide=keep_guide)


def select_cost(cost: str, menu_cost=COMMON_COST):
    find_image_and_click_then_sleep(menu_cost, retry_time=5)
    clicked = False
    try:
        find_image_and_click_then_sleep(
            cost, retry_time=3, sleep_duration=0.5, threshold=0.9)
        clicked = True
        find_image(cost, retry_time=1)
        press_escape()
    except:
        if not clicked:
            press_escape()
    finally:
        sleep(SLEEP)


def click_play_and_check_no_energy(play_btn=COMMON_PLAY, keep_guide=False):
    find_image_and_click_then_sleep(play_btn, retry_time=5, sleep_duration=1)
    check_no_energy(keep_guide=keep_guide)
    check_not_full_team()


def check_not_full_team():
    def _run():
        find_image(COMMON_TEAM_NOT_FULL, retry_time=2)
        find_image_and_click_then_sleep(
            COMMON_NO, retry_time=2, ignore_exception=True)
    raise_exception_when_runnable(_run, NotFullTeamException)


def fight_wait_town(is_rerun=False):
    sleep(1)
    while not enable_auto_on():
        sleep(SLEEP)
    while not click_town_or_rerun(is_rerun=is_rerun):
        sleep(1)


def decline_except_persuade(decline):
    y, x, img = None, None, None
    try:
        y, x, img = find_image(decline, retry_time=1, return_game_screen=True)
        find_image(COMMON_PERSUADE, retry_time=1, game_screen=img)
    except:
        if y != None:
            click_screen_and_sleep(y, x, sleep_duration=0.5)
            find_image_and_click_then_sleep(
                COMMON_YES, retry_time=1, ignore_exception=True)


def open_treasure():
    try:
        find_image_and_click_then_sleep(
            COMMON_OPEN, retry_time=1, sleep_duration=0.5)
        find_image_and_click_then_sleep(
            COMMON_YES, retry_time=1, sleep_duration=0.5)
        # decline when no key
        find_image_and_click_then_sleep(
            COMMON_NO, retry_time=1, sleep_duration=0.5)
        press_escape()
        sleep(SLEEP)
        find_image_and_click_then_sleep(
            COMMON_YES, retry_time=1, sleep_duration=0.5)
    except:
        pass


def get_json_file(file) -> dict:
    with open(file, 'r') as f:
        return json.load(f)


def save_json_file(file, data, is_sort=False) -> dict:
    with open(file, 'w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=is_sort))


def set_rerun_mode(is_enable: bool):
    cfg = get_json_file(CONFIG_FILE)
    cfg['rerun_mode'] = is_enable
    save_json_file(CONFIG_FILE, cfg)


def is_smart_rerun() -> bool:
    return get_json_file(CONFIG_FILE).get('smart_rerun_mode', False)


def is_brush_force_energy() -> bool:
    return get_json_file(CONFIG_FILE).get('brush_force_energy', False)


def is_rerun_mode() -> bool:
    return get_json_file(CONFIG_FILE).get('rerun_mode', False)


def is_debug() -> bool:
    return get_json_file(CONFIG_FILE).get('debug', False)


def is_save_captured_image() -> bool:
    return get_json_file(CONFIG_FILE).get('save_captured_image', False)


def is_decline_treasure() -> bool:
    return get_json_file(CONFIG_FILE).get('decline_treasure', False)


def is_image_exist(img: str, retry_time=1, threshold=0.8) -> bool:
    try:
        find_image(img, retry_time=retry_time, threshold=threshold)
        return True
    except:
        return False


def is_no_energy_bar(imgs) -> bool:
    for img in imgs:
        if is_image_exist(img, threshold=0.9):
            return True
    return False


def clean_config_of_farm(name: str):
    cfg = get_json_file(CONFIG_FILE)
    try:
        cfg.pop(name)
    except:
        pass
    save_json_file(CONFIG_FILE, cfg)


def is_config_error(name: str):
    return get_json_file(USAGE_FILE).get(name, {}).get('is_config_error', False)
