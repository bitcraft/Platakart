# -*- coding: utf-8; -*-

import logging
from pubsub import pub
import pygame.display
import pygame.font
import pygame.sprite

logger = logging.getLogger("platakart.kartselect")

from platakart.core import Scene

WHITE = (255, 255, 255)

class Button(pygame.sprite.DirtySprite):

    def __init__(self, id, label, font, pos, up_surf, down_surf):
        super(Button, self).__init__()
        self.id = id
        self.font = font
        self.label = label
        self.pos = pos
        self.up_surf = up_surf.copy()
        self.up_rect = self.up_surf.get_rect()
        self.down_surf = down_surf.copy()
        self.down_rect = self.down_surf.get_rect()
        label_surf = font.render(label, True, WHITE)
        label_rect = label_surf.get_rect()
        label_rect.center = self.up_rect.center
        self.up_surf.blit(label_surf, label_rect)
        label_rect.center = self.down_rect.center
        self.down_surf.blit(label_surf, label_rect)
        self.up_rect.topleft = pos
        self.down_rect.topleft = pos
        self.down_rect.top += 4
        self.rect = self.up_rect
        self.image = self.up_surf
        pub.subscribe(self.on_mouse_down, "input.mouse-down")
        pub.subscribe(self.on_mouse_up, "input.mouse-up")
        pub.subscribe(self.on_mouse_move, "input.mouse-move")

    def on_mouse_down(self, pos, button):
        if self.rect.collidepoint(pos):
            self.image = self.down_surf
            self.rect = self.down_rect
            self.dirty = 1

    def on_mouse_up(self, pos, button):
        if self.rect.collidepoint(pos):
            self.image = self.up_surf
            self.rect = self.up_rect
            self.dirty = 1
            pub.sendMessage("kart-select.button.clicked", id=self.id)

    def on_mouse_move(self, pos, rel, buttons):
        if self.image is self.down_surf:
            if not self.rect.collidepoint(pos):
                self.image = self.up_surf
                self.rect = self.up_rect
                self.dirty = 1


class KartSelectScene(Scene):

    def __init__(self, resources):
        self.resources = resources
        self.rendered = False
        self.buttons = None
        pub.subscribe(self.on_button_clicked, "kart-select.button.clicked")
        
    def get_name(self):
        return "kart-select"

    def setup(self):
        self.rendered = False
        logger.debug("Setting up kart select scene")
        self.font = pygame.font.SysFont("Verdana", 32)
        self.buttons = pygame.sprite.RenderUpdates()
        self.buttons.add(Button("purple", "Select Purple", self.font,
                                (400, 50),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"]))

        self.buttons.add(Button("green", "Select Green", self.font,
                                (400, 210),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"]))

        self.buttons.add(Button("blue", "Select Blue", self.font,
                                (400, 380),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"]))

    def teardown(self):
        logger.debug("Tearing down kart select scene")
        self.buttons = None

    def update(self, screen, delta):
        if not self.rendered:
            screen_rect = screen.get_rect()
            screen.blit(self.resources.images["kart-select"], screen_rect)
            pygame.display.flip()
            pub.sendMessage(
                "game.play-sound", name="kart-select", loops=-1)
            self.rendered = True
        self.buttons.update()
        rects = self.buttons.draw(screen)
        pygame.display.update(rects)

    def on_button_clicked(self, id):
        logger.debug("Kart {%s} selected" % id)
