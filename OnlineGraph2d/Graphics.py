import pygame


def generate_shape(obj):
    image = pygame.Surface(obj.size, pygame.SRCALPHA)

    if obj.shape == 'rect':
        pygame.draw.rect(image, obj.color, image.get_rect())
    elif obj.shape == 'circle':
        pygame.draw.circle(image, obj.color, (obj.size[0] // 2, obj.size[1] // 2), obj.size[0] / 2)

    return image
