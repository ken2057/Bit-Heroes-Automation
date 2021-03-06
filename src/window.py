import os
import pyautogui
import pywinauto
import win32gui
import sys
from time import sleep
from debug import save_image_dbg, save_print_dbg
from error import *
from const import *
import const


def get_app():
    const.app = pywinauto.Application().connect(path=APP_NAME)
    cur_pos = pyautogui.position()
    const.app.top_window().set_focus()
    pyautogui.moveTo(cur_pos.x, cur_pos.y)


def click_screen_and_sleep(y: int, x: int, sleep_duration=SLEEP):
    def add(x): return x + PREFIX_CLICK
    cur_active = pyautogui.getActiveWindow()
    cur_pos = pyautogui.position()
    if not const.app:
        get_app()
    const.app[GAME_TITLE].click_input(
        coords=(add(x), add(y) + TITLE_BAR_HEIGHT))
    # reset mouse position and set focus to previous app
    pyautogui.moveTo(cur_pos.x, cur_pos.y)
    cur_active.activate()
    sleep(sleep_duration)


def get_game_screen():
    if sys.platform in ['Windows', 'win32', 'cygwin']:
        hwnd = win32gui.FindWindow(None, GAME_TITLE)

        if not hwnd:
            raise MismatchConditionException(txt=f'{GAME_TITLE} not running')

        x, y, x1, y1 = win32gui.GetClientRect(hwnd)
        if (x1, y1) != MAX_RESOLUTION:
            raise MismatchConditionException(
                txt='Resolution %s:%s not supported, working resolution is %s:%s' % (x1, y1, *MAX_RESOLUTION))

        x, y = win32gui.ClientToScreen(hwnd, (x, y))
        x1, y1 = win32gui.ClientToScreen(hwnd, (x1 - x, y1 - y))
        img = pyautogui.screenshot(region=(x, y, x1, y1))

        # save_image_dbg('get_game_screen', img)

        return img

    raise MismatchConditionException(txt='OS not supported')


def start_game():
    if sys.platform in ['Windows', 'win32', 'cygwin']:
        hwnd = win32gui.FindWindow(None, GAME_TITLE)
        if not hwnd:
            os.system(f"start steam://rungameid/{STEAM_ID}")
        else:
            win32gui.SetForegroundWindow(hwnd)
    else:
        raise MismatchConditionException(txt='OS not supported')


def press_escape():
    get_app()
    cur_pos = pyautogui.position()
    cur_active = pyautogui.getActiveWindow()
    pywinauto.keyboard.send_keys('{VK_ESCAPE}')
    pyautogui.moveTo(cur_pos.x, cur_pos.y)
    cur_active.activate()
    save_print_dbg('pressed escape')
