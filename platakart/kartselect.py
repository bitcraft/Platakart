# -*- coding: utf-8; -*-

import logging
from pubsub import pub
import pygame.display
import pygame.font

logger = logging.getLogger("platakart.kartselect")

from platakart.core import Scene


class KartSelectScene(Scene):

    def __init__(self, resources):
        self.resources = resources
        self.rendered = False

    def get_name(self):
        return "kart-select"

    def setup(self):
        self.rendered = False
        logger.debug("Setting up kart select scene")
        self.font = pygame.font.SysFont("Verdana", 32)

    def teardown(self):
        logger.debug("Tearing down kart select scene")

    def update(self, screen, delta):
        if not self.rendered:
            screen.fill(0)
            pygame.display.flip()
            self.rendered = True
