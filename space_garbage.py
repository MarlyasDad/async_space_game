from curses_tools import draw_frame, get_frame_size
import asyncio
import random
from statistics import median
from obstacles import Obstacle
from exploison import explode


async def fly_garbage(canvas, garbage_frame, obstacles, collisions, is_running, window_size, border_depth, speed=0.5):
    """
    Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start.
    """
    _, window_size_x = window_size

    rows_number, columns_number = canvas.getmaxyx()

    frame_size = get_frame_size(garbage_frame)
    frame_size_y, frame_size_x = frame_size

    row = 1

    column = random.randint(border_depth + frame_size_x, window_size_x - border_depth - frame_size_x)

    obstacle = Obstacle(row, column, frame_size_y, frame_size_x)
    obstacles.append(obstacle)

    try:
        while row < rows_number - frame_size_y - border_depth:
            draw_frame(canvas, row, column, garbage_frame)
            obstacle.row = row
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed

            if obstacle in collisions or not is_running.state:
                await explode(canvas, row + median([0, frame_size_y]), column + median([0, frame_size_x]))
                return
    finally:
        obstacles.remove(obstacle)
