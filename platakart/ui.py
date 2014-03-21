# -*- coding: utf-8 -*-

from pubsub import pub
import pygame.sprite

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# This is probably not the best place for Scene, but putting it here
# helps to avoid forward declarations in core.py.
class Scene(object):

    def get_name(self):
        raise NotImplemented

    def setup(self, **kwargs):
        raise NotImplemented

    def teardown(self):
        pass

    def update(self, screen, delta):
        pass


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
            pub.sendMessage("game.play-sound", name="menu-select")
            pub.sendMessage("button.clicked", id=self.id)

    def on_mouse_move(self, pos, rel, buttons):
        if self.image is self.down_surf:
            if not self.rect.collidepoint(pos):
                self.image = self.up_surf
                self.rect = self.up_rect
                self.dirty = 1
