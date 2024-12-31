import math

import pygame


def generate_shape(obj, camera):
    image = pygame.Surface(obj.size, pygame.SRCALPHA)

    if obj.shape == 'rect':
        pygame.draw.rect(image, obj.color, image.get_rect())
    elif obj.shape == 'circle':
        pygame.draw.circle(image, obj.color, (obj.size[0] // 2, obj.size[1] // 2), obj.size[0] / 2)

    if obj.angle != 0 and obj.shape != 'circle':
        image = pygame.transform.rotate(image, -math.degrees(obj.angle))
        rect = image.get_rect()

        obj_obj_vect = pygame.math.Vector2(obj.obj.pos[0] + obj.obj.size[0] / 2, obj.obj.pos[1] + obj.obj.size[1] / 2)
        obj_vect = pygame.math.Vector2(obj.pos[0] + obj.size[0] / 2, obj.pos[1] + obj.size[1] / 2)
        new_pos = (obj_vect - obj_obj_vect).rotate(math.degrees(obj.angle)) + obj_obj_vect
        rect.center = new_pos  # noqa
        pos = rect.topleft
    else:
        pos = obj.pos

    pos = (pos[0] - camera.pos[0], pos[1] - camera.pos[1])

    return image, pos
