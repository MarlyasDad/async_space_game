import asyncio
import curses
import random
import time
from itertools import cycle
from statistics import median
from dataclasses import dataclass, field
from curses_tools import draw_frame, read_controls, get_frame_size
from space_garbage import fly_garbage
from physics import update_speed


@dataclass
class IsRunning:
    state: bool = field(default=True)


TIC_TIMEOUT = 0.1
STARS = ('+', '*', '.', ':')
STARS_COUNT = 150

is_running = IsRunning()
coroutines: list = list()
obstacles: list = list()
obstacles_in_last_collisions: list = list()
spaceship_frame: str = ''
ship_row_speed = ship_col_speed = 0
year = 1957
level = 1
max_level = 100
garbage_speed = 0.1
weapon = False


async def sleep(tics=1):
    for i in range(tics):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, garbage_frames, window_size,
                                  border_depth):
    global is_running
    global level, max_level, garbage_speed

    await sleep(20)
    while is_running.state:
        frame = random.choice(garbage_frames)
        coroutines.append(fly_garbage(
            canvas, frame, obstacles, obstacles_in_last_collisions, is_running,
            window_size, border_depth, speed=garbage_speed))
        await sleep(max_level + 1 - level)


async def level_increase(canvas):
    global level, garbage_speed, year, weapon, max_level
    global is_running

    garbage_acceleration = 0.01
    level_acceleration = 1
    year_acceleration = 1

    while is_running.state:
        canvas.addstr(1, 1, f"Year: {year} Weapon: {weapon}")
        await sleep(20)
        level += level_acceleration

        if level > max_level:
            level = max_level

        year += year_acceleration
        garbage_speed += garbage_acceleration
        if year >= 2020:
            weapon = True


async def fire(canvas, start_row, start_column, rows_speed=-0.3,
               columns_speed=0):
    """
    Display animation of gun shot. Direction and speed can be specified.
    """
    global is_running

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep(1)
    canvas.addstr(round(row), round(column), 'O')
    await sleep(1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 1 < column < max_column and is_running.state:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return


def random_ticks():
    """
    Calculate count await-elements for drawing
    """
    return int(random.randint(1, 8) * 0.25 / TIC_TIMEOUT)


async def blink(canvas, row, column):
    """
    Blink the star
    """
    symbol = random.choice(STARS)
    while True:
        for _ in range(random_ticks()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol, curses.A_DIM)

        for _ in range(random_ticks()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)

        for _ in range(random_ticks()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol, curses.A_BOLD)

        for _ in range(random_ticks()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)


def move_spaceship(readkeys, row, column, window_size, frame_size,
                   border_depth):
    """
    Calculate the new coordinates of the rocket
    given the boundaries of the window
    """
    global ship_row_speed, ship_col_speed
    rows_direction, columns_direction, space_pressed = readkeys

    up_border = left_border = border_depth
    window_size_y, window_size_x = window_size
    frame_size_y, frame_size_x = frame_size

    # left and right borders based on ship size
    bottom_border = window_size_y - frame_size_y - border_depth
    right_border = window_size_x - frame_size_x - border_depth

    ship_row_speed, ship_col_speed = update_speed(
        ship_row_speed, ship_col_speed, rows_direction, columns_direction)

    calc_row, calc_column = row + ship_row_speed, column + ship_col_speed

    if ship_row_speed < 0 and calc_row < up_border + 1:
        calc_row = up_border

    if ship_row_speed > 0 and calc_row > bottom_border:
        calc_row = bottom_border

    if ship_col_speed < 0 and calc_column < left_border + 1:
        calc_column = left_border

    if ship_col_speed > 0 and calc_column > right_border:
        calc_column = right_border

    return calc_row, calc_column


async def animate_spaceship(frame1, frame2):
    global spaceship_frame
    for frame in cycle([frame1, frame2]):
        spaceship_frame = frame
        await sleep(2)


async def run_spaceship(canvas, window_size, border_depth):
    """
    Draw and move the rocket
    """
    global is_running
    global coroutines
    global weapon

    frame_size = get_frame_size(spaceship_frame)
    frame_size_y, frame_size_x = frame_size
    window_size_y, window_size_x = window_size

    rocket_start_position_y = window_size_y - frame_size_y - border_depth
    row = rocket_start_position_y
    window_center_x = median([1, window_size_x, ])
    frame_width_half = median([1, frame_size_x, ])
    rocket_start_position_x = window_center_x - frame_width_half
    column = rocket_start_position_x

    last_frame = spaceship_frame

    try:
        while True:
            draw_frame(canvas, row, column, last_frame, negative=True)
            readkeys = read_controls(canvas)
            row, column = move_spaceship(readkeys, row, column, window_size,
                                         frame_size, border_depth)
            draw_frame(canvas, row, column, spaceship_frame)
            last_frame = spaceship_frame

            _, _, space_pressed = readkeys
            if space_pressed and weapon:
                coroutines.append(fire(canvas, row, column + frame_width_half))
            await asyncio.sleep(0)

            for obstacle in obstacles:
                if obstacle.has_collision(row, column, frame_size_y,
                                          frame_size_x):
                    return
    finally:
        is_running.state = False
        draw_frame(canvas, row, column, last_frame, negative=True)
        coroutines.append(show_game_over(canvas, window_size))


async def show_game_over(canvas, window_size):
    with open('frames/game_over.txt', 'r') as file:
        frame = file.read()

    window_size_y, window_size_x = window_size
    frame_size = get_frame_size(frame)
    frame_size_y, frame_size_x = frame_size

    window_center_x = median([0, window_size_x, ])
    frame_width_half = median([0, frame_size_x, ])
    text_start_position_x = window_center_x - frame_width_half
    column = text_start_position_x

    window_center_y = median([0, window_size_y, ])
    frame_height_half = median([0, frame_size_y, ])
    text_start_position_y = window_center_y - frame_height_half
    row = text_start_position_y
    while True:
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)


def draw(canvas):
    global is_running
    global coroutines
    global obstacles

    with open('frames/rocket_frame_1.txt', 'r') as file:
        frame_1 = file.read()

    with open('frames/rocket_frame_2.txt', 'r') as file:
        frame_2 = file.read()

    garbage_names = ['duck', 'hubble', 'lamp', 'trash_large', 'trash_small',
                     'trash_xl']
    garbage_frames = list()
    for name in garbage_names:
        with open(f'frames/{name}.txt', 'r') as file:
            garbage_frames.append(file.read())

    canvas.border(0)
    canvas.nodelay(True)
    canvas.derwin(2, 35, 1, 1)
    is_running.state = True

    border_depth = 1
    array_index_correction = 1
    window_size = canvas.getmaxyx()
    window_size_y, window_size_x = window_size
    stars_up_border = stars_left_border = array_index_correction
    stars_bottom_border = window_size_y - border_depth - array_index_correction
    stars_right_border = window_size_x - border_depth - array_index_correction
    for _ in range(STARS_COUNT):
        row = random.randint(stars_up_border, stars_bottom_border)
        column = random.randint(stars_left_border, stars_right_border)
        coroutines.append(blink(canvas, row, column))

    coroutines.append(level_increase(canvas))
    coroutines.append(animate_spaceship(frame_1, frame_2))
    coroutines.append(run_spaceship(canvas, window_size, border_depth))
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames,
                                              window_size, border_depth))

    while coroutines:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.initscr()
    curses.curs_set(False)
    curses.wrapper(draw)
    input('Нажмите любую клавишу для выхода...')
