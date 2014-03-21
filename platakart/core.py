# -*- coding: utf-8; -*-

import logging
import ConfigParser
import os.path
from pubsub import pub

logger = logging.getLogger("platakart.core")

from pygame.time import Clock
import pygame
import pygame.event
import pygame.font
import pytmx

from platakart.title import TitleScene
from platakart.kartselect import KartSelectScene
from platakart.trackselect import TrackSelectScene

SHOWFPSEVENT = pygame.USEREVENT + 1
GAMETITLE = "Platakart"


class Resources(object):

    def __init__(self):
        self.images = dict()
        self.sounds = dict()
        self.tilemaps = dict()
        self.fonts = dict()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self.path = os.path.join(current_dir, "resources")
        self.config_path = os.path.join(self.path, "resources.ini")
        self.loaded = False

    def load_images(self):
        for key, path in self.images.items():
            full_path = os.path.join(self.path, path)
            img = pygame.image.load(full_path)
            img.convert()
            self.images[key] = img
            logger.debug("Loaded image %s" % full_path)
            yield "image", key

    def load_sounds(self):
        for key, path in self.sounds.items():
            full_path = os.path.join(self.path, path)
            self.sounds[key] = pygame.mixer.Sound(full_path)
            logger.debug("Loaded sound %s" % full_path)
            yield "sound", key

    def load_tilemaps(self):
        for key, path in self.tilemaps.items():
            full_path = os.path.join(self.path, path)
            self.tilemaps[key] = pytmx.load_pygame(full_path)
            logger.debug("Loaded tilemap %s" % full_path)
            yield "tilemap", key

    def load_fonts(self):
        yield None, None

    def load_config(self):
        parser = ConfigParser.SafeConfigParser()
        parser.read(self.config_path)
        self.images.update(parser.items("images"))
        self.sounds.update(parser.items("sounds"))
        self.tilemaps.update(parser.items("tilemaps"))
        self.fonts.update(parser.items("fonts"))

    def load(self):
        if self.loaded:
            return
        self.load_config()
        dicts = (self.images, self.sounds, self.tilemaps, self.fonts)
        total = sum(map(len, dicts))
        loaded = 0
        logger.debug(
            "Loading resources from config: %s" % str(self.config_path))
        gens = (self.load_images, self.load_sounds, self.load_tilemaps,
                self.load_fonts)

        for gen in gens:
            for category, key in gen():
                loaded += 1
                pub.sendMessage("resources.loading",
                                percent=float(loaded) / float(total),
                                category=category,
                                key=key)
                yield
        self.loaded = True
        pub.sendMessage("resources.loaded")


class Game(object):

    def __init__(self, config, scenes, starting_scene, resources):
        self.clock = Clock()
        self.config = config
        self.shutting_down = False
        self.scenes = scenes
        self.current_scene = starting_scene
        self.resources = resources

        try:
            self.display_width = int(config.get("display_width", 640))
        except ValueError:
            logger.warning("Invalid DISPLAY_WIDTH")
            self.display_width = 640

        try:
            self.display_height = int(config.get("display_height", 480))
        except ValueError:
            logger.warning("Invalid DISPLAY_HEIGHT")
            self.display_height = 480

        self.display_size = (self.display_width, self.display_height)
        pub.subscribe(self.switch_scene, "game.switch-scene")
        pub.subscribe(self.play_sound, "game.play-sound")
        pub.subscribe(self.stop_sound, "game.stop-sound")

    def init_pygame(self):
        logger.debug("Initializing pygame")
        pygame.display.init()
        pygame.font.init()
        pygame.mixer.init()
        screen = pygame.display.set_mode(self.display_size)
        pygame.display.set_caption(GAMETITLE)
        return screen

    def switch_scene(self, name, options):
        self.current_scene.teardown()
        self.current_scene = self.scenes[name]
        if options is None:
            self.current_scene.setup()
        else:
            self.current_scene.setup(dict(options))

    def play_sound(self, name=None, loops=0, maxtime=0, fade_ms=0):
        if int(self.config.get("sound_enabled", 0)):
            self.resources.sounds[name].play(loops, maxtime, fade_ms)

    def stop_sound(self, name=None, fade_ms=0):
        if fade_ms == 0:
            self.resources.sounds[name].stop()
        else:
            self.resources.sounds[name].fadeout(fade_ms)

    def main_loop(self):
        screen = self.init_pygame()

        logger.debug("Entering main loop")
        try:
            self._main_loop(screen)
        except KeyboardInterrupt:
            logger.debug("Keyboard interrupt received")
        logger.debug("Shutting down main loop")
        pygame.quit()

    def _main_loop(self, screen):
        # Get references to things that will be used in every frame to
        # avoid needless derefrencing.
        target_fps = float(self.config.get("target_fps", 30))
        pump = pygame.event.pump
        get = pygame.event.get
        QUIT = pygame.QUIT
        MOUSEMOTION = pygame.MOUSEMOTION
        MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
        MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
        KEYDOWN = pygame.KEYDOWN
        KEYUP = pygame.KEYUP
        pygame.time.set_timer(SHOWFPSEVENT, 3000)
        self.current_scene.setup()
        while not self.shutting_down:
            pump()
            for event in get():
                t = event.type
                if t == QUIT:
                    self.shutting_down = True
                    break
                elif t == SHOWFPSEVENT:
                    logger.debug("FPS: %d" % self.clock.get_fps())
                elif t == MOUSEMOTION:
                    pub.sendMessage("input.mouse-move", pos=event.pos,
                                    rel=event.rel, buttons=event.buttons)
                elif t == MOUSEBUTTONDOWN:
                    pub.sendMessage("input.mouse-down", pos=event.pos,
                                    button=event.button)
                elif t == MOUSEBUTTONUP:
                    pub.sendMessage("input.mouse-up", pos=event.pos,
                                    button=event.button)
                elif t == KEYUP:
                    pub.sendMessage(
                        "input.key-up",
                        key=event.key, 
                        mod=event.mod)
                elif t == KEYDOWN:
                    pub.sendMessage(
                        "input.key-down",
                        unicode=event.unicode,
                        key=event.key,
                        mod=event.mod)

            delta = self.clock.tick(target_fps)
            self.current_scene.update(screen, delta)


def parse_config(config_path):
    parser = ConfigParser.SafeConfigParser()
    config = dict()
    try:
        parser.read(config_path)
        for section in parser.sections():
            config.update(parser.items(section))
    except Exception as ex:
        logger.error("Error parsing config file: %s" % str(config_path))
        logger.exception(ex)

    logger.debug("Config is: \n %s" % str(config))
    return config

def create_game(config_path):
    if config_path is None:
        logger.warning("Starting with default configuration.")
        conf = dict()
    else:
        conf = parse_config(config_path)

    resources = Resources()
    scenes = {"title": TitleScene(resources),
              "kart-select": KartSelectScene(resources),
              "track-select": TrackSelectScene(resources)}
    g = Game(conf, scenes, scenes["title"], resources)
    return g
