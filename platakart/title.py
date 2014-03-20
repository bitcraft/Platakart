# -*- coding: utf-8; -*-

import logging
from pubsub import pub
import pygame.display
import pygame.font

logger = logging.getLogger("platakart.title")

from platakart.core import Scene

PERCENT_COLOR = (255, 255, 255)

class TitleScene(Scene):

    def __init__(self, resources):
        self.started_loading_resources = False
        self.render_title = False
        self.render_percent = False
        self.render_button = False
        self.resources = resources
        self.loader_gen = None
        self.loaded = False
        self.font = None
        self.percent_surf = None
        self.button_rect = None
        pub.subscribe(self.on_resource_loaded, "resources.loading")
        pub.subscribe(self.on_mouse_move, "input.mouse-move")
        pub.subscribe(self.on_mouse_up, "input.mouse-up")

    def get_name(self):
        return "title"

    def setup(self):
        logger.debug("Setting up title scene")
        self.font = pygame.font.SysFont("Verdana", 32)

    def teardown(self):
        logger.debug("Tearing down title scene")
        self.font = None
        self.percent_surf = None
        self.render_title = False
        self.render_percent = False

    def on_resource_loaded(self, percent, category, key):
        if category == "image" and key == "title":
            self.render_title = True
        else:
            self.percent_surf = self.font.render(
                "Loading %d%%" % int(percent * 100), True, PERCENT_COLOR)
            if int(percent) != 1:
                self.render_percent = True
            elif int(percent) == 1:
                self.render_button = True

    def on_mouse_move(self, pos, rel, buttons):
        if self.button_rect:
            if self.button_rect.collidepoint(pos):
                self.render_button = "hover"
            else:
                self.render_button = "normal"

    def on_mouse_up(self, pos, button):
        if self.button_rect:
            if self.button_rect.collidepoint(pos):
                logger.debug("Mouse clicked button")

    def update(self, screen, delta):
        if not self.loaded:
            if self.loader_gen is None:
                self.loader_gen = self.resources.load()
            else:
                try:
                    self.loader_gen.next()
                except StopIteration:
                    self.loaded = True
                
        if self.render_title:
            screen_rect = screen.get_rect()
            screen.blit(self.resources.images["title"], screen_rect)
            pygame.display.flip()
            self.render_title = False

        if self.render_percent:
            screen_rect = screen.get_rect()
            surf_copy = self.percent_surf.copy()
            surf_copy.fill((0, 0, 0))
            surf_rect = surf_copy.get_rect()
            x = screen_rect.centerx - (surf_rect.width // 2)
            y = screen_rect.height * .75
            screen.blit(surf_copy, (x, y))
            rect = screen.blit(self.percent_surf, (x, y))
            pygame.display.update(rect)
            self.render_percent = False

        if self.render_button:
            screen_rect = screen.get_rect()

            if self.render_button == "hover":
                add_y = 4
                img = self.resources.images["red_button_down"]
            else:
                add_y = 0
                img = self.resources.images["red_button_up"]

            surf_rect = img.get_rect()
            x = screen_rect.centerx - (surf_rect.width // 2)
            y = (screen_rect.height * .75) + add_y
            screen.blit(self.resources.images["title"], screen_rect)
            button_rect = screen.blit(img, (x, y))
            self.button_rect = button_rect
            label_surf = self.font.render("PLAY", True, PERCENT_COLOR)
            label_rect = label_surf.get_rect()
            label_rect.center = button_rect.center
            screen.blit(label_surf, label_rect)
            pygame.display.flip()
            self.render_button = False
