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
        floor = pymunk.Segment(pymunk.Body(), (0, 10), (640, 10), 5.0)
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
        moment = pymunk.moment_for_segment(mass, (-50, 0), (50, 0))
        chassis_body = pymunk.Body(mass, moment)
        chassis_body.position = 150, 150
        chassis = pymunk.Segment(chassis_body, (-50, 0), (50, 0), 5.0)

        # set up rear-suspension
        mass = 1
        moment = pymunk.moment_for_segment(mass, (0, 0), (0, 10))
        rear_suspension_body = pymunk.Body(mass, moment)
        rear_suspension_body.position = 100, 160
        rear_suspension = pymunk.Segment(
            rear_suspension_body, (0, 0), (0, 25), 1.0)
        rear_suspension_body_joint = pymunk.SlideJoint(
            rear_suspension_body, chassis_body, (0, 0), (-50, 0), 10.0, 15.0)

        # set up front-suspension
        mass = 1
        moment = pymunk.moment_for_segment(mass, (0, 0), (0, 10))
        front_suspension_body = pymunk.Body(mass, moment)
        front_suspension_body.position = 100, 160
        front_suspension = pymunk.Segment(
            front_suspension_body, (0, 0), (0, 25), 1.0)
        front_suspension_body_joint = pymunk.SlideJoint(
            front_suspension_body, chassis_body, (0, 0), (50, 0), 10.0, 15.0)

        space.add(chassis_body, chassis, 
                  rear_suspension_body, rear_suspension, rear_suspension_body_joint,
                  front_suspension_body, front_suspension, front_suspension_body_joint)


        return chassis

    def on_key_up(self, key, mod):
        if key == K_RIGHT:
            pass
        elif key == K_LEFT:
            pass
        elif key == K_UP:
            for kart in self.karts:
                kart.body.apply_impulse((0, 30000))
