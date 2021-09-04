import math
import random
import sys

from PIL import Image, ImageDraw

try:
    from scipy.spatial import cKDTree as KDTree
    import numpy as np
    IMPORTED_SCIPY = True
except ImportError:
    IMPORTED_SCIPY = False

BACKGROUND = (255, 255, 255)
TOTAL_CIRCLES = 1500

color = lambda c: ((c >> 16) & 255, (c >> 8) & 255, c & 255)

COLORS_ON = [
    color(0xF9BB82), color(0xEBA170), color(0xFCCD84)
]
COLORS_OFF = [
    color(0x9CA594), color(0xACB4A5), color(0xBBB964),
    color(0xD7DAAA), color(0xE5D57D), color(0xD1D6AF)
]


def generate_circle(image_width, image_height, min_diameter, max_diameter):
    radius = random.triangular(min_diameter, max_diameter,
                               max_diameter * 0.8 + min_diameter * 0.2) / 2

    angle = random.uniform(0, math.pi * 2)
    distance_from_center = random.uniform(0, image_width * 0.48 - radius)
    x = image_width  * 0.5 + math.cos(angle) * distance_from_center
    y = image_height * 0.5 + math.sin(angle) * distance_from_center

    return x, y, radius


def overlaps_motive(image, circle):
    x, y, r = unpack_circle_tuple(circle)
    points_x = [x, x, x, x-r, x+r, x-r*0.93, x-r*0.93, x+r*0.93, x+r*0.93]
    points_y = [y, y-r, y+r, y, y, y+r*0.93, y-r*0.93, y+r*0.93, y-r*0.93]

    for xy in zip(points_x, points_y):
        if image.getpixel(xy)[:3] != BACKGROUND:
            return True

    return False


def circle_intersection(circle_1, circle_2):
    x1, y1, r1 = unpack_circle_tuple(circle_1)
    x2, y2, r2 = unpack_circle_tuple(circle_2)
    return (x2 - x1)**2 + (y2 - y1)**2 < (r2 + r1)**2


def circle_draw(draw_image, image, circle):
    x, y, r = unpack_circle_tuple(circle)
    fill_colors = COLORS_ON if overlaps_motive(image, circle) else COLORS_OFF
    fill_color = random.choice(fill_colors)

    draw_image.ellipse((x - r, y - r, x + r, y + r),
                       fill=fill_color,
                       outline=fill_color)

def unpack_circle_tuple(circle):
    return circle[0], circle[1], circle[2]

def open_motive_image():
    if len(sys.argv) <= 1:
        return Image.open('example.png')
    return Image.open(sys.argv[1])

def main():
    image = open_motive_image()
    canvas = Image.new('RGB', image.size, BACKGROUND)
    draw_image = ImageDraw.Draw(canvas)

    width, height = image.size

    min_diameter = (width + height) / 200
    max_diameter = (width + height) / 75

    circle = generate_circle(width, height, min_diameter, max_diameter)
    circle_draw(draw_image, image, circle)
    circles = [circle]

    try:
        for i in range(TOTAL_CIRCLES-1):
            tries = 0
            current_max_diameter = max_diameter
            if IMPORTED_SCIPY:
                kdtree = KDTree([(x, y) for (x, y, _) in circles])
                while True:
                    circle = generate_circle(width, height, min_diameter, current_max_diameter)
                    elements, indexes = kdtree.query([(circle[0], circle[1])], k=12)
                    for element, index in zip(elements[0], indexes[0]):
                        if not np.isinf(element) and circle_intersection(circle, circles[index]):
                            break
                    else:
                        break
                    tries += 1
                    if current_max_diameter > min_diameter+1:
                        current_max_diameter -= 1
            else:
                while any(circle_intersection(circle, circle2) for circle2 in circles):
                    tries += 1
                    circle = generate_circle(width, height, min_diameter, max_diameter)
                    if current_max_diameter > min_diameter+1:
                        current_max_diameter -= 1

            print('Circle {}/{}\n\t{} tries'.format(i, TOTAL_CIRCLES, tries))

            circle_draw(draw_image, image, circle)
            circles.append(circle)
    except (KeyboardInterrupt, SystemExit):
        pass

    canvas.show()

if __name__ == '__main__':
    main()
