import asyncio
import curses
import random
import time
from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1
STARS = ('+', '*', '.', ':')
STARS_COUNT = 90


def random_seconds():
    return int(random.randint(3, 50) * 0.1 / TIC_TIMEOUT)


async def animate_spaceship():
    pass


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


async def blink(canvas, window_size):
    row = random.randint(1, window_size[0] - 2)
    column = random.randint(1, window_size[1] - 2)
    symbol = random.choice(STARS)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)

        canvas.addstr(row, column, symbol)
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)

        canvas.addstr(row, column, symbol)
        for _ in range(random_seconds()):
            await asyncio.sleep(0)
            canvas.addstr(row, column, symbol)


def calc_new_positions(readkeys, row, column, window_size, frame_size):
    """
    Calculate the new coordinates of the rocket
    given the boundaries of the window
    """
    calc_row = row
    calc_column = column
    if (readkeys[0] < 0 and row > 1) or (
            readkeys[0] > 0 and row < window_size[0] - frame_size[0] - 1):
        calc_row += readkeys[0]
    if (readkeys[1] < 0 and column > 1) or (
            readkeys[1] > 0 and column < window_size[1] - frame_size[1] - 1):
        calc_column += readkeys[1]
    return calc_row, calc_column


async def draw_rocket(canvas, frame1, frame2, row, column, window_size):
    """
    Draw and move the rocket
    """
    canvas.nodelay(True)
    frame_size = get_frame_size(frame1)

    draw_frame(canvas, row, column, frame1)
    await asyncio.sleep(0)

    while True:
        draw_frame(canvas, row, column, frame1, negative=True)
        readkeys = read_controls(canvas)
        row, column = calc_new_positions(readkeys, row, column, window_size,
                                         frame_size)
        draw_frame(canvas, row, column, frame2)
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frame2, negative=True)
        readkeys = read_controls(canvas)
        row, column = calc_new_positions(readkeys, row, column, window_size,
                                         frame_size)
        draw_frame(canvas, row, column, frame1)
        await asyncio.sleep(0)


def draw(canvas):
    with open('frames/rocket_frame_1.txt', 'r') as file:
        frame_1 = file.read()

    with open('frames/rocket_frame_2.txt', 'r') as file:
        frame_2 = file.read()

    canvas.border(0)
    canvas.nodelay(True)
    window_size = canvas.getmaxyx()
    frame_size = get_frame_size(frame1)

    blink_list = [blink(canvas, window_size) for _ in range(STARS_COUNT)]

    coroutines = [
        *blink_list,
        fire(canvas, window_size[0] / 2, window_size[1] / 2,),
        draw_rocket(canvas, frame_1, frame_2,
                    window_size[0] - frame_size[0] - 1,
                    window_size[1] / 2, window_size),
    ]

    while coroutines:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)
        if len(coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.initscr()
    curses.curs_set(False)
    curses.wrapper(draw)
    input('Нажмите любую клавишу для выхода...')
