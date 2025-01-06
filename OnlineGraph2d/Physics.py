import math
from dataclasses import dataclass

import pygame


@dataclass
class Settings:
    gravity: float = 0.1
    ground_friction: float = 0.2
    air_friction: float = 0.02
    swing_friction: float = 0.002


class Object:
    def __init__(self, pos, angle, size, shape, color, layer, centered=False, show=True):
        self.pos, self.angle, self.size = pos, angle, size
        self.shape, self.color, self.layer, self.centered, self.show = shape, color, layer, centered, show


class GameObject(Object):
    def __init__(self, static, mass=None, collision=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.static = static
        self.rope = None

        if not self.static:
            self.mass = mass
            self.collision = collision
            self.touching, self.can_jump = False, False

            self.vel = [0, 0]
            self.acc = [0, Settings.gravity]

            self.ang_vel = 0
            self.ang_acc = 0

    def update(self):
        if not self.static:
            # add acceleration
            self.vel[0] += self.acc[0]
            self.vel[1] += self.acc[1]

            # compute rope
            if self.rope and self.rope.swing and not self.can_jump:
                if self.rope.init_vel is not None:
                    self.ang_vel = -(self.rope.init_vel[0] * math.cos(self.rope.angle) + self.rope.init_vel[1] * math.sin(self.rope.angle)) / self.rope.length
                    self.rope.init_vel = None

                self.rope.angle = (self.rope.angle + math.pi) % (2 * math.pi) - math.pi

                self.ang_acc = (self.acc[0] * math.cos(self.rope.angle) - self.acc[1] * math.sin(self.rope.angle)) / self.rope.length
                self.ang_vel += self.ang_acc
                self.ang_vel *= (1 - Settings.swing_friction)
                self.rope.angle += self.ang_vel

                self.vel[0] = self.rope.pivot[0] + self.rope.length * math.sin(self.rope.angle) - self.pos[0]
                self.vel[1] = self.rope.pivot[1] + self.rope.length * math.cos(self.rope.angle) - self.pos[1]
            else:
                self.ang_vel = 0
                self.ang_acc = 0

            # set maximum velocity
            if self.vel[0] >= 0:
                self.vel[0] = min(self.vel[0], 10)
            else:
                self.vel[0] = max(self.vel[0], -10)

            if self.vel[1] >= 0:
                self.vel[1] = min(self.vel[1], 10)
            else:
                self.vel[1] = max(self.vel[1], -10)

            # friction
            if not (self.rope and self.rope.swing and not self.can_jump):
                if self.touching:
                    current_friction = Settings.ground_friction * self.mass
                else:
                    current_friction = Settings.air_friction * self.mass

                if abs(self.vel[0]) <= current_friction:
                    self.vel[0] = 0
                else:
                    if self.vel[0] > 0:
                        self.vel[0] -= current_friction
                    elif self.vel[0] < 0:
                        self.vel[0] += current_friction

            x_edge = (self.pos[0], self.pos[0] + self.size[0])
            y_edge = (self.pos[1], self.pos[1] + self.size[1])

            # check game map collision
            self.touching, self.can_jump = False, False

            for map_obj in self.collision:  # map_obj is [pos[x, y], size[x, y]] of type tuple[tuple[int, int], tuple[int, int]]
                obj_x_edge = (map_obj[0][0], map_obj[0][0] + map_obj[1][0])
                obj_y_edge = (map_obj[0][1], map_obj[0][1] + map_obj[1][1])

                if y_edge[0] < obj_y_edge[1] and y_edge[1] > obj_y_edge[0]:  # they are aligned on the y_axis
                    if (self.vel[0] > 0 and x_edge[1] < obj_x_edge[0] < (x_edge[1] + self.vel[0])) or (self.vel[0] < 0 and x_edge[0] > obj_x_edge[1] > (x_edge[0] + self.vel[0])):  # they will collide on the x-axis
                        self.touching = True
                        self.vel[0] = 0

                if x_edge[0] < obj_x_edge[1] and x_edge[1] > obj_x_edge[0]:  # they are aligned on the y_axis
                    if (self.vel[1] > 0 and y_edge[1] < obj_y_edge[0] < (y_edge[1] + self.vel[1])) or (self.vel[1] < 0 and y_edge[0] > obj_y_edge[1] > (y_edge[0] + self.vel[1])):  # they will collide on the y-axis
                        self.touching = True
                        if self.vel[1] > 0:  # if it is above the object (it is going from top to bottom) it can jump
                            self.can_jump = True
                        self.vel[1] = 0

            self.pos[0] += self.vel[0]
            self.pos[1] += self.vel[1]
        else:
            raise Exception("'update' function was called but object is static")

    def apply_vel(self, vel, angle):
        if vel is not None and angle is not None:
            vel_x = vel * math.cos(angle)
            vel_y = vel * math.sin(angle)

            self.vel[0] += vel_x
            self.vel[1] += vel_y

            return [vel_x, vel_y]

        elif vel:
            raise Exception("'vel' was given but 'angle' was missing")
        elif angle:
            raise Exception("'angle' was given but 'vel' was missing")

    def apply_axis_vel(self, vel, axis, limit=None):
        if axis not in {0, 1}:
            raise ValueError("'axis' must be 0 or 1")

        if limit is None:
            self.vel[axis] += vel
        elif (0 <= vel < limit) or (0 >= vel > limit):
            # apply force within the limit
            if vel > 0:
                self.vel[axis] += min(vel, limit - self.vel[axis])
            elif vel < 0:
                self.vel[axis] += max(vel, limit - self.vel[axis])

    def render_vel(self, display, camera, double=False):
        central_pos = (self.pos[0] + self.size[0] / 2 - camera.pos[0], self.pos[1] + self.size[1] / 2 - camera.pos[1])
        if double:
            pygame.draw.line(display, (255, 0, 0), central_pos, (central_pos[0] + self.vel[0] * 10, central_pos[1]), width=3)
            pygame.draw.line(display, (255, 0, 0), central_pos, (central_pos[0], central_pos[1] + self.vel[1] * 10), width=3)
        else:
            pygame.draw.line(display, (255, 0, 0), central_pos, (central_pos[0] + self.vel[0] * 10, central_pos[1] + self.vel[1] * 10), width=3)


class FollowerObject(Object):
    def __init__(self, obj, rel_pos, *args, **kwargs):
        super().__init__(pos=[0, 0], *args, **kwargs)
        self.obj = obj
        self.rel_pos = rel_pos  # relative position

        self.update()

    def update(self):
        self.pos = [self.obj.pos[0] + self.rel_pos[0], self.obj.pos[1] + self.rel_pos[1]]


class Camera:
    def __init__(self, obj, screen_size):
        self.obj, self.screen_size = obj, screen_size
        self.pos = [0, 0]
        self.update()

    def update(self):
        self.pos[0] = self.obj.pos[0] - self.screen_size[0] / 2
        self.pos[1] = self.obj.pos[1] - self.screen_size[1] / 2


class Rope:
    def __init__(self, obj, pivot, init_vel, swing, color, show=True):
        self.obj, self.pivot, self.init_vel = obj, pivot, init_vel
        self.swing = swing
        self.color, self.show = color, show
        self.length = math.sqrt((self.obj.pos[0] + self.obj.size[0] / 2 - self.pivot[0]) ** 2 + (self.obj.pos[1] + self.obj.size[1] / 2 - self.pivot[1]) ** 2)
        self.angle = -math.atan2(self.pivot[1] - (self.obj.pos[1] + self.obj.size[1] / 2), self.pivot[0] - (self.obj.pos[0] + self.obj.size[0] / 2)) - math.pi / 2  # uses pendulum compatible angle system

    def blit(self, display, camera):
        pygame.draw.line(display, self.color, (self.obj.pos[0] + self.obj.size[0] / 2 - camera.pos[0], self.obj.pos[1] + self.obj.size[1] / 2 - camera.pos[1]), (self.pivot[0] - camera.pos[0], self.pivot[1] - camera.pos[1]), width=3)
