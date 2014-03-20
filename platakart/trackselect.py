# -*- coding: utf-8; -*-

import logging
from collections import namedtuple

from pubsub import pub
import pygame.display
import pygame.font
import pygame.sprite

logger = logging.getLogger("platakart.trackselect")

from platakart.ui import Scene
from platakart.ui import Button

WHITE = (255, 255, 255)


TrackInfo = namedtuple("TrackInfo", "name, description, thumbnail")


class TrackButton(pygame.sprite.DirtySprite):

    def __init__(self, thumb_surf, pos, track_info):
        super(TrackButton, self).__init__()
        self.image = thumb_surf
        self.thumb_surf = thumb_surf
        self.rect = self.image.get_rect()
        self.rect.topleft = pos

    def on_mouse_move(self, pos, rel, buttons):
        if self.rect.containspoint(pos):
            logger.debug("Moused over %s" % track_info["name"])


class TrackButtonBar(pygame.sprite.RenderUpdates):

    def __init__(self):
        super(TrackButtonBar, self).__init__()
        self.selected_index = 0
        self.tiles_to_show = 0

    def update(self):
        """Reposition all of the images based on the selected_index"""
        super(TrackButtonBar, self).update()
        
        

class TrackSelectScene(Scene):

    def __init__(self, resources):
        self.resources = resources
        self.rendered = False
        self.track_buttons = None
        pub.subscribe(self.on_button_clicked, "kart-select.button.clicked")

    def get_name(self):
        return "kart-select"

    def setup(self, options=None):
        self.rendered = False
        logger.debug("Setting up kart select scene")
        logger.debug("kart_id: %s" % options["kart_id"])
        self.font = pygame.font.SysFont("Verdana", 32)
        self.track_buttons = pygame.sprite.RenderUpdates()

        for tilemap in self.resources.tilemaps.values():
            info = TrackInfo(tilemap.name, tilemap.description,
                             tilemap.thumbnail)
            img = self.resources.images[info.thumbnail]
            self.track_buttons.add(TrackButton(img, (0, 0), info))

    def teardown(self):
        logger.debug("Tearing down kart select scene")
        self.buttons = None

    def update(self, screen, delta):
        if not self.rendered:
            screen_rect = screen.get_rect()
            screen.blit(self.resources.images["track-select"], screen_rect)
            screen.blit(self.resources.images["testtrack-thumb"], (10, 128))
            pygame.display.flip()
            self.rendered = True

    def on_button_clicked(self, id):
        logger.debug("Kart {%s} selected" % id)
