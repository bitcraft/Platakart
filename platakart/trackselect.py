# -*- coding: utf-8; -*-

from collections import namedtuple
from random import sample
import logging
import string

from pubsub import pub
import pygame.display
import pygame.font
import pygame.sprite
from pygame import K_DOWN
from pygame import K_LEFT
from pygame import K_RIGHT
from pygame import K_UP

logger = logging.getLogger("platakart.trackselect")

from platakart.ui import BLACK
from platakart.ui import BLUE
from platakart.ui import WHITE
from platakart.ui import Button
from platakart.ui import Scene


TrackInfo = namedtuple("TrackInfo", "key, name, description, thumbnail")


class TrackButton(pygame.sprite.DirtySprite):

    def __init__(self, font, thumb_surf, track_info):
        super(TrackButton, self).__init__()
        self.thumb_surf = thumb_surf.copy()
        self.image = self.thumb_surf
        thumb_rect = self.thumb_surf.get_rect().inflate(-1, -1)
        pygame.draw.rect(self.thumb_surf, BLACK, thumb_rect, 2)
        self.hover_surf = thumb_surf.copy()
        highlight_rect = self.hover_surf.get_rect().inflate(-24, -24)
        pygame.draw.rect(
            self.hover_surf, BLUE, highlight_rect, 8)
        self.track_info = track_info
        self.rect = self.image.get_rect()
        label_surf = font.render(track_info.name, True, WHITE)
        label_rect = label_surf.get_rect()
        label_rect.center = self.rect.center
        self.font = font
        self.thumb_surf.blit(label_surf, label_rect)
        self.hover_surf.blit(label_surf, label_rect)
        pub.subscribe(self.on_mouse_move, "input.mouse-move")

    def on_mouse_move(self, pos, rel, buttons):
        if self.rect.collidepoint(pos):
            self.image = self.hover_surf
            self.dirty = 1
        elif self.image is self.hover_surf:
            self.image = self.thumb_surf

    def on_mouse_up(self, pos, button):
        if self.rect.collidepoint(pos):
            pub.sendMessage(
                "track-select.track-thumb.clicked",
                name=self.track_info.name)


class TrackButtonBar(pygame.sprite.RenderUpdates):

    def __init__(self, rect):
        super(TrackButtonBar, self).__init__()
        self.selected_index = 0
        self.tiles_to_show = 0
        self.rect = rect
        self.dirty = True
        pub.subscribe(self.on_key_up, "input.key-up")

    def update(self):
        """Reposition all of the images based on the selected_index"""
        super(TrackButtonBar, self).update()

    def get_selected_track(self):
        return self.sprites()[self.selected_index].track_info

    def on_key_up(self, key, mod):
        idx = self.selected_index

        if key == K_LEFT or key == K_UP:
            self.selected_index -= 1
            pub.sendMessage("game.stop-sound", name="menu-switch")
            pub.sendMessage("game.play-sound", name="menu-switch")
        elif key == K_RIGHT or key == K_DOWN:
            self.selected_index += 1
            pub.sendMessage("game.stop-sound", name="menu-switch")
            pub.sendMessage("game.play-sound", name="menu-switch")

        buttons = [s for s in self.sprites()]
        for button in buttons:
            button.visible = 0
            button.dirty = 0
            button.rect.topleft = -128, -128

        self.selected_index = max(
            0, min(len(buttons) - 1, self.selected_index))

        idx = self.selected_index
        center_button = buttons[idx]
        center_button.rect.center = self.rect.center
        center_button.rect.left += 4

        if idx - 1 != -1:
            top_button = buttons[idx-1]
            top_button.rect.center = self.rect.center
            top_button.rect.left -= 4
            top_button.rect.top -= 164
            top_button.visible = 1
            top_button.dirty = 1

        if idx < len(buttons) - 1:
            bottom_button = buttons[idx+1]
            bottom_button.rect.center = self.rect.center
            bottom_button.rect.left -= 4
            bottom_button.rect.bottom += 164
            bottom_button.visible = 1
            bottom_button.dirty = 1

        self.dirty = True


class TrackSelectScene(Scene):

    def __init__(self, resources):
        self.resources = resources
        self.rendered = False
        self.track_buttons = None

    def get_name(self):
        return "track-select"

    def setup(self, options=None):
        self.rendered = False
        logger.debug("Setting up kart select scene")
        logger.debug("kart_id: %s" % options["kart_id"])
        self.font = pygame.font.SysFont("Verdana", 32)
        self.track_buttons = TrackButtonBar(pygame.Rect(19, 16, 128, 480))
        font = pygame.font.SysFont("Verdana", 32)
        for key, tilemap in self.resources.tilemaps.items():
            info = TrackInfo(key, tilemap.name, tilemap.description,
                             tilemap.thumbnail)
            img = self.resources.images[info.thumbnail]
            self.track_buttons.add(
                TrackButton(font, img, info))
        self.track_buttons.on_key_up(None, None)
        self.go_button = Button("go", "Go!", self.font, (400, 400),
                                self.resources.images["red_button_up"],
                                self.resources.images["red_button_down"])
        pub.subscribe(self.on_button_clicked, "button.clicked")

    def teardown(self):
        logger.debug("Tearing down track select scene")
        self.buttons = None
        pub.unsubscribe(self.on_button_clicked, "button.clicked")

    def update(self, screen, delta):
        if self.track_buttons.dirty:
            screen_rect = screen.get_rect()
            screen.blit(self.resources.images["track-select"], screen_rect)

            self.rendered = True
            self.track_buttons.update()
            self.track_buttons.draw(screen)

            track_info = self.track_buttons.get_selected_track()
            
            surf = self.font.render(track_info.name, True, WHITE)
            surf_rect = screen.blit(surf, (200, 80))
            margin = 8
            for i, line in enumerate(track_info.description.split("|")):
                surf_rect.top = 80 + (surf_rect.height + margin) * (i + 1)
                surf = self.font.render(line.strip(), True, WHITE)
                screen.blit(surf, surf_rect)

            screen.blit(self.go_button.image, self.go_button.rect)
            pygame.display.flip()

    def on_button_clicked(self, id):
        logger.debug("Track {%s} selected" % id)
