import asyncio
import curses
import random
import time
from curses_tools import draw_frame, read_controls, get_frame_size
from space_garbage import fly_garbage
from physics import update_speed

TIC_TIMEOUT = 0.1
STARS = ('+', '*', '.', ':')
STARS_COUNT = 80

coroutines: list = list()
obstacles: list = list()
spaceship_frame: str = ''


async def sleep(tics=1):
    for i in range(tics):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, garbage_frames, window_size):
    _, window_size_x = window_size
    while True:
        column = random.randint(1, window_size_x - 1)
        frame = random.choice(garbage_frames)
        coroutines.append(fly_garbage(canvas, column, frame, speed=0.5))
        await sleep(20)


async def fire(canvas, start_row, start_column, rows_speed=-0.3,
               columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def random_seconds():
    """
    Calculate count await-elements for drawing
    """
    return int(random.randint(10, 80) * 0.1 / TIC_TIMEOUT)


async def blink(canvas, row, column):
    """
    Blink the star
    """
    symbol = random.choice(STARS)
    while True:
        # await sleep(random_seconds())
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol, curses.A_DIM)

        # await sleep(random_seconds())
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)

        # await sleep(random_seconds())
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol, curses.A_BOLD)

        # await sleep(random_seconds())
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)


def calc_new_position(readkeys, row, column, window_size, frame_size):
    """
    Calculate the new coordinates of the rocket
    given the boundaries of the window
    """
    border_depth = 1

    move_down = move_right = 1
    move_up = move_left = -1
    rows_direction, columns_direction, space_pressed = readkeys

    up_border = left_border = 1
    window_size_y, window_size_x = window_size
    frame_size_y, frame_size_x = frame_size

    # left and right borders based on ship size
    bottom_border = window_size_y - frame_size_y - border_depth
    right_border = window_size_x - frame_size_x - border_depth

    calc_row = row
    calc_column = column
    if (rows_direction == move_up and row > up_border) or (
            rows_direction == move_down and row < bottom_border):
        calc_row += rows_direction
    if (columns_direction == move_left and column > left_border) or (
            columns_direction == move_right and column < right_border):
        calc_column += columns_direction
    return calc_row, calc_column


async def animate_spaceship(frame1, frame2):
    # TODO:
    # while True:
    global spaceship_frame
    spaceship_frame = frame1
    await asyncio.sleep(0)


async def run_spaceship(canvas, window_size):
    """
    Draw and move the rocket
    """
    last_frame: str = ''
    border_depth = 1
    # TODO:

    frame_size = get_frame_size(spaceship_frame)
    frame_size_y, frame_size_x = frame_size
    window_size_y, window_size_x = window_size

    rocket_start_position_y = window_size_y - frame_size_y - border_depth
    row = rocket_start_position_y

    window_center_x = int(window_size_x/2)
    frame_width_half = int(frame_size_x/2)
    rocket_start_position_x = window_center_x - frame_width_half
    column = rocket_start_position_x

    draw_frame(canvas, row, column, spaceship_frame)
    last_frame = spaceship_frame
    await asyncio.sleep(0)

    while True:
        draw_frame(canvas, row, column, last_frame, negative=True)
        readkeys = read_controls(canvas)
        row, column = calc_new_position(readkeys, row, column, window_size,
                                        frame_size)
        draw_frame(canvas, row, column, spaceship_frame)
        last_frame = spaceship_frame
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, last_frame, negative=True)
        readkeys = read_controls(canvas)
        row, column = calc_new_position(readkeys, row, column, window_size,
                                        frame_size)
        draw_frame(canvas, row, column, spaceship_frame)
        last_frame = spaceship_frame
        await asyncio.sleep(0)


def draw(canvas):
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

    border_depth = 1
    array_index_correction = 1

    window_size = canvas.getmaxyx()
    window_size_y, window_size_x = window_size
    stars_up_border = stars_left_border = 1
    stars_bottom_border = window_size_y - border_depth - array_index_correction
    stars_right_border = window_size_x - border_depth - array_index_correction

    # Creating stars
    for _ in range(STARS_COUNT):
        row = random.randint(stars_up_border, stars_bottom_border)
        column = random.randint(stars_left_border, stars_right_border)
        coroutines.append(blink(canvas, row, column))

    window_center_y = int(window_size_y/2)
    window_center_x = int(window_size_x/2)

    coroutines.append(fire(canvas, window_center_y, window_center_x))
    coroutines.append(animate_spaceship(frame_1, frame_2))
    coroutines.append(run_spaceship(canvas, window_size))
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames, window_size))

    while coroutines:
        for coroutine in coroutines:
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
