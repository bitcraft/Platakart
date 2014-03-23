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

from collections import namedtuple
Kart = namedtuple("Kart", "chassis, rear_motor, front_motor")


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
        floor = pymunk.Segment(floor_body, (0, 20), (640, 20), 50.0)
        floor.friction = 2.0
        floor.collision_type = 2
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
        mass = 10
        inertia = pymunk.moment_for_segment(mass, (-75, 0), (75, 0))
        chassis_body = pymunk.Body(mass, inertia)
        chassis_body.position = 150, 300
        chassis = pymunk.Segment(chassis_body, (-75, 0), (75, 0), 15.0)

        # set up wheels
        mass = 1
        radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        damping = 1.0
        stiffness = 300.0

        rear_wheel_body = pymunk.Body(mass, inertia)
        rear_wheel_body.position = (100, 250)
        rear_wheel = pymunk.Circle(rear_wheel_body, radius, (0, 0))
        rear_wheel.friction = 1.0
        rear_wheel.collision_type = 2
        rear_wheel_body_spring = pymunk.DampedSpring(
            rear_wheel_body, chassis_body, (0, 0), (-50, -15), 50.0,
            stiffness, damping)

        front_wheel_body = pymunk.Body(mass, inertia)
        front_wheel_body.position = (200, 250)
        front_wheel = pymunk.Circle(front_wheel_body, radius, (0, 0))
        front_wheel.friction = 1.0
        front_wheel.collision_type = 2
        front_wheel_body_spring = pymunk.DampedSpring(
            front_wheel_body, chassis_body, (0, 0), (50, -15), 50.0,
            stiffness, damping)

        rear_groove_joint = pymunk.GrooveJoint(chassis_body, rear_wheel_body,
                                             (-50, -50), (-50, -15), (0, 0))
        front_groove_joint = pymunk.GrooveJoint(chassis_body, front_wheel_body,
                                              (50, -50), (50, -15), (0, 0))

        motor1 = pymunk.SimpleMotor(chassis_body, front_wheel_body, 0.0)
        motor2 = pymunk.SimpleMotor(chassis_body, rear_wheel_body, 0.0)

        space.add(chassis_body, chassis, rear_wheel_body, rear_wheel,
                  rear_wheel_body_spring, rear_groove_joint,
                  front_wheel_body, front_wheel,
                  front_wheel_body_spring, front_groove_joint,
                  motor1, motor2)

        return Kart(chassis_body, motor2, motor1)

    def on_key_up(self, key, mod):
        for kart in self.karts:
            if key == K_RIGHT:
                kart.rear_motor.rate = 10
                kart.front_motor.rate = 10
            elif key == K_LEFT:
                kart.rear_motor.rate = -10
                kart.front_motor.rate = -10
            elif key == K_UP:
                    kart.chassis.apply_impulse((0, 6000))
