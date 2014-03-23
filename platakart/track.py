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

from pygame import K_DOWN
from pygame import K_LEFT
from pygame import K_RIGHT
from pygame import K_UP

from platakart.ui import BLACK
from platakart.ui import BLUE
from platakart.ui import RED
from platakart.ui import Scene
from platakart.ui import WHITE

PERCENT_COLOR = WHITE
FADE_COLOR = BLACK

from collections import namedtuple
Kart = namedtuple("Kart", "chassis, rear_motor, front_motor")

class Kart(pygame.sprite.Sprite):

    CHASSIS_MASS = 15.0
    WHEEL_MASS = 5.0
    STIFFNESS = 205.0
    DAMPING = 0.01
    WHEEL_FRICTION = 1.0
    REAR_WHEEL_OFFSET_PERCENT = .17186
    FRONT_WHEEL_OFFSET_PERCENT = .80129
    WHEEL_VERTICAL_OFFSET = .79858

    def __init__(self, id, space, start_pos, body_surf, wheel_surf):
        super(Kart, self).__init__()
        self.id = id
        self.space = space
        self.body_surf = body_surf
        self.wheel_surf = wheel_surf
        self.physics_initialized = False
        self.start_pos = start_pos
        self.wheels = list()
        self.chassis = None


    def _make_wheel(self, chassis_body, body_rect, mass, 
                    h_offset_percent, v_offset_percent):
        wheel_rect = self.wheel_surf.get_rect()
        radius = wheel_rect.width // 2
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        damping = self.DAMPING
        stiffness = self.STIFFNESS
        wheel_vertical_offset = v_offset_percent * wheel_rect.height

        wheel_body = pymunk.Body(self.WHEEL_MASS, inertia)
        wheel_offset = body_rect.width * h_offset_percent
        wheel_body.position = (wheel_offset, wheel_vertical_offset)
        wheel = pymunk.Circle(wheel_body, radius, (0, 0))
        wheel.friction = self.WHEEL_FRICTION

        # wheel_body_spring = pymunk.DampedSpring(
        #     wheel_body, chassis_body, (0, 0), (-50, -15), 50.0,
        #     stiffness, damping)

        # groove_joint = pymunk.GrooveJoint(chassis_body, wheel_body,
        #                                   (-50, -50), (-50, -40), (0, 0))

        motor = pymunk.SimpleMotor(chassis_body, wheel_body, 0.0)

        self.wheels.append(motor)
        # wheel_body_spring, groove_joint,
        return wheel_body, wheel,  motor

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
            self.REAR_WHEEL_OFFSET_PERCENT,
            self.WHEEL_VERTICAL_OFFSET,
            self.WHEEL_MASS))

        self.space.add(*self._make_wheel(
            chassis_body,
            body_rect,
            self.FRONT_WHEEL_OFFSET_PERCENT,
            self.WHEEL_VERTICAL_OFFSET,
            self.WHEEL_MASS))

        self.physics_initialized = True

    def update(self):
        pass


class TrackScene(Scene):

    def __init__(self, resources, conf):
        self.resources = resources
        self.space = None
        self.karts = None
        self.step_amt = 1.0 / float(conf.get("target_fps", 30))
        logger.debug("Calculated space step amount = %f" % self.step_amt)

    def get_name(self):
        return "track"

    def setup(self):
        logger.debug("Setting up track scene")
        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)

        # floor
        floor_body = pymunk.Body()
        floor = pymunk.Segment(floor_body, (-1000, 20), (1000, 20), 50.0)
        floor.friction = .5
        self.space.add(floor)

        self.karts = list()
        green_kart = Kart(
            "green-kart",
            self.space,
            (150, 150),
            self.resources.images["green-kart"], 
            self.resources.images["wheel"])
        green_kart.init_physics()
        self.karts.append(green_kart)
        pub.subscribe(self.on_key_up, "input.key-up")

    def teardown(self):
        logger.debug("Tearing down track scene")
        pub.unsubscribe(self.on_key_up, "input.key-up")

    def update(self, screen, delta):
        self.space.step(self.step_amt)
        screen.fill(BLACK)
        pymunk.pygame_util.draw(screen, self.space)
        pygame.display.flip()
    

    def on_key_up(self, key, mod):
        for kart in self.karts:
            if key == K_RIGHT:
                for motor in self.motors:
                    motor.rate = 25
                    motor.rate = 25
            elif key == K_LEFT:
                for motor in self.motors:
                    motor.rate = -25
                    motor.rate = -25
            elif key == K_UP:
                    kart.chassis.apply_impulse((0, 12000))
