# -*- coding: utf-8; -*-

import logging
import random

logger = logging.getLogger("platakart.track")

from pubsub import pub
import pygame.display
import pygame.sprite
import pygame.draw
import pymunk
import pymunk.pygame_util
import pyscroll

from pygame import K_DOWN
from pygame import K_LEFT
from pygame import K_RIGHT
from pygame import K_UP
from pymunktmx.shapeloader import load_shapes

from platakart.ui import BLACK
from platakart.ui import Scene

from collections import namedtuple

KartPerf = namedtuple(
    "KartPerf", "max_motor_rate, acceleration_rate, break_rate")


class Kart(pygame.sprite.Sprite):

    RIGHT = 1
    LEFT = -1
    CHASSIS_MASS = 15.0
    WHEEL_MASS = 5.0
    STIFFNESS = 205.0
    DAMPING = 0.01
    WHEEL_FRICTION = 1.0
    JUMP_IMPULSE = 12000
    REAR_WHEEL_OFFSET_PERCENT = .17186
    FRONT_WHEEL_OFFSET_PERCENT = .80129
    WHEEL_VERTICAL_OFFSET = .79858

    def __init__(self, id, space, start_pos, body_surf, wheel_surf,
                 kart_perf):
        super(Kart, self).__init__()
        self.id = id
        self.body_surf = body_surf
        self.chassis = None
        self.direction = self.LEFT
        self.map_data = None
        self.map_layer = None
        self.motors = list()
        self.perf = kart_perf
        self.physics_initialized = False
        self.space = space
        self.start_pos = start_pos
        self.wheel_surf = wheel_surf
        self.wheels = list()

    def _make_wheel(self, chassis_body, body_rect, mass,
                    h_offset_percent, v_offset_percent):
        wheel_rect = self.wheel_surf.get_rect()
        radius = wheel_rect.width // 2
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        damping = self.DAMPING
        stiffness = self.STIFFNESS
        wheel_vertical_offset = v_offset_percent * wheel_rect.height
        wheel_offset = ((body_rect.width * h_offset_percent)
                        - body_rect.width / 2)

        wheel_body = pymunk.Body(self.WHEEL_MASS, inertia)
        wheel_body.position = (chassis_body.position.x + wheel_offset,
                               chassis_body.position.y - (radius * 4))
        wheel = pymunk.Circle(wheel_body, radius, (0, 0))
        wheel.friction = self.WHEEL_FRICTION

        wheel_body_spring = pymunk.DampedSpring(
            wheel_body,
            chassis_body,
            (0, 0),
            (-wheel_offset, -body_rect.height * .75),
            50.0,
            stiffness,
            damping)

        groove_joint = pymunk.GrooveJoint(
            chassis_body, wheel_body,
            (-wheel_offset, -body_rect.height),
            (-wheel_offset, -wheel_vertical_offset - (radius * 1.25)),
            (0, 0))

        motor = pymunk.SimpleMotor(chassis_body, wheel_body, 0.0)
        self.motors.append(motor)
        self.wheels.append(wheel_body)

        return wheel_body, wheel,  motor, groove_joint, wheel_body_spring

    def init_physics(self):
        if self.physics_initialized:
            logger.warning("Attempted multiple setups of physics for %s"
                           % self.id)
            return

        logger.debug("Setting up physics for %s" % self.id)
        # set up chassis
        body_rect = self.body_surf.get_rect()
        half_width = body_rect.width / 2.0
        inertia = pymunk.moment_for_segment(
            self.CHASSIS_MASS, (-half_width, 0), (half_width, 0))

        chassis_body = pymunk.Body(self.CHASSIS_MASS, inertia)
        chassis_body.position = self.start_pos
        chassis = pymunk.Segment(
            chassis_body, (-half_width, 0), (half_width, 0),
            body_rect.height // 2)
        self.space.add(chassis_body, chassis)
        self.chassis = chassis_body

        # set up wheels
        self.space.add(*self._make_wheel(
            chassis_body,
            body_rect,
            self.WHEEL_MASS,
            self.REAR_WHEEL_OFFSET_PERCENT,
            self.WHEEL_VERTICAL_OFFSET))

        self.space.add(*self._make_wheel(
            chassis_body,
            body_rect,
            self.WHEEL_MASS,
            self.FRONT_WHEEL_OFFSET_PERCENT,
            self.WHEEL_VERTICAL_OFFSET))

        self.physics_initialized = True

    def update(self):
        pass

    def draw(self, screen):
        degs_per_rad = 57.2957795
        for wheel in self.wheels:
            x, y = wheel.position
            w, h = self.wheel_surf.get_size()
            wheel_surf = pygame.transform.rotozoom(
                self.wheel_surf, wheel.angle * degs_per_rad, 1)
            ww, hh = wheel_surf.get_size()
            rrect = pygame.Rect(x+4, screen.get_height() - y - h + 30, ww, hh)
            rrect.move_ip((w-ww) / 2, (h-hh) / 2)
            screen.blit(wheel_surf, rrect.topleft)

        body_surf = pygame.transform.rotozoom(
            self.body_surf, (self.chassis.angle * degs_per_rad) % 360, 1)
        p = pymunk.pygame_util.to_pygame(self.chassis.position, screen)
        r = body_surf.get_rect()
        r.topleft = p
        r.left -= 43
        r.top += 12
        screen.blit(body_surf, r)

    def accelerate(self, direction):
        amt = direction * self.perf.acceleration_rate
        for motor in self.motors:
            if abs(motor.rate + amt) < self.perf.max_motor_rate:
                motor.rate += amt

    def decelerate(self):
        amt = self.direction * self.perf.break_rate
        for motor in self.motors:
            motor.rate -= amt
            if self.direction == self.RIGHT:
                if motor.rate < 0:
                    motor.rate = 0
            elif self.direction == self.LEFT:
                if motor.rate > 0:
                    motor.rate = 0

    def jump(self):
        self.chassis.apply_impulse((0, self.JUMP_IMPULSE))


class TrackScene(Scene):

    def __init__(self, resources, conf):
        self.resources = resources
        self.space = None
        self.karts = None
        self.step_amt = 1.0 / float(conf.get("target_fps", 30))
        logger.debug("Calculated space step amount = %f" % self.step_amt)

    def get_name(self):
        return "track"

    def setup(self, options=None):
        logger.debug("Setting up track scene")
        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)

        if options:
            track_name = options.get("trackname")
            if track_name:
                tmx_data = self.resources.tilemaps[track_name]
                load_shapes(tmx_data, space=self.space)
                self.map_data = pyscroll.TiledMapData(tmx_data)
                self.map_layer = pyscroll.BufferedRenderer(self.map_data, (640, 480))
                self.map_layer.center((200, 200))

        # floor
        floor_body = pymunk.Body()
        floor = pymunk.Segment(floor_body, (-1000, 20), (1000, 20), 50.0)
        floor.friction = .5
        #self.space.add(floor)

        self.karts = list()
        perf = KartPerf(30, 8, 15)
        green_kart = Kart(
            "green-kart",
            self.space,
            (150, 150),
            self.resources.images["green-kart"],
            self.resources.images["wheel"],
            perf)
        # green_kart.init_physics()
        self.karts.append(green_kart)
        pub.subscribe(self.on_key_up, "input.key-up")

    def teardown(self):
        logger.debug("Tearing down track scene")
        pub.unsubscribe(self.on_key_up, "input.key-up")

    def update(self, screen, delta):
        self.space.step(self.step_amt)
        screen.fill((128, 128, 255))
        self.map_layer.update()
        self.map_layer.draw(screen, pygame.Rect(0, 0, 640, 480))
        # pymunk.pygame_util.draw(screen, self.space)
        #for kart in self.karts:
        #    kart.draw(screen)
        pygame.display.flip()

    def on_key_up(self, key, mod):
        for kart in self.karts:
            if key == K_RIGHT:
                kart.accelerate(Kart.RIGHT)
            elif key == K_LEFT:
                kart.accelerate(Kart.LEFT)
            elif key == K_UP:
                kart.jump()
            elif key == K_DOWN:
                kart.decelerate()
