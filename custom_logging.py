# description:  Module to create and handle custom logger.
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20230930

"""Designs and creates a custom logger for dndbattlesim.

Functions:
    _create_formatter,
    add_custom_handler,
    create_custom_logger,
    create_custom_logger_with_handler
Classes:
    custom_logger
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import sys
import os
import logging
import warnings

################################################################################################################################
#=========================================================== SET UP ===========================================================
################################################################################################################################
# If you wish to include additional levels, make sure they each have distinct integer values and are listed in increasing order.
# The minimum level should be 2; 1 is reserved to log everything. The maximum level should be 98; 99 is reserved for no logging.
# The level's name should be 8 characters or less. Additional levels must have matching functions in class custom_logger.
_LEVEL_DICT = {
    'debugall': 9,                  # 9     for more desciptions for debug
    'debug':    logging.DEBUG,      # 10    for script debugging
    'roll':     11,                 # 11    for all dice rolls
    'resource': 12,                 # 12    for any resource changes
    'stat':     13,                 # 13    for any stat or ability changes
    'conditn':  14,                 # 14    for any condition changes or effects
    'damage':   15,                 # 15    for any damage inflicted by an attack, spell, etc
    'hit':      16,                 # 16    for any rolls to hit an attack
    'save':     17,                 # 17    for any saving throws
    'check':    18,                 # 18    for any skill or ability checks
    'info':     logging.INFO,       # 20    for information that does not fall into any other category
    'simulatn': 21,                 # 21    for any simulating of character decisions
    'action':   22,                 # 22    for any actions done by a character
    'picture':  23,                 # 23    for any pictures
    'turn':     24,                 # 24    for any information about the current character's turn
    'envrmnt':  25,                 # 25    for any information about the battle that is not specific to a character
    'round':    26,                 # 26    for any information about the current round of the battle
    'battle':   27,                 # 27    for any information about the battle as a whole; the highest non-error level
    'warning':  logging.WARNING,    # 30    for unusual behavior that is not an error
    'error':    logging.ERROR,      # 40    for errors
    'critical': logging.CRITICAL,   # 50    for showstopping errors
    'header':   55                  # 55    for the log header which gives important information
}
_INVERTED_DICT = {v: k for k, v in _LEVEL_DICT.items()}
_MAX_LEVEL = list(_LEVEL_DICT.values())[-1]

# Add custom levels to logging module
_DEFAULT_NAMES = ['debug', 'info', 'warning', 'error', 'critical']
for k, v in _LEVEL_DICT.items():
    if k not in _DEFAULT_NAMES:
        logging.addLevelName(v, k.upper())

################################################################################################################################
#========================================================== FUNCTIONS ==========================================================
################################################################################################################################

def _create_formatter(include_name=True):
    """Creates a formatter for the handlers of custom_logger class.

    There are two formats. One with the name.
        13:35:36 logger_name   HEADER : Message
    One without the name.
        13:35:36   HEADER : Message
    Since the date is omitted for brevity, consider including the date in the header/first few lines of the log.

    Args:
        include_name = (bool, optional) If the formatter should include the name. Default=True.

    Returns:
        (obj) A logging.Formatter instance
    """

    if include_name:
        return_val = logging.Formatter(
            fmt='%(asctime)s %(name)s %(levelname)8s : %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        return_val = logging.Formatter(
            fmt='%(asctime)s %(levelname)8s : %(message)s',
            datefmt='%H:%M:%S'
        )
    return return_val
# End _create_formatter function

def add_custom_handler(base_logger, file_name, log_level, include_name=False):
    """Creates a file handler for the custom logger.

    Args:
        - base_logger = (logger) The logger the handler should be added to
        - file_name = (str) Path and file name the handler writes to
        - log_level = (int or str) The logging level of the handler
        - include_name = (bool, optional) If the name of the logger should be included in messages

    Returns:
        No return value
    """

    # Check arg base_logger
    if not isinstance(base_logger, custom_logger):
        raise TypeError('base_logger must be class custom_logger')

    # Check arg file_name
    if not isinstance(file_name, str):
        raise TypeError('file_name must be a str')
    if not file_name.endswith('.log'):
        raise ValueError('file_name must be .log file')

    # Check arg log_level
    if isinstance(log_level, int):
        if log_level not in range(_MAX_LEVEL + 1):
            raise ValueError(f'log_level={log_level} is a level that would log nothing')
        else:
            true_log_level = log_level
    elif isinstance(log_level, str):
        if log_level.lower() not in _LEVEL_DICT.keys():
            raise ValueError(f'log_level={log_level.lower()} is not one of the pre-defined levels')
        else:
            true_log_level = _LEVEL_DICT[log_level.lower()]
    else:
        raise TypeError('log_level must be an int or str')

    log_handler = logging.FileHandler(file_name, mode='a')  # Note that this is 'a' i.e. will append to the log
    log_handler.setLevel(true_log_level)                    # Set the level of the handler
    log_formatter = _create_formatter(include_name)         # Create formatter for file handler
    log_handler.setFormatter(log_formatter)                 # Apply formatter to handler
    base_logger.addHandler(log_handler)                     # Apply handler to logger
    base_logger.header(f'Outputting to file {os.getcwd()}/{file_name}')
# End add_custom_handler function

def create_custom_logger(logger_name, console_level='warning', include_name=True):
    """Creates custom logger and removes default handler to it. Will add own stdout/console handler

    Args:
        - logger_name = (str) Name of the logger. Recommend to be related to the module the logger runs in.
        - console_level = (int or str, optional) Logging level for console prints. Default=warning
        - include_name = (bool, optional) If logger name should be included for console prints. Default=True.

    Returns:
        (obj) custom_logger instance
    """

    # Check arg logger_name
    if not isinstance(logger_name, str):
        raise TypeError('logger_name must be a str')

    # Check arg console_level
    if isinstance(console_level, int):
        if console_level not in range(_MAX_LEVEL + 1):
            warnings.warn(f'console_level={console_level} is a level that would print nothing')
            true_console_level = 99
        else:
            true_console_level = console_level
    elif isinstance(console_level, str):
        if console_level.lower() not in _LEVEL_DICT.keys():
            raise ValueError(f'console_level={console_level.lower()} is not one of the pre-defined levels')
        else:
            true_console_level = _LEVEL_DICT[console_level.lower()]
    else:
        raise TypeError('console_level must be an int or str')

    # Create logger
    return_val = custom_logger(logger_name=logger_name)
    return_val.setLevel(1)  # The logger will capture all levels, and the handlers will filter

    # Remove stdout handler
    #default_handler = return_val.handlers[0]
    #return_val.removeHandler(default_handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(true_console_level)
    console_formatter = _create_formatter(include_name) # Create formatter for console handler
    console_handler.setFormatter(console_formatter)     # Apply formatter to handler
    return_val.addHandler(console_handler)              # Apply handler to logger

    return return_val
# End custom_logger function

def create_custom_logger_with_handler(
    logger_name, file_name,
    log_level='roll', console_level='debug',
    include_name_con=True, include_name_log=False
):
    """Creates custom logger and applies particular handlers to the logger:
        - a file handler that writes to a .log file at level log_level
        - a stdout handler that writes at level console_level

    Args:
        - logger_name = (str) Name of the logger. Recommend to be related to the module the logger runs in.
        - file_name = (str) Name of the file to store all logs to. Must be a .log file.
        - log_level = (str or int, optional) Level of the log file. Default='sample'.
        - console_level = (str or int, optional) Level to output to console. Default='error'.
        - include_name_con = (bool, optional) If console prints should include the logger's name. Default=True.
        - include_name_log = (bool, optional) If the log file should include the logger's name. Default=False.

    Returns:
        (obj) custom_logger instance
    """

    return_val = create_custom_logger(logger_name=logger_name, console_level=console_level, include_name=include_name_con)
    add_custom_handler(return_val, file_name, log_level, include_name_log)
    return return_val
# End create_custom_logger_with_handler function

################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class custom_logger(logging.getLoggerClass()):
    """Custom logger class for scripting. Initialize with create_custom_logger() function.

    Inherited from logging.Logger class. Adds additional log levels to the standard 5:
        debug < sample (new) < info < warning < error < result (new) < critical < header (new)

    Args:
        logger_name = (str) Name of the logger. Recommend to be related to the module the logger runs in.

    Unique methods: Each method corresponds to its level
        - debugall
        - roll
        - resource
        - stat
        - conditn
        - damage
        - hit
        - save
        - check
        - simulatn
        - action
        - picture
        - turn
        - envrmnt
        - round
        - battle
        - header
    """

    def __init__(self, logger_name):
        """Init for custom_logger
 
        Args:
            - logger_name = (str) Name of the logger. Recommend to be related to the module the logger runs in.
        """
        super().__init__(name=logger_name)
    # End __init__

    # If you wish to include additional levels, you must include its corresponding function here
    def debugall(self, message):
        """Send a log message at level DEBUGALL=9"""
        self.log(_LEVEL_DICT['debugall'], message)

    def roll(self, message):
        """Send a log message at level ROLL=11"""
        self.log(_LEVEL_DICT['roll'], message)

    def resource(self, message):
        """Send a log message at level RESOURCE=12"""
        self.log(_LEVEL_DICT['resource'], message)

    def stat(self, message):
        """Send a log message at level STAT=13"""
        self.log(_LEVEL_DICT['stat'], message)

    def conditn(self, message):
        """Send a log message at level CONDITN=14"""
        self.log(_LEVEL_DICT['conditn'], message)

    def damage(self, message):
        """Send a log message at level DAMAGE=15"""
        self.log(_LEVEL_DICT['damage'], message)

    def hit(self, message):
        """Send a log message at level HIT=16"""
        self.log(_LEVEL_DICT['hit'], message)

    def save(self, message):
        """Send a log message at level SAVE=17"""
        self.log(_LEVEL_DICT['save'], message)

    def check(self, message):
        """Send a log message at level CHECK=18"""
        self.log(_LEVEL_DICT['check'], message)

    def simulatn(self, message):
        """Send a log message at level SIMULATN=21"""
        self.log(_LEVEL_DICT['simulatn'], message)

    def action(self, message):
        """Send a log message at level ACTION=22"""
        self.log(_LEVEL_DICT['action'], message)

    def picture(self, message):
        """Send a log message at level PICTURE=23"""
        self.log(_LEVEL_DICT['picture'], message)

    def turn(self, message):
        """Send a log message at level TURN=24"""
        self.log(_LEVEL_DICT['turn'], message)

    def envrmnt(self, message):
        """Send a log message at level ENVRMNT=25"""
        self.log(_LEVEL_DICT['envrmnt'], message)

    def round(self, message):
        """Send a log message at level ROUND=26"""
        self.log(_LEVEL_DICT['round'], message)

    def battle(self, message):
        """Send a log message at level BATTLE=27"""
        self.log(_LEVEL_DICT['battle'], message)

    def header(self, message):
        """Send a log message at level HEADER=55"""
        self.log(_LEVEL_DICT['header'], message)
# End custom_logger class

# eof