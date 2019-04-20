import asyncio
import curses

TIC_TIMEOUT = 0.1


class EventLoopCommand:

    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):

    def __init__(self, seconds):
        self.seconds = seconds


def convert_seconds_to_iterations(seconds):
    return seconds * 1000000


async def refresh(canvas, seconds):
    while True:
        canvas.refresh()
        await Sleep(seconds)


async def blink_the_star(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await Sleep(2)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await Sleep(0.5)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)


def draw(canvas):
    canvas.border(0)
    canvas.nodelay(True)

    coroutines = {
        refresh(canvas, TIC_TIMEOUT): 0,
        blink_the_star(canvas, row=1, column=5, symbol=':'): 0,
        blink_the_star(canvas, row=1, column=7): 0,
        blink_the_star(canvas, row=1, column=9): 0,
    }

    while coroutines:
        for coroutine in coroutines:
            try:
                if coroutines[coroutine] <= 0:
                    timeout = coroutine.send(None).seconds
                    ticks_to_sleep = convert_seconds_to_iterations(timeout)
                    coroutines[coroutine] = ticks_to_sleep
                coroutines[coroutine] -= 1
            except StopIteration:
                del coroutines[coroutine]


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.initscr()
    curses.curs_set(False)
    curses.wrapper(draw)
    input('Нажмите любую клавишу для выхода...')
