import time
import asyncio
import curses


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
await asyncio.sleep(0)


def draw(canvas):
    row, column = (1, 10)
    canvas.border(0)
    canvas.nodelay(True)
    while True:
        # canvas.addstr(row, column, 'Hello, World!')
        canvas.addstr(row, column, '*', curses.A_DIM)
        canvas.refresh()
        time.sleep(2)
        canvas.addstr(row, column, '*')
        canvas.refresh()
        time.sleep(0.3)
        canvas.addstr(row, column, '*', curses.A_BOLD)
        canvas.refresh()
        time.sleep(0.5)
        canvas.addstr(row, column, '*')
        canvas.refresh()
        time.sleep(0.3)
        key = canvas.getkey()
        if key == "q":
            exit()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(False)
    input('Нажмите любую клавишу для выхода...')
