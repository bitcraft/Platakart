# -*- coding: utf-8; -*-

import logging
import random

logger = logging.getLogger("platakart.track")

from pubsub import pub
import pygame.display
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
        floor = pymunk.Segment(pymunk.Body(), (0, 20), (640, 20), 50.0)
        self.space.add(floor)

        self.karts = list()
        self.karts.append(self.make_kart(self.space))
        pub.subscribe(self.on_key_up, "input.key-up")

    def teardown(self):
        logger.debug("Tearing down track scene")
        pub.unsubscribe(self.on_key_up, "input.key-up")

    def update(self, screen, delta):
        self.space.step(self.step_amt)
        screen.fill(BLACK)
        pymunk.pygame_util.draw(screen, self.space)
        pygame.display.flip()

    def make_kart(self, space):
        # set up chassis
        mass = 100
        chassis_body = pymunk.Body(mass, pymunk.inf)
        chassis_body.position = 150, 300
        chassis = pymunk.Segment(chassis_body, (-75, 0), (75, 0), 5.0)

        # set up wheels
        mass = 1
        radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        damping = 0.0
        stiffness = 250.0

        rear_wheel_body = pymunk.Body(mass, inertia)
        rear_wheel_body.position = (100, 250)
        rear_wheel = pymunk.Circle(rear_wheel_body, radius, (0, 0))
        rear_wheel_body_spring = pymunk.DampedSpring(
            rear_wheel_body, chassis_body, (0, 0), (-50, 0), 40.0,
            stiffness, damping)

        front_wheel_body = pymunk.Body(mass, inertia)
        front_wheel_body.position = (200, 250)
        front_wheel = pymunk.Circle(front_wheel_body, radius, (0, 0))
        front_wheel_body_spring = pymunk.DampedSpring(
            front_wheel_body, chassis_body, (0, 0), (50, 0), 40.0,
            stiffness, damping)

        space.add(chassis_body, chassis, rear_wheel_body, rear_wheel,
                  rear_wheel_body_spring,
                  front_wheel_body, front_wheel,
                  front_wheel_body_spring)

        return chassis

    def on_key_up(self, key, mod):
        if key == K_RIGHT:
            pass
        elif key == K_LEFT:
            pass
        elif key == K_UP:
            for kart in self.karts:
                kart.body.apply_impulse((0, 32000))
