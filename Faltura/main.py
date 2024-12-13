from OnlineGraph2d.Network import Server, Client, get_ip
from OnlineGraph2d.Graphics import generate_shape
from OnlineGraph2d.Physics import GameObject, Camera

import pygame
import math

host_type = input('who are you? [server/client]: ').lower()
port = 5555

if host_type == 'server':
    print('\nsetting up server...')

    server_ip = get_ip()

    if not server_ip:
        print('error: failed to get the ip address')
    else:
        print(f'server started: the server ip is: {server_ip}')

        server = Server(server_ip=server_ip, port=port)

elif host_type == 'client':
    server_ip = input('\nenter the server ip: ')

    client = Client(server_ip=server_ip, port=port)

else:
    print('\nhost type not valid')
    exit()

host = server if host_type == 'server' else client  # noqa

pygame.init()

screen_size = (1600, 900)
FPS = 120
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption(host_type + ('_' + str(host.client_number) if host_type == 'client' else ''))
clock = pygame.time.Clock()
text_font = pygame.font.SysFont('dejavusansmono', 15)

close = False
objects = {}
colors_rgb = [
    (0, 255, 0),  # green
    (0, 0, 255),  # blue
    (255, 255, 0),  # yellow
    (255, 0, 0),  # red
    (255, 100, 0),  # orange
    (128, 0, 128),  # purple
    (165, 42, 42),  # brown
    (255, 255, 255)  # white
]
grappling_gun_target = None

game_map = [
    GameObject(pos=(0, screen_size[1] - 100), angle=0, size=(screen_size[0] - 500, 100), shape='rect', color=(255, 255, 255), static=True),
    GameObject(pos=(200, screen_size[1] - 150), angle=0, size=(50, 50), shape='rect', color=(255, 255, 255), static=True),
    GameObject(pos=(250, screen_size[1] - 250), angle=0, size=(50, 150), shape='rect', color=(255, 255, 255), static=True),
    GameObject(pos=(300, screen_size[1] - 350), angle=0, size=(50, 250), shape='rect', color=(255, 255, 255), static=True),
    GameObject(pos=(600, screen_size[1] - 600), angle=0, size=(50, 50), shape='rect', color=(255, 255, 255), static=True),
    GameObject(pos=(900, screen_size[1] - 600), angle=0, size=(50, 50), shape='rect', color=(255, 255, 255), static=True)
]
game_map_collision = [(map_obj.pos, map_obj.size) for map_obj in game_map]

player = GameObject(pos=[100, 100], angle=0, size=(30, 30), shape='circle', color=colors_rgb[host.client_number], static=False, gravity=0.1, friction=0.2, air_friction=0.05, collision=game_map_collision)
camera = Camera(obj=player, screen_size=screen_size)

if host_type == 'server':
    local_objects = [player]
    objects = {host.client_number: local_objects}
else:
    local_objects = [player]

while not close:
    # clear display and show fps
    display.fill((0, 0, 0))
    display.blit(text_font.render(f'FPS: {clock.get_fps():.1f} / {FPS}', 1, (255, 255, 255)), (screen_size[0] - 170, 25))

    # check if the window is closed
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            close = True

        # check if the mouse button is pressed for the grappling gun
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            grappling_gun_target = (mouse_pos[0] + camera.pos[0], mouse_pos[1] + camera.pos[1])

    # grappling gun
    if grappling_gun_target is not None:
        grappling_gun_target_ok = player.grappling_gun_check(mouse_pos=grappling_gun_target)
        if not grappling_gun_target_ok:
            grappling_gun_target = None
            player.rope = None
        else:
            if not pygame.mouse.get_pressed()[0]:
                # release grappling gun
                if player.rope:
                    #player.force(force=15, angle=math.degrees(player.rope.angle))
                    grappling_gun_target = None
                    player.rope = None
            else:
                player.grappling_gun(mouse_pos=grappling_gun_target)

    # check keyboard keys for movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LSHIFT]:
        run = True
    else:
        run = False

    if keys[pygame.K_w] and player.can_jump:
        player.axis_force(force=-8, axis=1)
    if keys[pygame.K_d]:
        player.axis_force(force=1, axis=0, limit=5) if run else player.axis_force(force=1, axis=0, limit=3)
    if keys[pygame.K_a]:
        player.axis_force(force=-1, axis=0, limit=-5) if run else player.axis_force(force=-1, axis=0, limit=-3)

    # transfer data
    if host_type == 'server':
        other_data = host.send(objects)
        objects = {host.client_number: local_objects} | other_data
        pass
    else:
        objects = host.send(local_objects)
        objects = {host_number: host_objs for host_number, host_objs in objects.items() if host_number != host.client_number}

    # update player collision
    player.collision = game_map_collision + [(obj.pos, obj.size) for host_number, host_objs in objects.items() for obj in host_objs if host_number != host.client_number]

    # compute positions
    player.update()
    camera.update()
    player.render_force(display=display, camera=camera, double=False)

    # display objects
    for map_obj in game_map:
        display.blit(generate_shape(map_obj), (map_obj.pos[0] - camera.pos[0], map_obj.pos[1] - camera.pos[1]))

    if host_type == 'client':
        for game_obj in local_objects:
            if game_obj.rope:
                game_obj.rope.blit(display=display, camera=camera)
            display.blit(generate_shape(game_obj), (game_obj.pos[0] - camera.pos[0], game_obj.pos[1] - camera.pos[1]))

    for host_objs in objects.values():
        for game_obj in host_objs:
            if game_obj.rope:
                game_obj.rope.blit(display=display, camera=camera)
            display.blit(generate_shape(game_obj), (game_obj.pos[0] - camera.pos[0], game_obj.pos[1] - camera.pos[1]))

    # render
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
