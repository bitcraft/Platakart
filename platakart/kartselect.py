# -*- coding: utf-8; -*-

import logging
from pubsub import pub
import pygame.display
import pygame.font
import pygame.sprite

logger = logging.getLogger("platakart.kartselect")

from platakart.ui import Button
from platakart.ui import Scene
from platakart.ui import WHITE
from platakart.ui import BLACK

FADE_COLOR = BLACK


class KartSelectScene(Scene):

    def __init__(self, resources):
        self.resources = resources
        self.rendered = False
        self.buttons = None
        self.fading_out = -0.1
        self.selected_kart_id = None
        
    def get_name(self):
        return "kart-select"

    def setup(self, kwargs=None):
        self.rendered = False
        logger.debug("Setting up kart select scene")
        self.font = pygame.font.SysFont("Verdana", 32)
        self.buttons = pygame.sprite.RenderUpdates()
        self.buttons.add(Button("veloc", "Velocity", self.font,
                                (400, 50),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"]))

        self.buttons.add(Button("balan", "Balance", self.font,
                                (400, 210),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"]))

        self.buttons.add(Button("accel", "Acceleration", self.font,
                                (400, 380),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"]))
        pub.subscribe(self.on_button_clicked, "button.clicked")


    def teardown(self):
        logger.debug("Tearing down kart select scene")
        self.buttons = None
        self.font = None
        pub.unsubscribe(self.on_button_clicked, "button.clicked")

    def update(self, screen, delta):
        if not self.rendered:
            screen_rect = screen.get_rect()
            screen.blit(self.resources.images["kart-select"], screen_rect)
            pygame.display.flip()
            pub.sendMessage(
                "game.play-sound", name="kart-select", loops=-1)
            self.rendered = True

        if self.fading_out >= 100:
            pub.sendMessage("game.switch-scene", name="track-select",
                            options=[("kart_id", self.selected_kart_id)])
        elif self.fading_out >= 0:
            self.fading_out += 10
            fade_rect = screen.get_rect()
            amt = fade_rect.height * float(self.fading_out) / 100.0
            fade_rect.height = int(amt)
            pygame.draw.rect(screen, FADE_COLOR, fade_rect)
            pygame.display.update(fade_rect)
        else:
            self.buttons.update()
            rects = self.buttons.draw(screen)
            pygame.display.update(rects)

    def on_button_clicked(self, id):
        logger.debug("Kart {%s} selected" % id)
        self.fading_out = 0.0
        self.selected_kart_id = id
