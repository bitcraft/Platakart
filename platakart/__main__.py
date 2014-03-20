# -*- coding: utf-8; -*-

from argparse import ArgumentParser
import logging
import os
import os.path

logger = logging.getLogger("platakart.__main__")

from platakart.core import create_game

config_file_path = os.getenv("PLATAKART_CONF_PATH")

try:
    if config_file_path is None:
        logger.debug("PLATAKART_CONF_PATH env arg not defined")
        home = os.path.expanduser("~")
        config_file_path = os.path.join(home, ".platakart", "platakart.ini")
        with open(config_file_path, "r"):
            pass
except:
    logger.debug("No config file found in home folder")
    config_file_path = None

parser = ArgumentParser(prog="platakart", description="Platakart Racing!")

parser.add_argument(
    "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default="WARNING", help="Verbosity of logging output")

args = parser.parse_args()

logging.basicConfig(level=getattr(logging, args.log_level))

game = create_game(config_file_path)
game.main_loop()
