import math

import pygame


class GameObject:
    def __init__(self, pos, angle, size, shape, color, static, gravity=None, friction=None, air_friction=None, collision=None):
        self.pos, self.angle = pos, angle
        self.size, self.shape, self.color = size, shape, color
        self.static = static
        self.rope = None

        if not self.static:
            self.perm_force, self.temp_force = [0, 0], [0, 0]  # permanent and temporary forces sums
            self.gravity, self.friction, self.air_friction = gravity, friction, air_friction
            self.collision = collision
            self.touching, self.can_jump = False, False

    def update(self):
        if not self.static:  # it's not the game map
            # reset temp_force
            self.temp_force = [0, 0]

            # update rope
            if self.rope:
                self.rope.update()

            # add gravity
            self.perm_force[1] += self.gravity

            # rope swing
            if self.rope:
                if self.rope.pivot[1] <= self.pos[1]:
                    tension = math.sqrt(self.perm_force[0] ** 2 + self.perm_force[1] ** 2)
                    swing_forces = self.force(force=tension, angle=math.degrees(self.rope.angle))
                    self.temp_force[0] += swing_forces[0]
                    self.temp_force[1] += swing_forces[1]

            # set maximum force
            if self.perm_force[0] >= 0:
                self.perm_force[0] = min(self.perm_force[0], 10)
            else:
                self.perm_force[0] = max(self.perm_force[0], -10)

            if self.perm_force[1] >= 0:
                self.perm_force[1] = min(self.perm_force[1], 10)
            else:
                self.perm_force[1] = max(self.perm_force[1], -10)

            # friction
            if not (self.rope and not self.touching):
                if abs(self.perm_force[0]) <= self.friction:
                    self.perm_force[0] = 0
                else:
                    if self.touching:
                        current_friction = self.friction
                    else:
                        current_friction = self.air_friction

                    if self.perm_force[0] > 0:
                        self.perm_force[0] -= current_friction
                    elif self.perm_force[0] < 0:
                        self.perm_force[0] += current_friction

            x_edge = (self.pos[0], self.pos[0] + self.size[0])
            y_edge = (self.pos[1], self.pos[1] + self.size[1])

            # check game map collision
            self.touching, self.can_jump = False, False

            no_x_perm_force, no_y_perm_force = False, False
            for map_obj in self.collision:
                obj_x_edge = (map_obj[0][0], map_obj[0][0] + map_obj[1][0])
                obj_y_edge = (map_obj[0][1], map_obj[0][1] + map_obj[1][1])

                if y_edge[0] < obj_y_edge[1] and y_edge[1] > obj_y_edge[0]:  # they are aligned on the y_axis
                    if (self.perm_force[0] > 0 and x_edge[1] < obj_x_edge[0] < (x_edge[1] + self.perm_force[0])) or (self.perm_force[0] < 0 and x_edge[0] > obj_x_edge[1] > (x_edge[0] + self.perm_force[0])):  # it will collide on the x-axis
                        no_x_perm_force = True
                        self.touching = True
                        self.perm_force[0] = 0

                if x_edge[0] < obj_x_edge[1] and x_edge[1] > obj_x_edge[0]:  # they are aligned on the y_axis
                    if (self.perm_force[1] > 0 and y_edge[1] < obj_y_edge[0] < (y_edge[1] + self.perm_force[1])) or (self.perm_force[1] < 0 and y_edge[0] > obj_y_edge[1] > (y_edge[0] + self.perm_force[1])):  # it will collide on the y-axis
                        no_y_perm_force = True
                        self.touching = True
                        if self.perm_force[1] > 0:  # if it above the object it can jump
                            self.can_jump = True
                        self.perm_force[1] = 0

            if not no_x_perm_force:
                self.pos[0] += self.perm_force[0]
            if not no_y_perm_force:
                self.pos[1] += self.perm_force[1]

            self.perm_force[0] -= self.temp_force[0]
            self.perm_force[1] -= self.temp_force[1]
        else:
            raise Exception("'update' function was called but object is static")

    def force(self, force, angle):
        # compute external force
        if force is not None and angle is not None:
            angle_radians = math.radians(angle)

            force_x = force * math.cos(angle_radians)
            force_y = force * math.sin(angle_radians)

            self.perm_force[0] += force_x
            self.perm_force[1] += force_y

            return [force_x, force_y]

        elif force:
            raise Exception("'force' was given but 'angle' was missing")
        elif angle:
            raise Exception("'angle' was given but 'force' was missing")

    def axis_force(self, force, axis, limit=None):  # axis: 0 = x, 1 = y
        if axis not in {0, 1}:
            raise ValueError("'axis' must be 0 or 1")

        if limit is None:
            self.perm_force[axis] += force
        elif (0 <= force < limit) or (0 >= force > limit):
            # apply force within the limit
            if force > 0:
                self.perm_force[axis] += min(force, limit - self.perm_force[axis])
            elif force < 0:
                self.perm_force[axis] += max(force, limit - self.perm_force[axis])

    def grappling_gun_check(self, mouse_pos):
        for map_obj in self.collision:
            obj_x_edge = (map_obj[0][0], map_obj[0][0] + map_obj[1][0])
            obj_y_edge = (map_obj[0][1], map_obj[0][1] + map_obj[1][1])

            if obj_x_edge[0] <= mouse_pos[0] <= obj_x_edge[1] and obj_y_edge[0] <= mouse_pos[1] <= obj_y_edge[1]:
                return True

        return False

    def grappling_gun(self, mouse_pos):
        if not self.rope:
            self.rope = Rope(obj=self, pivot=mouse_pos, color=self.color)

    def render_force(self, display, camera, double=False):
        central_pos = (self.pos[0] + (self.size[0] / 2) - camera.pos[0], self.pos[1] + (self.size[1] / 2) - camera.pos[1])
        if double:
            pygame.draw.line(display, (255, 0, 0), central_pos, (central_pos[0] + (self.perm_force[0] + self.temp_force[0]) * 10, central_pos[1]), width=3)
            pygame.draw.line(display, (255, 0, 0), central_pos, (central_pos[0], central_pos[1] + (self.perm_force[1] + self.temp_force[1]) * 10), width=3)
        else:
            pygame.draw.line(display, (255, 0, 0), central_pos, (central_pos[0] + (self.perm_force[0] + self.temp_force[0]) * 10, central_pos[1] + (self.perm_force[1] + self.temp_force[1]) * 10), width=3)


