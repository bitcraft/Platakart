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
        self.step_amt = 1.0 / float(conf.get("target_fps", 30))
        logger.debug("Calculated space step amount = %f" % self.step_amt)
        self.balls = None
        self.lines = None
        self.contacts = None

    def get_name(self):
        return "track"

    def setup(self):
        logger.debug("Setting up track scene")
        self.space = pymunk.Space()
        self.space.add_collision_handler(0, 0, None, None,
                                         self.add_collision, None)
        self.contacts = list()
        self.space.gravity = (0.0, -900.0)
        self.balls = list()
        for i in range(1):
            self.balls.append(self.add_ball())
        self.lines = self.add_static_L(self.space)
        pub.subscribe(self.on_key_up, "input.key-up")

    def teardown(self):
        logger.debug("Tearing down track scene")
        pub.unsubscribe(self.on_key_up, "input.key-up")

    def update(self, screen, delta):
        self.space.step(self.step_amt)
        screen.fill(BLACK)
        pymunk.pygame_util.draw(screen, self.space)
        pygame.display.flip()

    def make_wheel(self):
        mass = 10
        radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, inertia)
        x = random.randint(120, 380)
        body.position = x, 550
        body.ang_vel_limit = 2
        shape = pymunk.Circle(body, radius)
        self.space.add(body, shape)
        return shape

    def make_kart(self):
        pass

    def add_ball(self):
        mass = 1
        radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        body = pymunk.Body(mass, inertia)
        x = random.randint(120, 380)
        body.position = x, 200
        body.friction = 0.5
        shape = pymunk.Circle(body, radius)
        self.space.add(body, shape)
        return shape

    def add_collision(self, space, arb):
        self.contacts = arb.contacts

    def add_static_L(self, space):
        body = pymunk.Body()
        body.position = (0, 10)
        body.friction = 0.5
        l1 = pymunk.Segment(body, (0, 0), (640, 0), 5)
        l2 = pymunk.Segment(body, (10, 0), (10, 480), 5)
        l3 = pymunk.Segment(body, (630, 0), (630, 480), 5)

        self.space.add(l1, l2, l3)
        return [l1, l2, l3]

    def on_key_up(self, key, mod):
        if key == K_RIGHT:
            for ball in self.balls:
                body = ball.body
                body.apply_impulse((100, 0), (-10, 10))
        elif key == K_LEFT:
            for ball in self.balls:
                body = ball.body
                body.apply_impulse((-100, 0), (-10, 10))
        elif key == K_UP:
            for ball in self.balls:
                body = ball.body
                body.apply_impulse((0, 300))
