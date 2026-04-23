import pygame
from pygame.constants import *
import asyncio
from math import floor, ceil, cos, sin, radians, log2
from random import randint


RANDOM_SEED = randint(0, 18446744073709551615)
INITIAL_WINDOW_WIDTH = 640
INITIAL_WINDOW_HEIGHT = 360
TILE_SIZE = 6
TILES_LONG = 30
TILES_TALL = 20
FONT_SIZE = 20
TEXT_SEPARATION = 10


def merge_values(x: int, y: int, z: int) -> int:
    n = 0
    if x < 0:
        n += 1
        x = -1 - x
    if y < 0:
        n += 2
        y = -1 - y

    bits = ceil(log2(max(x, y, z) + 1))
    i = 4
    for _ in range(bits):
        n += (x % 2) * i
        x //= 2
        i *= 2

        n += (y % 2) * i
        y //= 2
        i *= 2

        n += (z % 2) * i
        z //= 2
        i *= 2

    return n


def coserp(a: float, b: float, f: float) -> float:
    f = (1 - cos(radians(f * 180))) * 0.5
    return a * (1 - f) + b * f


def prng(seed: int) -> tuple[int, float]:
    seed += 31
    seed ^= (seed << 13)
    seed ^= (seed >> 7)
    seed ^= (seed << 17)
    return seed, (seed & 0xFFFFFFFFFFFFFFFF) / 2**64


class PerlinNoise:
    def __init__(self, seed: int, gradient_size: int, chunk_width: int, chunk_height: int, chunk_count: int):
        self.chunk_ids = []
        self.chunk_data = []
        for _ in range(chunk_count):
            self.chunk_ids.append("")
            for _ in range(chunk_width * chunk_height):
                self.chunk_data.append(0.0)

        self.seed = seed
        self.gradient_size = gradient_size
        self.chunk_width = chunk_width
        self.chunk_height = chunk_height
        self.chunk_count = chunk_count
        self.chunk_index = 0

    def get(self, x: int, y: int) -> float:
        x /= self.gradient_size
        y /= self.gradient_size

        x_0 = floor(x)
        y_0 = floor(y)

        x_1 = x_0 + 1
        y_1 = y_0 + 1

        dx = x - x_0
        dy = y - y_0

        n_0 = self.dot_grid_gradient(x_0, y_0, x, y)
        n_1 = self.dot_grid_gradient(x_1, y_0, x, y)
        p_a = coserp(n_0, n_1, dx)

        n_0 = self.dot_grid_gradient(x_0, y_1, x, y)
        n_1 = self.dot_grid_gradient(x_1, y_1, x, y)
        p_b = coserp(n_0, n_1, dx)

        p = coserp(p_a, p_b, dy) + 0.5
        p = min(max(0.0, p), 1.0)
        return p

    def dot_grid_gradient(self, x_i: int, y_i: int, x: float, y: float) -> float:
        sup_x = floor(x_i / self.chunk_width)
        sub_x = x_i % self.chunk_width

        sup_y = floor(y_i / self.chunk_height)
        sub_y = y_i % self.chunk_height

        chunk_id = f"{sup_x},{sup_y}"

        if chunk_id not in self.chunk_ids:
            # generate new chunk
            self.chunk_ids[self.chunk_index] = chunk_id

            data_index = self.chunk_index * (self.chunk_width * self.chunk_height)

            seed, _ = prng(merge_values(sup_x, sup_y, self.seed))
            for _ in range(self.chunk_height):
                for _ in range(self.chunk_width):
                    seed, noise = prng(seed)
                    self.chunk_data[data_index] = noise
                    data_index += 1

            self.chunk_index += 1
            self.chunk_index %= self.chunk_count

        chunk_index = self.chunk_ids.index(chunk_id)
        data_index = (chunk_index * self.chunk_height + sub_y) * self.chunk_width + sub_x

        random_angle = self.chunk_data[data_index]
        return (x - x_i) * cos(radians(random_angle * 360)) + (y - y_i) * sin(radians(random_angle * 360))


async def main():
    pygame.init()
    pygame.display.set_caption("Perlin Noise Sim")
    screen = pygame.display.set_mode((INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT), pygame.RESIZABLE)
    font = pygame.font.SysFont(pygame.font.get_fonts()[0], FONT_SIZE)
    clock = pygame.time.Clock()

    perlin_noise = PerlinNoise(seed=RANDOM_SEED, gradient_size=16, chunk_width=16, chunk_height=16, chunk_count=64)

    x = 0
    y = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        keys = pygame.key.get_pressed()
        screen_width, screen_height = screen.get_size()

        dx = (keys[K_d] or keys[K_RIGHT]) - (keys[K_a] or keys[K_LEFT])
        dy = (keys[K_w] or keys[K_UP]) - (keys[K_s] or keys[K_DOWN])
        if keys[K_LSHIFT]:
            dx *= 5
            dy *= 5
        x += dx
        y += dy

        screen.fill("purple")
        for tile_y in range(-TILES_TALL, TILES_TALL + 1):
            for tile_x in range(-TILES_LONG, TILES_LONG + 1):
                if tile_x == 0 and tile_y == 0:
                    color = (255, 255, 0)
                else:
                    color = perlin_noise.get(tile_x + x, tile_y - y) * 255
                    color = (color, color, color)
                rect = pygame.Rect(screen_width * 0.5 + tile_x * TILE_SIZE,
                                   screen_height * 0.5 + tile_y * TILE_SIZE,
                                   TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)
        rendered_text = font.render(f"X = {x}   Y = {y}", True, "white")
        screen.blit(rendered_text, (screen_width * 0.5 - rendered_text.get_width() * 0.5,
                                    screen_height * 0.5 + TILES_TALL * TILE_SIZE + TEXT_SEPARATION))
        rendered_text = font.render(f"SEED = {perlin_noise.seed}", True, "white")
        screen.blit(rendered_text, (screen_width * 0.5 - rendered_text.get_width() * 0.5,
                                    screen_height * 0.5 - TILES_TALL * TILE_SIZE - rendered_text.get_height() - TEXT_SEPARATION))
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