class Camera:
    def __init__(self, obj, screen_size):
        self.obj, self.screen_size = obj, screen_size
        self.pos = [0, 0]
        self.update()

    def update(self):
        self.pos[0] = self.obj.pos[0] - (self.screen_size[0] / 2)
        self.pos[1] = self.obj.pos[1] - (self.screen_size[1] / 2)


class Rope:
    def __init__(self, obj, pivot, color):
        self.obj, self.pivot = obj, pivot
        self.color = color
        self.length, self.angle = 0, 0
        self.update()

    def update(self):
        self.length = math.sqrt((self.obj.pos[0] + (self.obj.size[0] / 2) - self.pivot[0]) ** 2 + (self.obj.pos[1] + (self.obj.size[1] / 2) - self.pivot[1]) ** 2)
        self.angle = math.atan2(self.pivot[1] - (self.obj.pos[1] + self.obj.size[1] / 2), self.pivot[0] - (self.obj.pos[0] + self.obj.size[0] / 2))

    def blit(self, display, camera):
        pygame.draw.line(display, self.color, (self.obj.pos[0] + (self.obj.size[0] / 2) - camera.pos[0], self.obj.pos[1] + (self.obj.size[1] / 2) - camera.pos[1]), (self.pivot[0] - camera.pos[0], self.pivot[1] - camera.pos[1]), width=3)
