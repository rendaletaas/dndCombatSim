# description:  Contains the spell class
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20231016

"""The spell class.

Classes:
    spell
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import json as _json
from rollFunctions import roll as _roll
import customLogging as _clog
from combatCharacter import combatCharacter as _combatCharacter


################################################################################################################################
#====================================================== CUSTOM FUNCTIONS ======================================================
################################################################################################################################
#
#def custom_spell(name, source, target=[], pass_arg=None):
#    """The effect of a custom spell. You should create an if-branch for each spell. See spell.do_spell method.
#
#    Args:
#        - name = (str) The name of the spell
#        - source = (combatCharacter obj) The character that is casting the spell
#        - target = (list of combatCharacter obj, optional) The target characters of the spell. Default=[]
#        - pass_arg = (any, optional) Any additional arguments that the spell needs. Default=None.
#
#    Returns: (dict) Results for each target
#        - Key                           | Value
#        - {name of affected character}  | (str) What happened to the character
#    """
#    if not isinstance(name, str):
#        raise TypeError('arg name must be a str')
#    if not isinstance(source, combatCharacter):
#        raise TypeError('arg source must be a combatCharacter obj')
#    if not isinstance(target, list):
#        raise TypeError('arg target must be a list of combatCharacter obj')
#
#    # Create an if-branch for each custom spell below; the example branch can be removed/overwritten
#    if name == 'unstoppable':
#        source.add_condition('unstoppable', 'indefinite', '3')
#        return {f'{source._name}': 'unstoppable condition'}
#
#    raise ValueError(f'could not find custom spell {name}')
## End custom_spell function
#
################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class spell(object):
    """Handler for a spell that a character casts.
    Spell handling is grouped by level and stored in their respecitve methods.

    Args:
        - name          = (str) The name of the spell
        - in_log        = (customLogging.custom_logger obj) The log for all messages
        - in_roll       = (rollFunctions.roll obj) The roll functions
        - in_json       = (str, optional) The name of the json to get this spell from. Default=spells.json.
        - spell_picture = (bool, optional) If the picture of the spell should be logged. Default=True

    Methods:
        - _log_spell_picture    :log a picture for a spell that does damage
        - do_spell              :Do this spell
        - _cantrip              :Where cantrips are handled
        - _first                :Where first level spells are handled
        - _second               :Where second level spells are handled
        - _third                :Where third level spells are handled
        - _fourth               :Where fourth level spells are handled
        - _fifth                :Where fifth level spells are handled
        - _sixth                :Where sixth level spells are handled
        - _seventh              :Where seventh level spells are handled
        - _eighth               :Where eighth level spells are handled
        - _ninth                :Where ninth level spells are handled
    """
    def __init__(self, name, in_log, in_roll, in_json='spells.json', spell_picture=True):
        """Init for spell

        Args:
            - name          = (str) The name of the spell
            - in_log        = (customLogging.custom_logger obj) The log for all messages
            - in_roll       = (rollFunctions.roll obj) The roll functions
            - in_json       = (str, optional) The name of the json to get this spell from. Default=spells.json.
            - spell_picture = (bool, optional) If the picture of the spell should be logged. Default=True

        Attributes:
            - _name     = (str) The name of this spell
            - _log      = (customLogging.custom_logger obj) The log for all messages
            - _roll     = (rollFunctions.roll obj)
            - _custom   = (bool) If the spell is custom
            - _do_pict  = (bool) If the spell picture should be logged
            - level     = (int) The level of this spell. In range(0,10)
            - school    = (str) The school of this spell
            - cost      = (str) The cost of this spell. One of [regular, bonus, reaction]
            - target    = (list of str) The valid targets of this spell
            - conc      = (bool) If this spell requires concentration
            - duration  = (str) The duration of this spell, in format # {unit}. See combatCharacter.resources.condition class
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        self._name = name
        if not isinstance(in_log, _clog.custom_logger):
            raise TypeError('arg in_log must be a customLogging.custom_logger obj')
        self._log = in_log
        if not isinstance(in_roll, _roll):
            raise TypeError('arg in_roll must be a rollFunctions.roll obj')
        self._roll = in_roll
        if (in_json!='spells.json'):
            self._custom = True
        else:
            self._custom = False
        self._do_pict = bool(spell_picture)

        with open(in_json, 'r') as read_file:
            data = _json.load(read_file)
            if not isinstance(data, dict):
                raise TypeError(f'data in {in_json} must be a dict')
            for i_name, i_dict in data.items():
                if (i_name!=name):
                    continue
                self.level = i_dict['level']
                if (self.level not in range(0,10)):
                    raise ValueError('spell level must be between 0 and 9 inclusive')
                self.school = i_dict['school']
                self.cost = i_dict['cast']
                if (self.cost not in ['regular', 'bonus', 'reaction']):
                    raise ValueError('spell cast/cost must be in [regular, bonus, reaction]')
                self.target = i_dict['target']
                if not isinstance(self.target, list):
                    raise TypeError('spell target must be a list')
                self.conc = i_dict['concentration']
                self.duration = i_dict['duration']
                if not isinstance(self.duration, str):
                    raise ValueError('spell duration must be a str')
                return
    # End __init__

    def _log_spell_picture(self, source, target, dc, save, succeeded, damage_fail, damage_succ, hp_lost, hp):
        """Create a log picture for the spell. This is meant only for spells that do damage.

        Args:
            - source        = (combatCharacter obj) The source of this spell
            - target        = (combatCharacter obj) The target of this spell
            - dc            = (str) The difficulty class of the spell, in format # {ability}. E.g. 12 dex
            - save          = (int) What the target rolled for their saving throw
            - succeeded     = (bool) If the target suceeded the saving throw
            - damage_fail   = (str) The damage of the spell when fail, in format # {type}. E.g. 8 radiant
            - damage_succ   = (str) The damage of the spell when success, in format above.
            - hp_lost       = (int) The amount of HP the target lost
            - hp            = (int) The new HP that the target has

        Returns:
            No return value
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be combatCharacter obj')
        if not isinstance(target, _combatCharacter):
            raise TypeError('arg target must be a combatCharacter obj')
        if not isinstance(dc, str):
            raise TypeError('arg dc must be a str')
        if not isinstance(save, int):
            raise TypeError('arg save must be an int')
        if not isinstance(damage_fail, str):
            raise TypeError('arg damage_fail must be a str')
        if not isinstance(damage_succ, str):
            raise TypeError('arg damage_succ must be a str')
        if not isinstance(hp_lost, int):
            raise TypeError('arg hp_lost must be an int')
        if not isinstance(hp, int):
            raise  TypeError('arg hp must be an int')


        str_list = ['' for i in range(5)]
        # Source
        largest_spacing = max(7, len(source._name), len(self._name))
        str_list[0] += '='*(largest_spacing + 1)
        str_list[1] += f'{source._name:^{largest_spacing}} '
        str_list[2] += f'{self._name:^{largest_spacing}} '
        str_list[3] += f'{dc:^{largest_spacing}} '
        str_list[4] += '='*(largest_spacing + 1)

        # Left arrow
        largest_spacing = len(damage_fail)
        str_list[0] += '='*largest_spacing
        str_list[1] += f'{damage_fail}'
        str_list[2] += '-'*largest_spacing
        str_list[3] += ' '*largest_spacing
        str_list[4] += '='*largest_spacing

        # Save
        str_list[0] += '='*10
        str_list[1] += ' '*10
        str_list[2] += f'---{"xxxx" if succeeded else "----"}---'
        str_list[3] += f' save={save:^3} '
        str_list[4] += '='*10

        # Right arrow
        largest_spacing = max(len(damage_fail), len(damage_succ))
        str_list[0] += '='*(largest_spacing+2)
        str_list[1] += f'{damage_succ if succeeded else damage_fail}  '
        str_list[2] += '-'*largest_spacing + '> '
        str_list[3] += ' '*(largest_spacing+2)
        str_list[4] += '='*(largest_spacing+2)

        # Target
        largest_spacing = max(len(target._name), 6)
        str_list[0] += '='*largest_spacing
        str_list[1] += f'{target._name:^{largest_spacing}}'
        str_list[2] += f'{("-" + str(hp_lost)):^{largest_spacing}}'
        str_list[3] += f'{(str(hp) + " HP"):^{largest_spacing}}'
        str_list[4] += '='*largest_spacing

        # Log
        for i in str_list:
            self._log.picture(i)
    # End _log_spell_picture method

    def do_spell(self, source, target=[], upcast=0, pass_arg=None):
        """Have this spell do its effects

        Args:
            - source    = (combatCharacter obj) The source character of this spell
            - target    = (list of combatCharacter obj) The target characters of this spell
            - upcast    = (int, optional) If not Default=0, will upcast at the specified level.
            - pass_arg  = (any, optional) Any additional args that the spell needs. Default=None

        Returns:
            (dict) The results of the spell
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(upcast, int):
            raise TypeError('arg upcast must be an int')
        if upcast not in range(0, 10):
            raise ValueError('arg upcast must be in 0 to 9 inclusive')
        upcast_diff = upcast - self.level
        # Cantrips/level 0 spells do not reduce the number of spell slots
        if (self.level == 0):
            upcast_diff = 0
        else:
            if (upcast_diff > 0):
                self._log.resource(f'{source._name} is using a {upcast} level spell slot')
                source.char_resources.spell_slots[upcast] -= 1
            else:
                upcast_diff = 0
                self._log.resource(f'{source._name} is using a {self.level} level spell slot')
                source.char_resources.spell_slots[self.level] -= 1

#        if self._custom:
#            return custom_spell(name=self._name, source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        # Cantrips cannot be upcast
        if (self.level == 0):
            return self._cantrip(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 1):
            return self._first(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 2):
            return self._second(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 3):
            return self._third(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 4):
            return self._fourth(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 5):
            return self._fifth(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 6):
            return self._sixth(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 7):
            return self._seventh(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        if (self.level == 8):
            return self._eighth(source=source, target=target, upcast=upcast_diff, pass_arg=pass_arg)
        # Ninth level spells cannot be upcast
        if (self.level == 9):
            return self._ninth(source=source, target=target, pass_arg=pass_arg)
        raise Exception('attribute level was set to something other than 0 to 9 inclusive')
    # End do_spell method

    ################################################################
    #=========================== CANTRIP ===========================
    ################################################################

    def _cantrip(self, source, target=[], pass_arg=None):
        """Where all cantrips (0 level) and spell like features are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list of combatCharacter obj')

        if self._name=='radiance_of_the_dawn':
            return_val = {}
            spell_dc = source.char_stats.get_spell_save()
            for i_target in target:
                if not isinstance(i_target, _combatCharacter):
                    raise TypeError('arg target must be a list of combatCharacter obj')
                tar_save = i_target.char_roll_stat('con save')
                succeeded = tar_save >= spell_dc
                damage = self._roll.roll_d_str(f'2d10+{source.char_stats.class_level["cleric"]}')
                (target_tuple) = i_target.take_damage({'radiant': (damage // 2) if (succeeded) else (damage)})
                if self._do_pict:
                    self._log_spell_picture(
                        source=source, target=i_target,
                        dc=f'{spell_dc} con', save=tar_save, succeeded=succeeded,
                        damage_fail=f'{damage} radiant', damage_succ=f'{damage // 2} radiant',
                        hp_lost=target_tuple[0], hp=target_tuple[1]
                    )
                return_val[i_target._name] = f'now has {target_tuple[1]} hp'
            return return_val

        if self._name=='shillelagh':
            source.add_condition('shillelagh', self.duration)
            return {source._name: 'has shillelagh on their club/quarterstaff'}

        raise Exception(f'logic for cantrip spell {self._name} has not been coded')
    # End _cantrip method

    ################################################################
    #========================= FIRST LEVEL =========================
    ################################################################

    def _first(self, source, target=[], upcast=0, pass_arg=None):
        """Where all first level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for first level spell {self._name} has not been coded')
    # End _first method

    ################################################################
    #======================== SECOND LEVEL ========================
    ################################################################

    def _second(self, source, target=[], upcast=0, pass_arg=None):
        """Where all second level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for second level spell {self._name} has not been coded')
    # End _second method

    ################################################################
    #========================= THIRD LEVEL =========================
    ################################################################

    def _third(self, source, target=[], upcast=0, pass_arg=None):
        """Where all third level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for third level spell {self._name} has not been coded')
    # End _third method

    ################################################################
    #======================== FOURTH LEVEL ========================
    ################################################################

    def _fourth(self, source, target=[], upcast=0, pass_arg=None):
        """Where all fourth level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for fourth level spell {self._name} has not been coded')
    # End _fourth method

    ################################################################
    #========================= FIFTH LEVEL =========================
    ################################################################

    def _fifth(self, source, target=[], upcast=0, pass_arg=None):
        """Where all fifth level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for fifth level spell {self._name} has not been coded')
    # End _fifth method

    ################################################################
    #========================= SIXTH LEVEL =========================
    ################################################################

    def _sixth(self, source, target=[], upcast=0, pass_arg=None):
        """Where all sixth level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for sixth level spell {self._name} has not been coded')
    # End _sixth method

    ################################################################
    #======================== SEVENTH LEVEL ========================
    ################################################################

    def _seventh(self, source, target=[], upcast=0, pass_arg=None):
        """Where all seventh level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for seventh level spell {self._name} has not been coded')
    # End _seventh method

    ################################################################
    #======================== EIGHTH LEVEL ========================
    ################################################################

    def _eighth(self, source, target=[], upcast=0, pass_arg=None):
        """Where all eighth level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for eigth level spell {self._name} has not been coded')
    # End _eighth method

    ################################################################
    #========================= NINTH LEVEL =========================
    ################################################################

    def _ninth(self, source, target=[], pass_arg=None):
        """Where all ninth level spells are"""
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for ninth level spell {self._name} has not been coded')
    # End _ninth method
# End spell class

# eof