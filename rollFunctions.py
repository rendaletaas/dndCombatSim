# description:  Functions for rolling dice
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20231016

"""Functions for rolling dice.

Classes:
    roll
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import random as _random
import customLogging as _clog

################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class roll(object):
    """Class containing all the functions to roll a dice.

    Args:
        - in_log = (customLogging.custom_logger obj) The log for all messages

    Methods:
        - roll_20       :roll a d20
        - roll_d        :roll a #d#+#
        - _parse_d      :(static) parse a dice string
        - roll_d_str    :parse a dice string then roll for it
    """
    def __init__(self, in_log):
        """Init for roll

        Args:
            - in_log = (customLogging.custom_logger obj) The log for all messages

        Attributes:
            - _log  = (customLogging.custom_logger obj) The log that all the messages that the methods will write to
        """
        if not isinstance(in_log, _clog.custom_logger):
            raise TypeError('arg in_log must be a customLogging.custom_logger obj')
        self._log = in_log
    # End __init__

    def roll_20(self, adv=0):
        """Will get a random number between 1 and 20 inclusive

        Args:
            - adv = (int) If there should be advantage/disadvantage on the roll. Advantage is > 0, disadvantage < 0. Default=0

        Returns:
            (int) A number rolled
        """
        if not isinstance(adv, int):
            raise TypeError('arg adv must be an int')
        if (adv == 0):
            return_val = _random.randint(1,20)
            self._log.roll(f'd20={return_val}')
        elif (adv > 0):
            roll1 = _random.randint(1,20)
            roll2 = _random.randint(1,20)
            return_val = max(roll1, roll2)
            self._log.roll(f'd20(adv)={return_val} ({roll1} or {roll2})')
        else:
            roll1 = _random.randint(1,20)
            roll2 = _random.randint(1,20)
            return_val = min(roll1, roll2)
            self._log.roll(f'd20(dis)={return_val} ({roll1} or {roll2})')
        return return_val
    # End roll_20 method

    def roll_d(self, faces, num_dice=1, supress=False):
        """Will roll the specified number of dice with the specified number of faces.

        Args:
            - faces     = (int) The number of faces on each die. Must be 1 or greater, else will return 0
            - num_dice  = (int, optional) The number of dice to roll. Must be 1 or greater, else will return 0. Default=1.
            - supress   = (bool, optional) If the log message should be supressed. Default=False.

        Returns:
            (int) 0 if any of the rules above are broken. Otherwise the result of the random roll.
        """
        if not isinstance(faces, int):
            raise TypeError('faces must be an int')
        if not isinstance(num_dice, int):
            raise TypeError('num_dice must be an int')
        if (faces < 1):
            if not supress:
                self._log.roll('d0=0')
            return 0
        if (num_dice < 1):
            if not supress:
                self._log.roll('0d=0')
            return 0
        
        if (faces == 1):
            if not supress:
                self._log.roll(f'{num_dice}d1={num_dice}')
            return num_dice
        
        return_val = 0
        log_str = ''
        for i in range(num_dice):
            roll_val = _random.randint(1, faces)
            log_str += f'd{faces}={roll_val} '
            return_val += roll_val
        if not supress:
            self._log.roll(log_str)
        return return_val
    # End roll_d method

    @staticmethod
    def _parse_d(d_str):
        """Will parse the string in #d# or #d#+# format

        Args:
            - d_str = (str) The string to parse

        Returns: (tuple of int)
            - (int) The number of faces on each die
            - (int) The number of dice to roll
            - (int) The modifier to the total
        """
        if not isinstance(d_str, str):
            raise TypeError('d_str must be a str')
        plus_split = d_str.split('+')
        if (len(plus_split)==1):
            mod = 0
        elif (len(plus_split)==2):
            mod = int(plus_split[1])
        else:
            raise ValueError(f'd_str={d_str} had too many +')
        d_split = plus_split[0].split('d')
        if (len(d_split)!=2):
            raise ValueError(f'd_str={d_str} did not have a d or too many to separate')
        return (int(d_split[1]), int(d_split[0]), mod)
    # End _parse_d method

    def roll_d_str(self, d_str):
        """Will parse the string in #d# or #d#+# format, then do the roll specified of that string

        Args:
            - d_str = (str) The string to parse

        Returns:
            (int) The total of the roll
        """
        parse_tuple = self._parse_d(d_str)
        roll_result = self.roll_d(parse_tuple[0], parse_tuple[1], True)
        return_val = roll_result + parse_tuple[2]
        self._log.roll(f'{d_str}={roll_result}+{parse_tuple[2]}={return_val}')
        return return_val
    # End roll_d_str method
# End roll class

# eof