import warnings
import multiprocessing
from farm.boss import Boss
from farm.fishing import Fishing
from farm.gauntlet import Gauntlet
from farm.trials import Trails
from farm.gvg import Gvg
from farm.pvp import Pvp
from farm.raid import Raid
from farm.quest import Quest
from farm.expedition import Expedition
from decorator import create_marker_file, focus_game, go_main_screen_after, terminal_wait, time_messure, check_reconnect


@terminal_wait
@go_main_screen_after
@create_marker_file
@focus_game
@check_reconnect
@time_messure
def main_v2():
    farms = [
        Raid,
        Quest,
        Expedition,
        Gauntlet,
        Gvg,
        Pvp,
        Trails,
        Boss  # second last, due to AFK host, or lobby not good
    ]

    # this will run each farm, to spend there energy
    empty = {}
    while len(empty) < len(farms):
        for i, farm in enumerate(farms):
            if i in empty:
                continue
            f = farm()
            f.start(wait_done=True)
            if not f.get_result():
                empty[i] = True

    while True:
        f = Fishing()  # this last, because no energy needed
        f.start(wait_done=True)
        if not f.get_result():
            break


if __name__ == '__main__':
    multiprocessing.freeze_support()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main_v2()
