# -*- coding: utf-8; -*-

import logging
from pubsub import pub
import pygame.display
import pygame.font
import pygame.draw
logger = logging.getLogger("platakart.title")

from platakart.ui import Scene
from platakart.ui import WHITE
from platakart.ui import BLACK

PERCENT_COLOR = WHITE
FADE_COLOR = BLACK

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
        self.fading_out = -0.1
        pub.subscribe(self.on_resource_loaded, "resources.loading")
        pub.subscribe(self.on_mouse_down, "input.mouse-down")
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
                pub.sendMessage("game.play-sound", name="menu-theme", loops=-1)
                self.render_button = True

    def on_mouse_down(self, pos, button):
        if self.button_rect:
            if self.button_rect.collidepoint(pos):
                self.render_button = "hover"

    def on_mouse_up(self, pos, button):
        if self.button_rect:
            if self.button_rect.collidepoint(pos):
                logger.debug("Mouse clicked button")
                pub.sendMessage("game.play-sound", name="menu-select")
                pub.sendMessage("game.stop-sound",
                                name="menu-theme",
                                fade_ms=100)
                self.fading_out = 0.0
            self.render_button = "normal"


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

        if self.fading_out >= 100:
            pub.sendMessage("game.switch-scene", name="kart-select", options=None)
        elif self.fading_out >= 0:
            self.fading_out += 10
            fade_rect = screen.get_rect()
            amt = fade_rect.height * float(self.fading_out) / 100.0
            fade_rect.height = int(amt)
            pygame.draw.rect(screen, FADE_COLOR, fade_rect)
            pygame.display.update(fade_rect)
