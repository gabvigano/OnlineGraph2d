import math

import pygame

from OnlineGraph2d.Graphics import generate_shape
from OnlineGraph2d.Network import Server, Client, get_ip
from OnlineGraph2d.Physics import Object, GameObject, FollowerObject, Camera, Rope

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
]
variables = {}
connection_number = 0
weapons = ['grappling_gun', 'gun']
weapon = 0
mouse_pos = None
grappling_gun = None
grappling_gun_swing = False


class AimDot(Object):
    def __init__(self, collision, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collision = collision

        self.mouse_pos = [0, 0]
        self.weapon = None

        self.grappling_gun = None
        self.bullets = []

    def update(self):
        if weapon == 0:
            self.show = True
        else:
            self.show = False

        if not self.grappling_gun and weapon == 0:
            best_pos = None
            min_dist = math.inf

            for map_obj in self.collision:
                obj_x_edge = (map_obj[0][0], map_obj[0][0] + map_obj[1][0])
                obj_y_edge = (map_obj[0][1], map_obj[0][1] + map_obj[1][1])

                if obj_x_edge[0] <= self.mouse_pos[0] <= obj_x_edge[1] and obj_y_edge[0] <= self.mouse_pos[1] <= obj_y_edge[1]:  # if the mouse is inside the object keep the mouse position
                    self.pos = self.mouse_pos
                    return

                current_x = max(obj_x_edge[0], min(self.mouse_pos[0], obj_x_edge[1]))
                current_y = max(obj_y_edge[0], min(self.mouse_pos[1], obj_y_edge[1]))
                current_pos = (current_x, current_y)

                current_dist = (current_pos[0] - self.mouse_pos[0]) ** 2 + (current_pos[1] - self.mouse_pos[1]) ** 2

                if current_dist < min_dist:
                    min_dist = current_dist
                    best_pos = current_pos

            self.pos = best_pos

        # delete far bullets
        self.bullets = [bullet for bullet in self.bullets if abs(bullet.pos[0]) < 3000 and abs(bullet.pos[1]) < 2000]

        # delete old bullets if there are too much
        max_bullets = math.floor(22 / connection_number)  # here 22 is the number of bullets the current buffer size of Network.py supports; in the future, if optimization is implemented, update this number
        self.bullets = self.bullets[-max_bullets:]


game_map = [
    GameObject(static=True, pos=[0, 500], angle=0, size=(300, 50), shape='rect', color=(255, 255, 255), layer=0),
    GameObject(static=True, pos=[450, 0], angle=0, size=(50, 50), shape='rect', color=(255, 255, 255), layer=0),
    GameObject(static=True, pos=[650, 500], angle=0, size=(300, 50), shape='rect', color=(255, 255, 255), layer=0),
    GameObject(static=True, pos=[0, 450], angle=0, size=(50, 50), shape='rect', color=(255, 255, 255), layer=0)
]
game_map_collision = [(map_obj.pos, map_obj.size) for map_obj in game_map]

player = GameObject(static=False, pos=[100, 100], angle=0, size=(20, 20), shape='circle', color=colors_rgb[host.client_number], layer=2, mass=1, collision=game_map_collision)
camera = Camera(obj=player, rel_pos=[0, -100], screen_size=screen_size)
gun = FollowerObject(obj=player, rel_pos=[player.size[0] - 5, player.size[1] / 2 - 2], angle=0, size=(10, 4), shape='rect', color=(100, 100, 100), layer=5)
aim_dot = AimDot(pos=[100, 100], angle=0, size=(7, 7), shape='circle', color=(255, 0, 0), layer=6, collision=game_map_collision, centered=True)

global_objects = [player, gun]
local_objects = [aim_dot]
if host_type == 'server':
    objects = {host.client_number: global_objects}  # initialize server's objects to have data to share at the first frame

while not close:
    # clear display
    display.fill((0, 0, 0))

    # mouse input
    for event in pygame.event.get():
        # check if the window is closed
        if event.type == pygame.QUIT:
            close = True

        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEWHEEL:
            weapon += event.y

        if event.type == pygame.MOUSEBUTTONDOWN:
            if weapon == 0:
                if event.button == 1:
                    grappling_gun = True
                    grappling_gun_swing = True
                elif event.button == 3:
                    grappling_gun = True
                    grappling_gun_swing = False
            elif weapon == 1 and event.button == 1:
                aim_dot.bullets.append(GameObject(static=False, pos=gun.pos, angle=0, size=(5, 5), shape='circle', color=(255, 255, 255), layer=10, mass=0.1, collision=game_map_collision))
                aim_dot.bullets[-1].apply_vel(vel=25, angle=gun.angle)

    # keyboard input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LSHIFT]:
        run = True
    else:
        run = False

    if keys[pygame.K_w] and player.can_jump:
        player.apply_axis_vel(vel=-12, axis=1)
    if keys[pygame.K_d]:
        player.apply_axis_vel(vel=1, axis=0, limit=10) if run else player.apply_axis_vel(vel=1, axis=0, limit=5)
    if keys[pygame.K_a]:
        player.apply_axis_vel(vel=-1, axis=0, limit=-10) if run else player.apply_axis_vel(vel=-1, axis=0, limit=-5)
    if keys[pygame.K_r]:
        player.pos = [100, 100]
        player.vel = [0, 0]
        aim_dot.bullets = []

    # normalize weapon
    weapon %= len(weapons)

    # update mouse position based on the camera movement
    mouse_camera_pos = (mouse_pos[0] + camera.pos[0], mouse_pos[1] + camera.pos[1])

    # update aim_dot mouse position, weapon and grappling gun
    aim_dot.mouse_pos = mouse_camera_pos
    aim_dot.weapon = weapon
    aim_dot.grappling_gun = grappling_gun

    # grappling gun
    if grappling_gun is not None:
        if player.rope and ((not pygame.mouse.get_pressed()[0] and player.rope.swing) or (not pygame.mouse.get_pressed()[2] and not player.rope.swing)):
            # release grappling gun
            if not player.rope.swing and player.rope.ready:
                player.apply_vel(vel=20, angle=-player.rope.angle - math.pi / 2)
            grappling_gun = None
            player.rope = None
        else:
            if not player.rope:
                # create grappling gun
                player.rope = Rope(obj=player, pivot=aim_dot.pos, init_vel=player.vel, swing=grappling_gun_swing, color=player.color)

    if player.can_jump and player.rope and player.rope.swing:
        grappling_gun = None
        player.rope = None

    # transfer data
    if host_type == 'server':
        other_data = host.send(objects)
        objects = {host.client_number: global_objects + aim_dot.bullets} | other_data  # update server's objects
        connection_number = len(list(objects.keys()))
    else:
        objects = host.send(global_objects + aim_dot.bullets)
        objects = {client_number: host_objs for client_number, host_objs in objects.items() if client_number != host.client_number}
        connection_number = len(list(objects.keys())) + 1  # + 1 because clients exclude their own content (see the above line)

    # update objects collision
    player.collision = game_map_collision + [(obj.pos, obj.size) for client_number, host_objs in objects.items() for obj in host_objs if obj is not player]
    for bullet in aim_dot.bullets:
        bullet.collision = game_map_collision + [(obj.pos, obj.size) for client_number, host_objs in objects.items() for obj in host_objs if obj is not bullet]

    # compute positions
    for game_obj in global_objects + local_objects + aim_dot.bullets:
        try:
            game_obj.update()
        except AttributeError:
            pass

    camera.update()

    if not player.rope:
        gun.angle = math.atan2(mouse_camera_pos[1] - gun.pos[1] + gun.size[1] / 2, mouse_camera_pos[0] - gun.pos[0] + gun.size[0] / 2)  # noqa
    else:
        gun.angle = math.atan2(aim_dot.pos[1] - gun.pos[1] + gun.size[1] / 2, aim_dot.pos[0] - gun.pos[0] + gun.size[0] / 2)  # noqa

    # player.render_vel(display=display, camera=camera, double=False)

    # display objects
    render_objs = []
    render_objs.extend(game_map)
    render_objs.extend(local_objects)
    if host_type == 'client':
        render_objs.extend(global_objects + aim_dot.bullets)
    for client_objs in objects.values():
        render_objs.extend(client_objs)

    render_objs.sort(key=lambda obj: obj.layer)  # sort objects by layer

    for obj in render_objs:
        try:
            if obj.rope and obj.rope.show:
                obj.rope.blit(display=display, camera=camera)
        except AttributeError:
            pass
        if obj.show:
            display.blit(*generate_shape(obj=obj, camera=camera))

    # display variables and fps
    try:
        variables = {
            'weapon': weapons[weapon],
            'bullets': len(aim_dot.bullets)
        }
    except IndexError:
        pass

    y = 25
    for name, value in variables.items():
        if '__separator__' in name:
            display.blit(text_font.render('_' * value, 1, (255, 255, 255)), (25, y))  # noqa
        else:
            try:
                display.blit(text_font.render(f'{name}: {value}', 1, (255, 255, 255)), (25, y))
            except Exception as e:  # noqa
                display.blit(text_font.render(f'{name}: None', 1, (255, 255, 255)), (25, y))
                print(e)
        y += 25

    display.blit(text_font.render(f'FPS: {clock.get_fps():.1f} / {FPS}', 1, (255, 255, 255)), (screen_size[0] - 170, 25))

    # render
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
