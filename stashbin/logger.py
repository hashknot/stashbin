#!/usr/bin/python

import logging
import logging.handlers

from constants import LOG_FILE

def configure():
    logger = logging.getLogger("pricewatch")
    logger.setLevel(logging.DEBUG)

    # fileHandler = logging.handlers.RotatingFileHandler(fileName, encoding='utf8',
    #                                                    maxBytes=100000, backupCount=1)
    # fileHandler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    # fileHandler.setLevel(logging.INFO)
    # logger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s: %(filename)s: %(message)s'))
    streamHandler.setLevel(logging.DEBUG)
    logger.addHandler(streamHandler)
