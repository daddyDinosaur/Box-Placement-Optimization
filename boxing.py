import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
from OpenGL.GLUT import glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18

def draw_box(x, y, z, width, height, depth, solid=False):
    vertices = [
        [x, y, z],
        [x + width, y, z],
        [x + width, y + height, z],
        [x, y + height, z],
        [x, y, z + depth],
        [x + width, y, z + depth],
        [x + width, y + height, z + depth],
        [x, y + height, z + depth],
    ]
    edges = (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    )
    faces = (
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 3, 7, 4),
    )

    if solid:
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
    else:
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

def draw_container():
    glColor3f(1, 1, 1)
    draw_box(0, 0, 0, 10, 10, 10)

def draw_boxes(boxes, solid_states):
    for (box, color), solid in zip(boxes, solid_states):
        glColor3f(color[0], color[1], color[2])
        draw_box(*box, solid)

def generate_distinct_colors(n):
    hues = np.linspace(0, 1, n, endpoint=False)
    random.shuffle(hues)
    colors = [hsv_to_rgb(h, 0.8, 0.8) for h in hues]
    return colors

def hsv_to_rgb(h, s, v):
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i = i % 6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)

def is_space_available(placed_boxes, box, position):
    x, y, z, w, h, d = position
    for pb in placed_boxes:
        px, py, pz, pw, ph, pd = pb
        if not (x + w <= px or x >= px + pw or
                y + h <= py or y >= py + ph or
                z + d <= pz or z >= pz + pd):
            return False
    return True

def pack_boxes(container_width, container_height, container_depth, boxes):
    positions = []
    placed_boxes = []

    for box in boxes:
        box_width, box_height, box_depth = box
        placed = False

        for x in range(container_width - box_width + 1):
            for y in range(container_height - box_height + 1):
                for z in range(container_depth - box_depth + 1):
                    position = (x, y, z, box_width, box_height, box_depth)
                    if is_space_available(placed_boxes, box, position):
                        positions.append(position)
                        placed_boxes.append(position)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            raise ValueError("Box does not fit in container")

    return positions

def render_text(text, font, color, x, y):
    text_surface = font.render(text, True, color, (0, 0, 0))
    text_data = pygame.image.tostring(text_surface, 'RGBA', True)
    glRasterPos2f(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def draw_color_square(color, x, y, size=20):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + size, y)
    glVertex2f(x + size, y + size)
    glVertex2f(x, y + size)
    glEnd()

def calculate_box_space(box):
    return box[3] * box[4] * box[5]

def render_space_info(font, total_space, used_space, display_width):
    total_text = f"Total Space: {total_space}"
    used_text = f"Used Space: {used_space}"
    text_width = max(font.size(total_text)[0], font.size(used_text)[0])
    x = (display_width - text_width) / 2
    render_text(total_text, font, (255, 255, 255), x, 20)
    render_text(used_text, font, (255, 255, 255), x, 40)

def main():
    pygame.init()
    display = (1366, 768)
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(-5, -5, -30)

    container_width = 10
    container_height = 10
    container_depth = 10

    boxes = [
        (2, 2, 2),
        (2, 5, 2),
        (7, 2, 3),
        (8, 7, 6),
        (4, 2, 1)
    ]

    boxes = sorted(boxes, key=lambda b: b[0] * b[1] * b[2], reverse=True)

    packed_boxes = pack_boxes(container_width, container_height, container_depth, boxes)
    colors = generate_distinct_colors(len(boxes))
    packed_boxes_with_colors = list(zip(packed_boxes, colors))

    solid_states = [False] * len(packed_boxes_with_colors)

    font = pygame.font.SysFont('Arial', 18)
    rotate_x, rotate_y = 0, 0
    mouse_down = False
    last_mouse_pos = None

    button_size = 20
    button_positions = [(3, display[1] - 40 - i * 40) for i in range(len(packed_boxes_with_colors))]

    def is_button_clicked(button_pos, mouse_pos):
        x, y = button_pos
        mx, my = mouse_pos
        return x <= mx <= x + button_size and y <= my <= y + button_size

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_down = True
                    last_mouse_pos = pygame.mouse.get_pos()
                    mouse_x, mouse_y = last_mouse_pos
                    for i, button_pos in enumerate(button_positions):
                        if is_button_clicked(button_pos, (mouse_x, display[1] - mouse_y)):
                            solid_states[i] = not solid_states[i]
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            elif event.type == pygame.MOUSEMOTION:
                if mouse_down:
                    current_mouse_pos = pygame.mouse.get_pos()
                    dx = current_mouse_pos[0] - last_mouse_pos[0]
                    dy = current_mouse_pos[1] - last_mouse_pos[1]
                    rotate_x += dy
                    rotate_y += dx
                    last_mouse_pos = current_mouse_pos

        total_space = container_width * container_height * container_depth
        used_space = sum(box[3] * box[4] * box[5] for box in packed_boxes)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()

        glRotatef(rotate_x, 1, 0, 0)
        glRotatef(rotate_y, 0, 1, 0)

        glEnable(GL_DEPTH_TEST)
        draw_container()
        draw_boxes(packed_boxes_with_colors, solid_states)

        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, display[0], 0, display[1])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        for i, ((_, color), solid) in enumerate(zip(packed_boxes_with_colors, solid_states)):
            render_text(f'Box {i+1} | Size: {calculate_box_space(_)}', font, (255, 255, 255), 24, display[1] - 40 - i * 40)
            draw_color_square(color, 24 + len(f'Box {i+1} | Size: {calculate_box_space(_)}') * 8.5, display[1] - 40 - i * 40, 20)
            if solid:
                draw_color_square((0, 1, 0), *button_positions[i]) #green
            else:
                draw_color_square((1, 0, 0), *button_positions[i]) #red
        
        render_space_info(font, total_space, used_space, display[0])

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == "__main__":
    main()