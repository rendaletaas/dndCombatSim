#!/usr/bin/env python3
# description:  Script to simulate DnD battles
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20230930

"""Script that will simulate DnD battles.
To do:
    Movement
    Wild shape
    Shillelagh

Functions:
    roll_20
    roll_d
    _parse_d
    roll_d_str
    _create_attack
Classes:
    attack
    spell
    battleChar
        stats
        resources
        actionChooser
    battleStage
        characterAction
Main in this file
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import time
import random
import math
import json
import custom_logging

################################################################################################################################
#=========================================================== SET UP ===========================================================
################################################################################################################################

ABILITIES = ['str', 'dex', 'con', 'int', 'wis', 'cha']
SKILLS = {
    'athletics':'str',
    'acrobatics':'dex', 'sleight_of_hand':'dex', 'stealth':'dex',
    'arcana':'int', 'history':'int', 'investigation':'int', 'nature':'int', 'religion':'int',
    'animal_handling':'wis', 'insight':'wis', 'medicine':'wis', 'perception':'wis', 'survival':'wis',
    'deception':'cha', 'intimidation':'cha', 'performance':'cha', 'persuasion': 'cha'
}
AUTO_SUCCESS = 100
AUTO_FAIL = -100
TIME_UNITS = {'round':6, 'second':1, 'minute':60, 'hour':3600, 'day':86400, 'sont':3, 'eont':3}

current_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
log = custom_logging.create_custom_logger_with_handler('battle', f'battle{current_time}.log', 'debug', 'conditn', False, False)
#log = custom_logging.create_custom_logger_with_handler('battle', f'battle{current_time}.log', 'debug', 'picture', False, False)

################################################################################################################################
#========================================================== FUNCTIONS ==========================================================
################################################################################################################################

def roll_20(adv='norm'):
    """Will get a random number between 1 and 20 inclusive

    Args:
        - adv = (str) If there should be advantage/disadvantage on the roll. One of [norm, adv, dis]. Default=norm.

    Returns:
        (int) A number rolled
    """
    if (adv=='norm'):
        return_val = random.randint(1,20)
        log.roll(f'd20={return_val}')
    elif (adv=='adv'):
        return_val = max(random.randint(1,20), random.randint(1,20))
        log.roll(f'd20(adv)={return_val}')
    else:
        return_val = min(random.randint(1,20), random.randint(1,20))
        log.roll(f'd20(dis)={return_val}')
    return return_val
# End roll_20 function

def roll_d(faces, num_dice=1, supress=False):
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
            log.roll('d0=0')
        return 0
    if (num_dice < 1):
        if not supress:
            log.roll('0d=0')
        return 0
    
    if (faces == 1):
        if not supress:
            log.roll(f'{num_dice}d1={num_dice}')
        return num_dice
    
    return_val = 0
    log_str = ''
    for i in range(num_dice):
        roll_val = random.randint(1, faces)
        log_str += f'd{faces}={roll_val} '
        return_val += roll_val
    if not supress:
        log.roll(log_str)
    return return_val
# End roll_d function

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
    else:
        mod = int(plus_split[1])
    d_split = plus_split[0].split('d')
    return (int(d_split[1]), int(d_split[0]), mod)
# End _parse_d function

def roll_d_str(d_str):
    """Will parse the string in #d# or #d#+# format, then do the roll specified of that string

    Args:
        - d_str = (str) The string to parse

    Returns:
        (int) The total of the roll
    """
    parse_tuple = _parse_d(d_str)
    roll_result = roll_d(parse_tuple[0], parse_tuple[1], True)
    return_val = roll_result + parse_tuple[2]
    log.roll(f'{d_str}={roll_result}+{parse_tuple[2]}={return_val}')
    return return_val
# End roll_d_str function

def _create_attack(name, in_json='attacks.json'):
    """Creates an attack obj automatically from the specified json for use by another object

    Args:
        - name      = (str) Name of the attack to look for
        - in_json   = (str, optional) Path of the json to look for attack. Default=attacks.json

    Returns:
        (attack obj) The attack
    """
    log.debugall(f'attempting to create attack {name}')
    with open(in_json, 'r') as read_file:
        data = json.load(read_file)
        for i_attack in data:
            if (name==i_attack['name']):
                return attack(
                    name=i_attack['name'],
                    ability=i_attack['ability'],
                    damagedice=i_attack['damagedice'],
                    prof=i_attack['type'],
                    hitmod=i_attack['hitmod'],
                    multi=i_attack['multi'],
                    properties=i_attack['properties'] if ('properties' in i_attack) else []
                )
    raise Exception(f'could not find attack {name} in {in_json}')
# End _create_attack function

################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class attack(object):
    """Possible attacks.

    Args:
        - name = (str) Name of the attack
        - ability = (str) Ability that this attack uses for its attack roll. One of [str, dex, con, int, wis, cha]
        - damagedice = (list of str) A list of each dice for the damage, in {ability} #d#+# {type} format. Example: str 1d12+1 slashing. You can also omit ability
            and a + modifier.
        - prof = (list of str) What type of attack this is to determine if user has proficiency
        - hitmod = (int, optional) Additional modifier to the attack roll. Default=0.
        - multi = (int, optional) If not Default=1, this is a multiattack that will do individual attack rolls.
        - properties = (list of str, optional) Additional properties for this attack. Default=[]

    Methods:
        - roll_hit: have the attack roll to hit
        - roll_damage: have the attack roll for damage
    """
    def __init__(self, name, ability, damagedice, prof, hitmod=0, multi=1, properties=[]):
        """Init for attack

        Attributes:
            - name          = (str) The name of the attack
            - _ability      = (str) The ability used for the attack roll
            - _damage       = (list of dict) Each dice used for damage
                - Key   | Value
                - num   | (int) Number of dice
                - fac   | (int) Faces of the die
                - mod   | (int) Modifier of the damage
                - abl   | (str) Ability to add to damage mod. One of ['', str, dex, con, int, wis, cha].
                - typ   | (str) Type of damage
            - _prof         = (set of str) The type of attack this is to determine if the user has proficiency
            - _hitmod       = (int) The modifier to the attack roll
            - _multi        = (int) The number of attacks for a multiattack. If 1, this is a single attack.
            - _properties   = (list of str) The properties of this attack
            - _used_ability = (str) The ability that was used for the last roll, for finesse
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        self.name = name

        if (ability not in ABILITIES):
            raise ValueError(f'{ability} is not an ability')
        self._ability = ability

        self._damage = []
        if not isinstance(damagedice, list):
            raise TypeError('arg damagedice must be a list')
        for i_die in damagedice:
            if not isinstance(i_die, str):
                raise TypeError('arg damagedice must be a list of str')
            str_split = i_die.split(' ')
            if (len(str_split)==2):
                mod_ability = ''
                parse_tuple = _parse_d(str_split[0])
            else:
                mod_ability = str_split[0]
                parse_tuple = _parse_d(str_split[1])
            self._damage.append({
                'num': parse_tuple[1], 'fac': parse_tuple[0], 'mod': parse_tuple[2], 'abl': mod_ability, 'typ': str_split[-1]
            })

        if not isinstance(prof, list):
            raise TypeError('arg prof must be a list')
        self._prof = set(prof)

        if not isinstance(hitmod, int):
            raise TypeError('arg hitmod must be an int')
        self._hitmod = hitmod

        if not isinstance(multi, int):
            raise TypeError('arg multi must be an int')
        self._multi = multi

        if not isinstance(properties, list):
            raise TypeError('arg properties must be a list of str')
        self._properties = properties
        self._last_used = ''
    # End __init__

    def roll_hit(self, character, adv='norm', improved=False):
        """Will do an attack roll with this attack

        Args:
            - character = (battleChar obj) The character doing this attack
            - adv = (str, optional) If the attack roll has advantage or disadvantage. One of [norm, adv, dis]. Default=norm.
            - improved = (bool, optional) If this has improved critical feat

        Returns: (tuple)
            - (str) If the hit was a critical hit/miss. One of [norm, hit, miss]
            - (int) The total rolled for the attack roll
        """
        if not isinstance(character, battleChar):
            raise TypeError('arg character must be a battleChar obj')
        
        # Roll d20
        roll = roll_20(adv=adv)
        if (roll == 1):
            log.hit(f'{character._name} using {self.name} rolled a critical miss!')
            return ('miss', 0)
        if ((roll == 20) or ((roll == 19) and (improved))):
            log.hit(f'{character._name} using {self.name} rolled a critical hit!')
            return ('hit', 20)
        
        # Check for bardic inspiration
        if ('bardic_inspiration' in character.char_resources.cond):
            bi_roll = roll_d_str(character.char_resources.cond['bardic_inspiration']._properties)
            log.action(f'{character._name} is using their bardic inspiration and rolled a {bi_roll}')
            roll += bi_roll
            character.char_resources.remove_condition('bardic_inspiration')
        
        # Handle properties
        other_mod = 0
        if (
            ('finesse' in self._properties) or
            (('monk_weapon' in self._properties) and ('monk' in character.char_stats.class_level))
        ):
            use_ability = 'dex' if (character.char_stats.dex > character.char_stats.str) else 'str'
            ability_mod = character.char_stats.get_mod(use_ability)
            self._last_used = use_ability
            log.simulatn(f'{character._name} is using {use_ability} for {self.name}')
        else:
            ability_mod = character.char_stats.get_mod(self._ability)
        if (('simple_ranged_weapon' in self._prof) or ('martial_ranged_weapon' in self._prof)):
            if ('fighting_style' in character.char_stats.property):
                if (character.char_stats.property['fighting_style']=='archery'):
                    log.debug(f'{character._name} gets a +2 due to archery')
                    other_mod += 2

        # Get total
        if (self._prof=={"all"}):
            prof_mod = character.char_stats.prof
        else:
            prof_mod = 0 if (self._prof.isdisjoint(set(character.char_stats.tools))) else character.char_stats.prof
        self_mod = self._hitmod
        log.debugall(f'{self.name} roll={roll} self={self_mod} prof={prof_mod} other={other_mod}')
        modifier = ability_mod + prof_mod + self._hitmod + other_mod
        log.hit(f'{character._name} using {self.name} rolled a {roll}+{modifier} to hit')
        return ('norm', roll + modifier)
    # End roll_hit method

    def roll_damage(self, char_obj, offhand=False, crit=False):
        """Will do a damage roll with this attack

        Args:
            - char_obj  = (battleChar) The user's object
            - offhand   = (bool, optional) If the attack was made with the offhand
            - crit      = (bool, optional) If the attack was a critical hit

        Returns:
            - (dict) All the damage of the attack, by type
                - Key               | Value
                - {type of damage}  | (int) Total value of damage of that type
        """
        if not isinstance(char_obj, battleChar):
            raise TypeError('arg char_obj must be a battleChar.stats obj')

        damage_list = self._damage

        # Get additional forms of damage
        if ('genies_wrath' in char_obj.char_resources.miscellaneous):
            if (char_obj.char_resources.miscellaneous['genies_wrath']):
                log.action(f'{char_obj._name} is using genies wrath to increase damage')
                split_list = char_obj.char_stats.property['patron'].split('_')
                if (split_list[-1]=='dao'):
                    genie_type = 'm_bludgeoning'
                elif (split_list[-1]=='djinni'):
                    genie_type = 'thunder'
                elif (split_list[-1]=='efreeti'):
                    genie_type = 'fire'
                elif (split_list[-1]=='marid'):
                    genie_type = 'cold'
                else:
                    raise ValueError(f'{char_obj._name} has an invalid genie patron')
                damage_list.append({'num':0, 'fac':0, 'mod':char_obj.char_stats.prof, 'abl':'', 'typ':genie_type})
                char_obj.char_resources.miscellaneous['genies_wrath'] = 0

        # Iterate through all damage
        return_val = {}
        for i_damage in damage_list:
            if (i_damage['typ'] not in return_val):
                return_val[i_damage['typ']] = 0

            # Roll for damage
            roll = roll_d(i_damage['fac'], (2 if crit else 1) * i_damage['num'])

            # Handle properties
            if (
                (i_damage['abl'] in ['str', 'dex']) and (
                    ('finesse' in self._properties) or
                    (('monk_weapon' in self._properties) and ('monk' in char_obj.char_stats.class_level))
                )
            ):
                use_ability = self._last_used
            else:
                use_ability = i_damage['abl']

            # Get total
            ability_mod = char_obj.char_stats.get_mod(use_ability) if use_ability else 0
            log.debugall(f'type={i_damage["typ"]} roll={roll} self={i_damage["mod"]} ability={ability_mod}')
            return_val[i_damage['typ']] += roll + (min(ability_mod, 0) if offhand else ability_mod) + i_damage['mod']

        # Log damage
        printstr = f'{self.name} did'
        for i_key, i_value in return_val.items():
            printstr += f' {i_value} {i_key} +'
        log.damage(printstr[:-1] + 'damage')
        return return_val
    # End roll_damage method
# End attack class

class spell(object):
    """Handler for a spell that a character casts.
    Spell handling is grouped by level and stored in their respecitve methods.

    Args:
        - name      = (str) The name of the spell
        - in_json   = (str, optional) The name of the json to get this spell from. Default=spells.json.

    Methods:
        - do_spell: Do this spell
        - _cantrip: Where cantrips are handled
        - _first:   Where first level spells are handled
        - _second:  Where second level spells are handled
        - _third:   Where third level spells are handled
        - _fourth:  Where fourth level spells are handled
        - _fifth:   Where fifth level spells are handled
        - _sixth:   Where sixth level spells are handled
        - _seventh: Where seventh level spells are handled
        - _eighth:  Where eighth level spells are handled
        - _ninth:   Where ninth level spells are handled
    """
    def __init__(self, name, in_json='spells.json'):
        """Init for spell

        Attributes:
            - _name     = (str) The name of this spell
            - level     = (int) The level of this spell. In range(0,10)
            - school    = (str) The school of this spell
            - cost      = (str) The cost of this spell. One of [regular, bonus, reaction]
            - target    = (list of str) The valid targets of this spell
            - conc      = (bool) If this spell requires concentration
            - duration  = (str) The duration of this spell, in format # {unit}. See battleChar.resources.condition class
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        self._name = name

        with open(in_json, 'r') as read_file:
            data = json.load(read_file)
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

    def do_spell(self, source, target=[], pass_arg=None):
        """Have this spell do its effects

        Args:
            - source    = (battleChar obj) The source character of this spell
            - target    = (list of battleChar obj) The target characters of this spell
            - pass_arg  = (any, optional) Any additional args that the spell needs. Default=None

        Returns:
            (dict) The results of the spell
        """
        if (self.level == 0):
            return self._cantrip(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 1):
            return self._first(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 2):
            return self._second(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 3):
            return self._third(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 4):
            return self._fourth(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 5):
            return self._fifth(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 6):
            return self._sixth(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 7):
            return self._seventh(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 8):
            return self._eighth(source=source, target=target, pass_arg=pass_arg)
        if (self.level == 9):
            return self._ninth(source=source, target=target, pass_arg=pass_arg)
        raise Exception('attribute level was set to something other than 0 to 9 inclusive')
    # End do_spell method

    def _cantrip(self, source, target=[], pass_arg=None):
        """Where all cantrips (0 level) are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        if self._name=='shillelagh':
            source.char_resources.add_condition('shillelagh', '1 minute')
            return {source._name: 'shillelagh'}

        raise Exception(f'logic for cantrip spell {self._name} has not been coded')
    # End _cantrip method

    def _first(self, source, target=[], pass_arg=None):
        """Where all first level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for first level spell {self._name} has not been coded')
    # End _first method

    def _second(self, source, target=[], pass_arg=None):
        """Where all second level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for second level spell {self._name} has not been coded')
    # End _second method

    def _third(self, source, target=[], pass_arg=None):
        """Where all third level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for third level spell {self._name} has not been coded')
    # End _third method

    def _fourth(self, source, target=[], pass_arg=None):
        """Where all fourth level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for fourth level spell {self._name} has not been coded')
    # End _fourth method

    def _fifth(self, source, target=[], pass_arg=None):
        """Where all fifth level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for fifth level spell {self._name} has not been coded')
    # End _fifth method

    def _sixth(self, source, target=[], pass_arg=None):
        """Where all sixth level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for sixth level spell {self._name} has not been coded')
    # End _sixth method

    def _seventh(self, source, target=[], pass_arg=None):
        """Where all seventh level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for seventh level spell {self._name} has not been coded')
    # End _seventh method

    def _eighth(self, source, target=[], pass_arg=None):
        """Where all eighth level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for eigth level spell {self._name} has not been coded')
    # End _eighth method

    def _ninth(self, source, target=[], pass_arg=None):
        """Where all ninth level spells are"""
        if not isinstance(source, battleChar):
            raise TypeError('arg source must be a battleChar obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')
        
        raise Exception(f'logic for ninth level spell {self._name} has not been coded')
    # End _ninth method
# End spell class

class battleChar(object):
    """Character that is within the battle. Anything that would take or deal damage in the battle.

    Args:
        - name      = (str) The name of this character
        - team      = (str) The team the character is on. One of [pc, ally, enemy]
        - stat_dict = (dict, optional) The stats to automatically add. See stats.set_stats method. Default={}.
        - act_cat   = (list of str, optional) Which category of actions to automatically include. Default=[].
        - act_inc   = (list of str, optional) Which individual actions to automatically include. Default=[].

    Classes:
        - stats:            object to hold the stats for this character
        - resources:        object to hold the resources for this character
            - condition:    object to hold a condition for this character
        - actionChooser:    object that gives a character's available actions and the bias they will choose that aciton

    Methods:
        - take_damage:          have character take damage
        - add_attack:           add an attack to the character
        - set_stats:            sets the stats of the character
        - roll_stat:            have a character do a roll for a stat
        - get_advantage:        checks to see if character has or grants advantage
        - get_random_attack:    gets a random attack this character can do
        - get_random_action:    gets a random action dependent on characters conditions
    """
    def __init__(self, name, team, stat_dict={}, act_cat=[], act_inc=[]):
        """Init for battleChar

        Attributes:
            - _name             = (str) The character's name
            - team              = (str) The character's team. One of [pc, ally, enemy]
            - char_stats        = (stats obj) The stats of this character
            - char_resources    = (resources obj) The resources of this character
            - char_actions      = (actionChooser obj) The actions available to this character
            - char_attacks      = (dict of int) The attacks of the character
                - Key               | Value
                - {name of attack}  | (int) Bias of this attack
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        self._name = name
        if (team == 'pc'):
            self.team = 'pc'
        elif (team == 'ally'):
            self.team = 'ally'
        else:
            self.team = 'enemy'

        # Create objects for character
        self.char_stats = self.stats(name=name)
        self.char_stats.set_stats(stat_dict=stat_dict)
        self.char_resources = self.resources(name=name, in_stats=self.char_stats)
        self.char_actions = self.actionChooser(name=name, in_json='actions.json', category=act_cat, include_action=act_inc)

        # Automatically get attacks of class
        self.char_attacks = {}
        if self.char_stats.class_level:
            for i_class, i_level in self.char_stats.class_level.items():
                if (i_class=='monk'):
                    if (i_level >= 17):
                        self.add_attack({f'unarmed_10': 0})
                    elif (i_level >= 11):
                        self.add_attack({f'unarmed_8': 0})
                    elif (i_level >= 5):
                        self.add_attack({f'unarmed_6': 0})
                    else:
                        self.add_attack({f'unarmed_4': 0})
                # As a fail safe, add the regular unarmed strike
                else:
                    self.add_attack({'unarmed':0})
        else:
            self.add_attack({'unarmed':0})

        log.debug(f'Created character {name} on team {team}')
    # End __init__

    class stats(object):
        """The stats of this character. In general, values that remain fairly static are stored here.
        There should only be one instance of this in a character.

        Args:
            - name = (str) The character's name

        Methods:
            - add_property: add properties to attribute property
            - set_stats:    set the stats of the character
            - get_mod:      get the modifier of an ability of the character
            - roll_ability: have the character roll for an ability check
            - roll_skill:   have the character roll for a skill check
            - roll_save:    have the character roll for a saving throw
        """
        def __init__(self, name):
            """Init of stats

            Attributes:
                - _name         = (str) The character's name
                - level         = (int) This character's level. If -1, this character is an NPC.
                - class_level   = (dict of int) The levels of each class the character has
                - prof          = (int) This character's proficiency modifier
                - str           = (int) This character's strength score
                - dex           = (int) This character's dexterity score
                - con           = (int) This character's constitution score
                - int           = (int) This character's intelligence score
                - wis           = (int) This character's wisdom score
                - cha           = (int) This character's charisma score
                - skills        = (list of str) The skills that the character is proficient in
                - expert        = (list of str) The skills that the character has expertise in
                - ac            = (int) This character's armor class
                - max_hp        = (int) This character's maximum HP
                - hit_dice      = (list of str) The hit dice of this character
                - tot_hd        = (int) The total count of hit dice of this character
                - saves         = (list of str) The saving throws this character is proficient in
                - speed         = (int) This character's movement speed
                - spellcast     = (str) The spellcasting ability of this character
                - slots         = (dict) The spell slots of this character
                    - Key       | Value
                    - {level}   | (int) The maximum number of slots
                - tools         = (list of str) The tools, weapons, armor, equipment, etc this character is proficient in
                - imm           = (list of str) This character's damage immunities
                - res           = (list of str) This character's damage resistances
                - vul           = (list of str) This character's damage vulnerabilities
                - condimm       = (list of str) This character's condition immunities
                - property      = (dict) Any additional stats or properties for the character
            """
            self._name = name
            self.level = -1
            self.class_level = {}
            self.prof = 0
            self.str = 10
            self.dex = 10
            self.con = 10
            self.int = 10
            self.wis = 10
            self.cha = 10
            self.skills = []
            self.expert = []
            self.ac = 10
            self.max_hp = 1
            self.hit_dice = []
            self.tot_hd = 0
            self.saves = []
            self.speed = 30
            self.spellcast = 'int'
            self.slots = {}
            self.tools = []
            self.imm = []
            self.res = []
            self.vul = []
            self.condimm = []
            self.property = {}
        # End __init__

        def add_property(self, in_dict):
            """Adding additional property to stats, in attribute property

            Args:
                - in_dict = (dict) The property to add. Key should be a string, but value can be any type

            Returns:
                No return value
            """
            if not isinstance(in_dict, dict):
                raise TypeError('arg in_dict must be a dict')
            self.property.update(in_dict)
        # End add_property method

        def set_stats(self, stat_dict):
            """Sets the stats of the character.

            Args:
                - stat_dict = (dict) The key is the attribute to change, the value is the new value. Should keep the same format for each
                    attribute. See __init__ doctring for format.

            Returns:
                No return value
            """
            if not isinstance(stat_dict, dict):
                raise TypeError('arg stat_dict must be a dict')
            if ('level' in stat_dict):
                self.level = stat_dict['level']
            if ('class_level' in stat_dict):
                self.class_level = stat_dict['class_level']
                # Automatically get proficiencies for class
                for i_class in stat_dict['class_level']:
                    add_list = []
                    if (i_class == 'bard'):
                        add_list += ['light_armor', 'simple_weapon', 'hand crossbow', 'longsword', 'rapier', 'shortsword']
                    if (i_class == 'druid'):
                        add_list += ['light_armor', 'medium_armor', 'shield', 'club', 'dagger', 'dart', 'javelin', 'mace', 'quarterstaff', 'scimitar', 'sickle', 'sling', 'spear', 'herbalism_kit']
                    if (i_class == 'fighter'):
                        add_list += ['light_armor', 'medium_armor', 'heavy_armor', 'shield', 'simple_weapon', 'martial_weapon']
                    if (i_class == 'warlock'):
                        add_list += ['light_armor', 'simple_weapon']
                    for i in add_list:
                        if (i not in self.tools):
                            self.tools.append(i)
            if ('prof' in stat_dict):
                self.prof = stat_dict['prof']
            if ('str' in stat_dict):
                self.str = stat_dict['str']
            if ('dex' in stat_dict):
                self.dex = stat_dict['dex']
            if ('con' in stat_dict):
                self.con = stat_dict['con']
            if ('int' in stat_dict):
                self.int = stat_dict['int']
            if ('wis' in stat_dict):
                self.wis = stat_dict['wis']
            if ('cha' in stat_dict):
                self.cha = stat_dict['cha']
            if ('skills' in stat_dict):
                self.skills = stat_dict['skills']
            if ('ac' in stat_dict):
                self.ac = stat_dict['ac']
            if ('max_hp' in stat_dict):
                if isinstance(stat_dict['max_hp'], str):
                    self.max_hp = roll_d_str(stat_dict['max_hp'])
                else:
                    self.max_hp = stat_dict['max_hp']
            if ('hit_dice' in stat_dict):
                self.hit_dice = stat_dict['hit_dice']
                self.tot_hd = 0
                for i_str in self.hit_dice:
                    parse_tuple = _parse_d(i_str)
                    self.tot_hd += parse_tuple[1]
            if ('saves' in stat_dict):
                self.saves = stat_dict['saves']
            if ('speed' in stat_dict):
                self.speed = stat_dict['speed']
            if ('spellcast' in stat_dict):
                self.spellcast = stat_dict['spellcast']
            if ('slots' in stat_dict):
                self.slots = {}
                for i_k, i_v in stat_dict['slots'].items():
                    self.slots[int(i_k)] = i_v
            if ('tools' in stat_dict):
                self.tools += stat_dict['tools']
            if ('imm' in stat_dict):
                self.imm = stat_dict['imm']
            if ('res' in stat_dict):
                self.res = stat_dict['res']
            if ('vul' in stat_dict):
                self.vul = stat_dict['vul']
            if ('condimm' in stat_dict):
                self.condimm = stat_dict['condimm']
            log.debug(f'updated stats of {self._name}')
        # End set stats method

        def get_mod(self, ability):
            """Will get the modifier of the specified ability of the character

            Args:
                - ability = (str) The ability score to get. One of [str, dex, con, int, wis, cha]

            Returns:
                (int) The modifier the character has of that ability.
            """
            if (ability not in ABILITIES):
                raise ValueError(f'{ability} is not an ability')
            if (ability=='str'):
                ability_score = self.str
            elif (ability=='dex'):
                ability_score = self.dex
            elif (ability=='con'):
                ability_score = self.con
            elif (ability=='int'):
                ability_score = self.int
            elif (ability=='wis'):
                ability_score = self.wis
            else:
                ability_score = self.cha
            return (ability_score-10) // 2
        # End get_mod method

        def roll_ability(self, ability, adv='norm', suppress=False, apply_bi=True):
            """Will have the character make an ability check of the specified ability

            Args:
                - ability   = (str) The ability score to that the character is to roll for. One of [str, dex, con, int, wis, cha]
                - adv       = (str, optional) If there should be advantage/disadvantage on the roll. One of [norm, adv, dis]. Default=norm.
                - suppress  = (bool, optional) If the log message should be supressed. Default=False.
                - apply_bi  = (bool, optional) If check for bardic inspiration should be done. Default=True.

            Returns:
                (int) The result of the roll
            """
            if (ability not in ABILITIES):
                raise ValueError(f'{ability} is not an ability')
            return_val = roll_20(adv=adv) + self.get_mod(ability=ability)
            if (apply_bi and ('bard' in self.class_level)):
                if (self.class_level['bard'] >= 2):
                    return_val += self.prof // 2
            if not suppress:
                log.check(f'{self._name} rolls a {return_val} for a {ability} check')
            return return_val
        # End roll_ability method

        def roll_skill(self, skill, adv='norm'):
            """Will have the character make a skill check of the specified skill

            Args:
                - skill = (str) The skill that the character is to roll for
                - adv = (str, optional) If there should be advantage/disadvantage on the roll. One of [norm, adv, dis]. Default=norm.

            Returns:
                (int) The result of the roll
            """
            if (skill not in SKILLS):
                raise ValueError(f'{skill} is not a skill')
            return_val = self.roll_ability(SKILLS[skill], adv=adv, suppress=True, apply_bi=False)
            if (skill in self.expert):
                return_val += 2 * self.prof
            elif (skill in self.skills):
                return_val += self.prof
            elif ('bard' in self.class_level):
                if (self.class_level['bard'] >= 2):
                    return_val += self.prof // 2
            log.check(f'{self._name} rolls a {return_val} for a {skill} check')
            return return_val
        # End roll_skill method

        def roll_save(self, ability, adv='norm'):
            """Will have the character make a saving throw of the specified ability

            Args:
                - ability = (str) The ability score to that the character is to roll for. One of [str, dex, con, int, wis, cha]
                - adv = (str, optional) If there should be advantage/disadvantage on the roll. One of [norm, adv, dis]. Default=norm.

            Returns:
                (int) The result of the roll
            """
            return_val = self.roll_ability(ability=ability, adv=adv, suppress=True) + (self.prof if ability in self.saves else 0)
            log.save(f'{self._name} rolls a {return_val} for a {ability} saving throw')
            return return_val
        # End roll_save method
    # End stats class

    class resources(object):
        """The resources of this character. These are values that will constantly change during battle. Anything that has
        a duration should also be stored here.
        There should only be one instance of this in a character.

        Args:
            - name = (str) The character's name
            - in_stats = (stats obj) The stats of the character

        Classes:
            condition: object to hold a condition on a character

        Methods:
            - add_miscellaneous:        add new key to attribute miscellaneous
            - add_resource:             update attributes
            - restore_all_slots:        restore all spell slots
            - effect_on_gain:           effects when gaining a condtion
            - effect_on_check:          effects when checking a condtion
            - effect_on_loss:           effects when losing a condition
            - add_condition:            adds condition to character
            - del_condition:            removes condition of character
            - heal_hp:                  restore HP to the character
            - remove_hp:                remove HP from the character
            - check_all_conditions:     do check_condtion method on all condtions
            - long_rest:                refill all resources that replenish on a long rest
            - short_rest:               refill all resources that replenish on a short rest
            - get_resources_for_round:  get all the resources the character has for the round
            - start_turn:               refill all resources that replenish on their turn, and trigger certain start of turn effects
            - end_turn:                 end the turn of the character, which will end certain effects
            - _gain_death_save:         have the character gain a death save roll
            - do_death_save:            have character do a death save
        """
        def __init__(self, name, in_stats):
            """Init of resources

            Attributes:
                - _name             = (str) The character's name
                - _cached_stats     = (dict) Any stats that need to be stored here for later use
                - _max_hp           = (int) The maximum HP of the character
                - hp                = (int) The current HP of the character
                - temp_hp           = (int) The temporary HP of the character
                - regular_action    = (int) The number of regular actions the character has
                - bonus_action      = (int) The number of bonus actions the character has
                - _speed            = (float) The character's speed i.e. max distance travelled
                - movement          = (float) The number of feet this character has for movement
                - reaction          = (int) The number of reactions this character has
                - _max_hit_dice     = (dict of int) The max dice for each Hit Dice
                - hit_dice          = (dict of int) The number of dice in the Hit Dice pool for the character
                - _max_slots        = (dict of int) The max slots for each spell level
                - spell_slots       = (dict of int) The number of Spell Slots of each spell level for the character
                - cond              = (dict of condition obj) All conditions on the character
                - death_saves       = (dict of int) The number of death save successes and failures
                    - Key       | Value
                    - success   | (int) The number of successful death saves
                    - fail      | (int) The number of failed death saves
                - bardic_insp       = (int) The number of bardic inspirations this character has
                - wild_shape        = (int) The number of wild shapes this character has
                - second_wind       = (int) The number of second winds the character has
                - action_surge      = (int) The number of action surges the character has
                - miscellaneous     = (dict of int) Any other miscellaneous resources
            """
            if not isinstance(in_stats, battleChar.stats):
                raise TypeError('arg in_stats must be a battleChar.stats object')
            self._name = name
            self._cached_stats = {}
            self._max_hp = 1*in_stats.max_hp
            self.hp = 1*in_stats.max_hp
            self.temp_hp = 0
            self.regular_action = 1
            self.bonus_action = 1
            self._speed = float(in_stats.speed)
            self.movement = float(in_stats.speed)
            self.reaction = 1
            self._max_hit_dice = {}
            for i_str in in_stats.hit_dice:
                parse_tuple = _parse_d(i_str)
                self._max_hit_dice[parse_tuple[0]] = parse_tuple[1]
            self.hit_dice = self._max_hit_dice.copy()
            self._max_slots = in_stats.slots.copy()
            self.spell_slots = in_stats.slots.copy()
            self.cond = {}
            self.death_saves = {'success':0, 'fail':0}

            # Class resources
            self.bardic_insp = 0
            self.wild_shape = 0
            self.second_wind = 0
            self.action_surge = 0

            self.miscellaneous = {}
        # End __init__

        class condition(object):
            """Object that is a condtion on the character.

            Args:
                - name          = (str) Name of this condtion
                - duration      = (str) Duration of this condition in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                    eont (end of next turn)]. Example: 2 round or 3 minute.
                - indefinite    = (bool, optional) If this condition is an indefinite one. If not Default=False, will ignore arg duration.

            Methods:
                - check_condition   : after a certain amount of time has passed, check to see if the condition is done or not
                - add_time          : add more time to the condtion
            """
            def __init__(self, name, duration, indefinite=False, prop=''):
                """Init for condition

                Attributes:
                    - name          = (str) Name of this condition
                    - indefinite    = (bool) If this condition is indefinite, i.e. has no end
                    - unit          = (str) Time unit used for condition duration
                    - remaining     = (float) Time remaining for condition, in unit above
                    - valid         = (bool) If the condition is valid because there is still time remaining on its duration
                    - _properties   = (str) Any properties that should go with this condtion
                """
                if not isinstance(name, str):
                    raise TypeError('arg name must be a str')
                self.name = name
                if not isinstance(prop, str):
                    raise TypeError('arg prop must be a str')
                self._properties = prop

                if indefinite:
                    self.indefinite = True
                    self.unit = ''
                    self.remaining = 0
                    self.valid = True
                    return
                self.indefinite = False

                if not isinstance(duration, str):
                    raise TypeError('arg duration must be a str')
                split_list = duration.split(' ')
                if (len(split_list)!=2):
                    raise ValueError('arg duration is not in the right format: # unit')
                if (split_list[1] not in ['round', 'second', 'minute', 'hour', 'day', 'sont', 'eont']):
                    raise ValueError('arg duration had an invalid unit')
                self.unit = split_list[1]
                if (not split_list[0].isnumeric()):
                    raise ValueError('arg duration did not have a number for time')
                self.remaining = float(split_list[0])

                self.valid = True
            # End __init__

            def check_condition(self, time_passed):
                """To check if condition has ended cause sufficient time has passed. Will subtract time passing from attribute remaining

                Args:
                    - time_passed = (str) Amount of time that has passed in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                        eont (end of next turn)]. Example: 2 round or 3 minute.

                Returns:
                    (bool) True if the condition has ended
                """
                if self.indefinite:
                    log.conditn(f'{self.name} continues as an indefinite condition')
                    return False

                if not isinstance(time_passed, str):
                    raise TypeError('arg time_passed must be a str')
                split_list = time_passed.split(' ')
                if (len(split_list)!=2):
                    raise ValueError('arg time_passed is not in the right format: # unit')
                if (split_list[1] not in ['round', 'second', 'minute', 'hour', 'day', 'sont', 'eont']):
                    raise ValueError('arg time_passed had an invalid unit')
                unit = split_list[1]
                if (not split_list[0].isnumeric()):
                    raise ValueError('arg time_passed did not have a number for time')
                amount = float(split_list[0])

                if (self.unit==unit):
                    self.remaining -= amount
                elif (self.unit=='sont'):
                    if (unit in ['minute', 'hour', 'day']):
                        self.remaining -= (TIME_UNITS[unit]/TIME_UNITS['sont'])*amount
                elif (self.unit=='eont'):
                    if (unit in ['minute', 'hour', 'day']):
                        self.remaining -= (TIME_UNITS[unit]/TIME_UNITS['eont'])*amount
                else:
                    self.remaining -= (TIME_UNITS[unit]/TIME_UNITS[self.unit])*amount

                if self.remaining <= 0:
                    log.conditn(f'{self.name} has ended')
                    self.valid = False
                    return True
                log.conditn(f'{self.name} has {round(self.remaining, 2)} {self.unit}(s) remaining')
                return False
            # End check_condition method

            def add_time(self, duration):
                """Adds more time to the condition. You cannot subtract time with this method; use check_condition method for such a thing.

                Args:
                    - duration  = (str) Duration of this condition in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                        eont (end of next turn)]. Example: 2 round or 3 minute.

                Returns:
                    No return value
                """
                if self.indefinite:
                    log.debug(f'cannot add time to an indefinite condition {self.name}')
                    return
                if not isinstance(duration, str):
                    raise TypeError('arg duration must be a str')
                split_list = duration.split(' ')
                if (len(split_list)!=2):
                    raise ValueError('arg time_passed is not in the right format: # unit')
                if (split_list[1] not in ['round', 'second', 'minute', 'hour', 'day', 'sont', 'eont']):
                    raise ValueError('arg duration had an invalid unit')
                unit = split_list[1]
                if (not split_list[0].isnumeric()): # This will automatically check for positive only time
                    raise ValueError('arg duration did not have a number for time')
                amount = float(split_list[0])

                if (self.unit==unit):
                    self.remaining += amount
                else:
                    self.remaining += (TIME_UNITS[unit]/TIME_UNITS[self.unit])*amount
                log.conditn(f'{self.name} now lasts for {self.remaining} {self.unit}(s)')
            # End add_time method
        # End condition class

        def add_miscellaneous(self, in_list):
            """Adds new keys to attribute miscellaneous

            Args:
                - in_list = (list) List of keys to add

            Returns:
                No return value
            """
            if not isinstance(in_list, list):
                raise TypeError('arg in_list must be a list of str')
            for i in in_list:
                if not isinstance(i, str):
                    raise TypeError('arg in_list must be a list of str')
                self.miscellaneous[i] = 1
        # End add_miscellaneous method

        def add_resource(self, in_dict):
            """Add resources to the character, updating the attributes. Also used to remove resources.
            HP handling is done by heal_hp and remove_hp methods, not this one.

            Args:
                - in_dict = (dict) Resources to change. If negative, will remove resources instead.
                    - Key       | Value
                    - temp_hp   | (int) Increase temp HP
                    - regular   | (int) Increase regular actions
                    - bonus     | (int) Increase bonus actions
                    - reaction  | (int) Increase reaction
                    - movement  | (int) Increase movement
                    - hit_dice  | (dict) Increase hit dice
                        - Key               | Value
                        - {int of faces}    | (int) Increase hit dice of this number of faces
                    - slots     | (dict) Increase spell slots
                        - Key                   | Value
                        - {spell slot level}    | (int) Increase slots of this level

            Returns:
                No return value
            """
            if not isinstance(in_dict, dict):
                raise TypeError('arg in_dict must be a dict')

            if ('temp_hp' in in_dict):
                self.temp_hp += in_dict['temp_hp']
                log.resource(f'{self._name} now has {self.temp_hp} temporary HP')
            if ('regular' in in_dict):
                self.regular_action = max(0, self.regular_action + in_dict['regular'])
                log.resource(f'{self._name} now has {self.regular_action} regular actions')
            if ('bonus' in in_dict):
                self.bonus_action = max(0, self.bonus_action + in_dict['bonus'])
                log.resource(f'{self._name} now has {self.bonus_action} bonus actions')
            if ('reaction' in in_dict):
                self.reaction = max(0, self.reaction + in_dict['reaction'])
                log.resource(f'{self._name} now has {self.reaction} reactions')
            if ('movement' in in_dict):
                if ('grappled' not in self.cond):
                    self.movement = max(0.0, self.movement + float(in_dict['movement']))
                    log.resource(f'{self._name} now has {self.movement} feet of movement')
                else:
                    log.resource(f'{self._name} cannot gain movement because they are grappled')

            if ('hit_dice' in in_dict):
                valid_faces = range(2, 14, 2)
                for i_faces, i_count in in_dict['hit_dice'].items():
                    if (i_faces not in valid_faces):
                        continue
                    self.hit_dice[i_faces] = max(0, min(self._max_hit_dice[i_faces], self.hit_dice[i_faces] + i_count))
                log.resource(f'{self._name} now has {self.hit_dice} hit dice')

            if ('slots' in in_dict):
                valid_levels = range(1,10)
                for i_level, i_count in in_dict['slots'].items():
                    if (i_level not in valid_levels):
                        continue
                    self.spell_slots[i_level] = max(0, min(self._max_slots[i_level], self.spell_slots[i_level] + i_count))
                log.resource(f'{self._name} now has {self.spell_slots} spell slots')
        # End add_resource method

        def restore_all_slots(self):
            """Restores all the spell slots of the character

            Args:
                No args

            Returns:
                No return value
            """
            for i_slot, i_count in self._max_slots.items():
                self.spell_slots[i_slot] = 1*i_count
        # End restore_all_slots method

        def effect_on_gain(self, name):
            """Do all effects that trigger when gaining the specified condtion.

            Args:
                - name = (str) The name of the condition

            Returns:
                No return value
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if (name in ['grappled', 'restrained']):
                self._cached_stats['_speed'] = 1*self._speed
                self._speed = 0
                log.conditn(f'{self._name} had their speed set to 0 because of {name}')
        # End effect_on_gain method

        def effect_on_check(self, name):
            """Do all effects that trigger when checking for that condition. In general, this should only happen in check_all_conditions method

            Args:
                - name = (str) The name of the condition

            Returns:
                No return value
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if (name in ['grappled', 'restrained']):
                self.movement = 0.0
                log.conditn(f'{self._name} has 0 feet of movement because they have {name}')
        # End effect_on_check method

        def effect_on_loss(self, name):
            """Lose all effects that trigger when losing the specified condition.

            Args:
                - name = (str) The name of the condition

            Returns:
                No return value
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if (name in ['grappled', 'restrained']):
                self._speed = 1*self._cached_stats['_speed']
                log.conditn(f'{self._name} regains their normal speed after losing {name}')
        # End effect_on_loss method

        def add_condition(self, name, duration, prop=''):
            """Adds the condition to the character. If character already has the condition, will add more time to its remaining time.

            Args:
                - name      = (str) Name of this condtion
                - duration  = (str) Duration of this condition in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                    eont (end of next turn)]. Example: 2 round or 3 minute. Can be 'indefinite' if there is no duration
                - prop      = (str, optional) Any properties that should go with the condition. Default=''

            Returns:
                (int) How many conditions the character now has
            """
            if (name in self.cond):
                log.conditn(f'Adding {duration} for {name} on {self._name}')
                self.cond[name].add_time(duration=duration)
            elif (duration=='indefinite'):
                self.cond[name] = self.condition(name=name, duration='', indefinite=True, prop=prop)
                log.conditn(f'{self._name} now has condition {name} indefinitely')
            else:
                self.cond[name] = self.condition(name=name, duration=duration, prop=prop)
                log.conditn(f'{self._name} now has condition {name} for {duration}')

            if (name=='dying'):
                self.add_condition('unconscious', 'indefinite')
            if (name in ['paralyzed', 'petrified', 'stunned', 'unconscious']):
                self.add_condition('incapacitated', 'indefinite')
            if (name=='unconscious'):
                self.add_condition('prone', 'indefinite')
            if (name=='stabilized'):
                self.death_saves = {'success':0, 'fail':0}
            self.effect_on_gain(name)
            return len(self.cond)
        # End add_condition method

        def remove_condition(self, name):
            """Remove the specified condtion from the character

            Args:
                - name = (str) Name of the condition to remove

            Returns:
                No return value
            """
            if (name in self.cond):
                del self.cond[name]
                self.effect_on_loss(name)

                if (name=='dying'):
                    self.death_saves = {'success':0, 'fail':0}
                    self.remove_condition('unconscious')
                if (name in ['paralyzed', 'petrified', 'stunned', 'unconscious']):
                    self.remove_condition('incapacitated')

                log.conditn(f'{self._name} no longer has {name}')
            else:
                log.conditn(f'Could not remove {name} from {self._name} because they did not have such a condition')
        # End remove_condition method

        def heal_hp(self, amount):
            """Heal the specified amount of HP to the character

            Args:
                - amount = (int) The amount to heal. If less than 0, will heal to max.

            Returns:
                (int) The new current HP of the character
            """
            if not isinstance(amount, int):
                raise TypeError('arg amount must be an int')
            if ('death' in self.cond):
                raise Exception('cannot heal a dead character')

            if (amount < 0):
                self.hp = 1*self._max_hp
                log.resource(f'{self._name} was healed to full HP={self.hp}')
            else:
                self.hp = min(self._max_hp, self.hp + amount)
                log.resource(f'{self._name} was healed {amount} to HP={self.hp}')

            if ((self.hp>0) and ('dying' in self.cond)):
                self.remove_condition('dying')
            return self.hp
        # End heal_hp method

        def remove_hp(self, amount, do_death_saves=True):
            """Remove the specified amount of HP to the character

            Args:
                - amount    = (int) The amount to remove. Must be non-negative.
                - team      = (bool, optional) If the character does death saves, i.e. if they are a PC. Default=True.

            Returns:
                (int) The new current HP of the character
            """
            if not isinstance(amount, int):
                raise TypeError('arg amount must be an int')
            if (amount < 0):
                raise ValueError('arg amount must be non-negative')
            remainder = self.hp - amount
            self.hp = max(remainder, 0)
            if (self.hp==0):
                if (do_death_saves):
                    if (abs(remainder)>=self._max_hp):
                        self.add_condition('death', 'indefinite')
                        log.conditn(f'{self._name} is now dead after losing {amount} HP (excess was >= max HP)')
                    else:
                        self.add_condition('dying', 'indefinite')
                        log.conditn(f'{self._name} is now dying after losing {amount} HP')
                else:
                    self.add_condition('death', 'indefinite')
                    log.conditn(f'{self._name} is now dead after losing {amount} HP')
            else:
                log.resource(f'{self._name} has {self.hp} HP after losing {amount} HP')
            return self.hp
        # End remove_hp method

        def check_all_conditions(self, time_passed):
            """Will check all conditions with the specified time passing. If any remain, will do the effects of those conditions if they trigger.

            Args:
                - time_passed = (str) Amount of time that has passed in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                    eont (end of next turn)]. Example: 2 round or 3 minute.

            Returns:
                (int) How many conditions remain on the character
            """
            if (self.cond):
                log.conditn(f'Checking conditions of {self._name}')
                delete_list = []
                for i_name, i_condition in self.cond.items():
                    condition_end = i_condition.check_condition(time_passed=time_passed)
                    if condition_end:
                        delete_list.append(i_name)
                    else:
                        self.effect_on_check(i_name)
                for i_name in delete_list:
                    self.remove_condition(i_name)
                return len(self.cond)
            else:
                return 0
        # End check_all_conditions method

        def long_rest(self, in_stats):
            """The character will do a long rest, regaining all resources that come with it

            Args:
                - in_stats = (stats obj) The stats of the character

            Returns:
                No return value
            """
            if not isinstance(in_stats, battleChar.stats):
                raise TypeError('arg in_stats must be a battleChar.stats obj')
            if (self.hp == 0):
                log.resource(f'{self._name} cannot do long rest because they have 0 HP')
                return

            # Character cannot recieve benefit of a long rest if they are dead
            if ('death' in self.cond):
                return

            # Replenish HP
            self.heal_hp(-1)

            # Replenish hit dice
            if in_stats.tot_hd:
                replenish_count = max(in_stats.tot_hd // 2, 1)
                full_break = False
                for i_faces in range(12, 2, -2):
                    if (i_faces not in self._max_hit_dice):
                        continue
                    for i in range(self._max_hit_dice[i_faces]):
                        if (replenish_count==0):
                            full_break = True
                            break
                        if (self.hit_dice[i_faces]>=self._max_hit_dice[i_faces]):
                            self.hit_dice[i_faces] = 1*self._max_hit_dice[i_faces] # Clip to max just in case
                            break
                        self.hit_dice[i_faces] += 1
                        replenish_count -= 1
                    if full_break:
                        break
                log.resource(f'{self._name} restored {replenish_count} hit dice')

            # Replenish class features
            for i_class, i_level in in_stats.class_level.items():
                if (i_class == 'bard'):
                    self.bardic_insp = max(1, in_stats.get_mod('cha'))
                    self.restore_all_slots()
                    log.resource(f'{self._name} restored their bard features after a long rest')
                if (i_class == 'druid'):
                    self.wild_shape = 2
                    self.restore_all_slots()
                    log.resource(f'{self._name} restored their druid features after a long rest')
                if (i_class == 'fighter'):
                    self.second_wind = 1
                    if (i_level >= 2):
                        self.action_surge = 2 if i_level >= 17 else 1
                    log.resource(f'{self._name} restored their fighter features after a long rest')
                if (i_class == 'warlock'):
                    self.restore_all_slots()
                    log.resource(f'{self._name} restored their warlock features after a long rest')
        # End long_rest method

        def short_rest(self, in_stats, spend_dice=[]):
            """The character will do a short rest, regaining all resources that come with it

            Args:
                - in_stats = (stats obj) The stats of the character
                - spend_dice = (list of str, optional) The list of #d# string of hit dice to spend to heal. If Default=[], will skip spending hit dice.

            Returns:
                No return value
            """
            if not isinstance(in_stats, battleChar.stats):
                raise TypeError('arg in_stats must be a battleChar.stats obj')
            if not isinstance(spend_dice, list):
                raise TypeError('arg spend_dice must be a list')
            if spend_dice:
                heal_total = 0
                for i_str in spend_dice:
                    parse_tuple = _parse_d(i_str)
                    if (parse_tuple[0] not in self.hit_dice):
                        log.debug(f'{self._name} does not have a d{parse_tuple[0]} hit die')
                        continue
                    for i in range(parse_tuple[1]):
                        if (self.hit_dice[parse_tuple[0]]==0):
                            break
                        self.hit_dice[parse_tuple[0]] -= 1
                        heal_total += roll_d(parse_tuple[0]) + in_stats.get_mod('con')
                log.resource(f'{in_stats._name} is using {spend_dice} hit dice to heal')
                self.heal_hp(heal_total)

            # Replenish class features
            for i_class, i_level in in_stats.class_level.items():
                if (i_class == 'druid'):
                    self.wild_shape = 2
                    log.resource(f'{self._name} restored some druid features after a short rest')
                if (i_class == 'fighter'):
                    self.second_wind = 1
                    if (i_level >= 2):
                        self.action_surge = 2 if i_level >= 17 else 1
                    log.resource(f'{self._name} restored some fighter features after a short rest')
                if (i_class == 'warlock'):
                    self.restore_all_slots()
                    log.resource(f'{self._name} restored their warlock features after a short rest')
        # End short_rest method

        def get_resources_for_round(self, remove_first={}):
            """Will get all resources the character has for the round

            Args:
                - remove_first = (dict, optional) Remove the specified resources first. Make sure all values are negative; using add_resource method.

            Returns: (dict) The resources the character has
                - Key       | Value
                - regular   | (int) How many regular actions they have
                - bonus     | (int) How many bonus actions they have
                - reaction  | (int) How many reactions they have
                - movement  | (int) How many feet of movement they have
                - slots     | (dict of int) How many spell slots per level they have
            """
            self.add_resource(in_dict=remove_first)
            return_val = {}
            return_val['regular'] = self.regular_action
            return_val['bonus'] = self.bonus_action
            return_val['reaction'] = self.reaction
            return_val['movement'] = self.movement
            return_val['slots'] = self.spell_slots
            log.debugall(f'{self._name} round resources={return_val}')
            return return_val
        # End get_resources_for_round method

        def start_turn(self):
            """The character will start their turn, regaining their actions and movement

            Args:
                No args

            Returns: (dict) Resources for round. See get_resources_for_round method
                - Key       | Value
                - regular   | (int) How many regular actions they have
                - bonus     | (int) How many bonus actions they have
                - reaction  | (int) How many reactions they have
                - movement  | (int) How many feet of movement they have
                - slots     | (dict of int) How many spell slots per level they have
            """
            self.regular_action = 1
            self.bonus_action = 1
            self.movement = float(1*self._speed)
            self.reaction = 1

            # Restore unique resources
            if ('genies_wrath' in self.miscellaneous):
                self.miscellaneous['genies_wrath'] = 1

            self.check_all_conditions('1 sont')
            return self.get_resources_for_round()
        # End start_turn method

        def end_turn(self):
            """Ends the turn of the character, triggering end of turn effects

            Args:
                No args

            Returns:
                No return value
            """
            self.check_all_conditions('1 eont')
        # End end_turn method

        def _gain_death_save(self, success, count=1):
            """Have the character gain a death save roll.

            Args:
                - success   = (bool) If it was a successful roll. Otherwise a failure.
                - count     = (int, optional) The number of rolls to add. One of [1,2]. 2 should only be used for fails.

            Returns:
                No return value
            """
            if success:
                self.death_saves['success'] += 1
            else:
                self.death_saves['fail'] += 1 if (count==1) else 2
            log.resource(f'{self._name} death saves = {self.death_saves}')

            if (self.death_saves['success'] >= 3):
                self.add_condition('stabilized', 'indefinite')
            elif (self.death_saves['fail'] >= 3):
                self.remove_condition('dying')
                self.add_condition('death', 'indefinite')
                log.conditn(f'{self._name} is now dead after 3 death save failures')
            elif ((self.death_saves['fail'] > 0) and ('stabilized' in self.cond)):
                self.remove_condition('stabilized')
                log.conditn(f'{self._name} is no longer stabilized after gain a death save fail')
        # End _gain_death_save method

        def do_death_save(self):
            """Have the character do a death save.

            Args:
                No args

            Returns: (dict of int) The number of death save successes and failures
                - Key       | Value
                - success   | (int) The number of successful death saves
                - fail      | (int) The number of failed death saves
            """
            if ('dying' not in self.cond):
                raise Exception('cannot do death save on character that is not dying')
            if ('stabilized' in self.cond):
                log.debug(f'{self._name} is already stabilized and does not need to do death saves')
                return {"success":0, "fail":0}

            death_roll = roll_20()
            if (death_roll==20):
                log.save(f'{self._name} critically succeeds on their death save')
                self.heal_hp(1)
                return {"success":0, "fail":0}

            if (death_roll>=10):
                log.save(f'{self._name} succeeds on death save')
                self._gain_death_save(True)
            elif (death_roll==1):
                log.save(f'{self._name} critically fails their death save')
                self._gain_death_save(False, 2)
            else:
                log.save(f'{self._name} fails their death save')
                self._gain_death_save(False)
            return self.death_saves
        # End do_death_save method
    # End resources class

    class actionChooser(object):
        """The available actions of a character and the bias they are likely to pick each one.
        There should only be one instance of this in a character.

        Args:
            - name              = (str) The name of the character
            - in_json           = (str) Path of a json to load all default actions
            - category          = (list of str, optional) Which categories to automatically include. Default=[]
            - include_action    = (list of str, optional) All other optional actions to load. These actions must be in the above json. Default=[]

        Methods:
            - add_action:           adds a new action for the character
            - remove_action:        removes an action this character has
            - change_bias:          change the bias of an action
            - update_bias:          have character consider their conditions to update their biases
            - get_all_actions:      gets all actions the character can do
            - can_do_action:        checks to see if character can do such an action
            - get_random_action:    will get a random action that this character can do
        """
        def __init__(self, name, in_json, category=[], include_action=[]):
            """Init of actionChooser

            Attributes:
                - _name     = (str) The name of the character
                - regular   = (dict) All regular actions
                    - Key               | Value
                    - {name of action}  | (int) The bias of that action
                - move      = (dict) All move actions. Same format as attribute regular
                - bonus     = (dict) All bonus actions. Same format as attribute regular
                - reaction  = (dict) All reactions. Same format as attribute regular
                - free      = (dict) All free actions. Same format as attribute regular
                - special   = (dict) All free actions. Same format as attribute regular
            """
            if not isinstance(category, list):
                raise TypeError('arg category must be a list of str')
            if not isinstance(include_action, list):
                raise TypeError('arg include_action must be a list of str')
            self._name = name
            self.regular = {}
            self.move = {}
            self.bonus = {}
            self.reaction = {}
            self.free = {}
            self.special = {}

            with open(in_json, 'r') as read_file:
                data = json.load(read_file)
                for i_category, i_action_dict in data.items():
                    for i_action, i_dict in i_action_dict.items():
                        if not (
                            (i_category == 'default') or
                            (i_category in category) or
                            (i_action in include_action)
                        ):
                            continue

                        if (i_dict['type']=='regular'):
                            self.regular[i_action] = i_dict['bias']
                        elif (i_dict['type']=='movement'):
                            self.move[i_action] = i_dict['bias']
                        elif (i_dict['type']=='bonus'):
                            self.bonus[i_action] = i_dict['bias']
                        elif (i_dict['type']=='reaction'):
                            self.reaction[i_action] = i_dict['bias']
                        elif (i_dict['type']=='free'):
                            self.free[i_action] = i_dict['bias']
                        else:
                            self.special[i_action] = i_dict['bias']
            log.debugall(f'{self._name} actions={self.get_all_actions()}')
        # End __init__

        def add_action(self, in_dict):
            """Adds a new action for the character

            Args:
                - in_dict = (dict) The actions to add
                    - Key           | Value
                    - {action name} | (dict) Attributes of this attack
                        - Key   | Value
                        - bias  | (int) The bias of the action
                        - type  | (str) The type this action is

            Returns:
                No return value
            """
            if not isinstance(in_dict, dict):
                raise TypeError('arg in_dict must be a dict')

            for i_action, i_att in in_dict.items():
                if (i_att['type']=='regular'):
                    if (i_att['type'] in self.regular):
                        raise ValueError(f'{self._name} already has a regular action called {i_action}')
                    self.regular[i_action] = i_att['bias']

                elif (i_att['type']=='bonus'):
                    if (i_action in self.bonus):
                        raise ValueError(f'{self._name} already has a bonus action called {i_action}')
                    self.bonus[i_action] = i_att['bias']

                elif (i_att['type']=='reaction'):
                    if (i_action in self.reaction):
                        raise ValueError(f'{self._name} already has a reaction called {i_action}')
                    self.reaction[i_action] = i_att['bias']

                elif (i_att['type']=='movement'):
                    if (i_action in self.move):
                        raise ValueError(f'{self._name} already has a move action called {i_action}')
                    self.move[i_action] = i_att['bias']

                elif (i_att['type']=='free'):
                    if (i_att['type'] in self.free):
                        raise ValueError(f'{self._name} already has a free action called {i_action}')
                    self.free[i_action] = i_att['bias']

                else:
                    if (i_att['type'] in self.special):
                        raise ValueError(f'{self._name} already has a special action called {i_action}')
                    self.special[i_action] = i_att['bias']
            log.debugall(f'{self._name} now has actions = {in_dict}')
        # End add_action method

        def remove_action(self, name, act_type):
            """Remove the specified action

            Args:
                - name      = (str) The name of the action
                - act_type  = (str) The type of the action. One of [regular, move, bonus, reaction, free, special]

            Returns:
                No return value
            """
            if not isinstance(name, str):
                raise ValueError('arg name must be a str')
            if not isinstance(act_type, str):
                raise ValueError('arg act_type must be a str')
            if (act_type=='regular'):
                action_dict = self.regular
            elif (act_type=='move'):
                action_dict = self.move
            elif (act_type=='bonus'):
                action_dict = self.bonus
            elif (act_type=='reaction'):
                action_dict = self.reaction
            elif (act_type=='free'):
                action_dict = self.free
            else:
                action_dict = self.special
            if (name not in action_dict):
                log.debugall(f'{self._name} had no {act_type} action called {name} to remove')
                return
            del action_dict[name]
            log.debugall(f'{self._name} no longer has action {name}')
        # End remove_action method

        def change_bias(self, in_dict):
            """Change the biases of the specified actions

            Args:
                - in_dict = (dict) The actions to have their bias changed
                    - Key   | Value
                    - {name of action}  | (int) New bias. One of [16,8,4,2,1,0].

            Returns:
                No return value
            """
            if not isinstance(in_dict, dict):
                raise TypeError('arg in_dict must be a dict')
            for i_name, i_bias in in_dict.items():
                if (i_bias not in [int(2**i) for i in range(-1,5)]):
                    raise ValueError('arg in_dict must have bias as a power of 2 or 0')
                if (i_name in self.regular):
                    self.regular[i_name] = i_bias
                    continue
                if (i_name in self.bonus):
                    self.bonus[i_name] = i_bias
                    continue
                if (i_name in self.free):
                    self.free[i_name] = i_bias
                    continue
                if (i_name in self.reaction):
                    self.reaction[i_name] = i_bias
                    continue
                if (i_name in self.move):
                    self.move[i_name] = i_bias
                    continue
                if (i_name in self.special):
                    self.special[i_name] = i_bias
                    continue
                log.debug(f'{self._name} did not have an action called {i_name}')
            log.debug(f'updated action biases of {self._name}')
        # End change_bias method

        def update_bias(self, char_obj):
            """Will look through all conditions, then update action biases because of this

            Args:
                - char_obj = (battleChar obj) The object of the character; SHOULD be the character that holds this actionChooser

            Returns:
                No return value
            """
            if not isinstance(char_obj, battleChar):
                raise TypeError('arg char_obj must be a battleChar.resources obj')
            if ('druid' in char_obj.char_stats.class_level):
                if ('shillelagh' in char_obj.char_resources.cond):
                    char_obj.char_actions.change_bias({'cast_shillelagh':0})
                else:
                    char_obj.char_actions.change_bias({'cast_shillelagh':16})
        # End update_bias method

        def get_all_actions(self):
            """Get all actions of this character

            Args:
                No args

            Returns: (dict) All actions of this character
                - Key               | Value
                - {name of action}  | (str) Type of action
            """
            return_val = {}
            for i_action in self.regular:
                return_val[i_action] = 'regular'
            for i_action in self.move:
                return_val[i_action] = 'move'
            for i_action in self.bonus:
                return_val[i_action] = 'bonus'
            for i_action in self.reaction:
                return_val[i_action] = 'reaction'
            for i_action in self.free:
                return_val[i_action] = 'free'
            for i_action in self.special:
                return_val[i_action] = 'special'
            return return_val
        # End get_all_actions method

        def can_do_action(self, name):
            """Checks to see if this character can do the specified action

            Args:
                - name = (str) The name of the new action

            Returns:
                (bool) If this character can do this action
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            return (name in self.get_all_actions())
        # End can_do_action method

        def get_random_action(self, act_type):
            """Gets a random action of this character, weighted by the biases

            Args:
                - act_type = (str) The type of the action. One of [regular, bonus, reaction, move]

            Returns:
                - None if there are no actions available, otherwise
                - (str) The name of an action this character can do
            """
            if (act_type=='regular'):
                action_dict = self.regular
            elif (act_type=='move'):
                action_dict = self.move
            elif (act_type=='bonus'):
                action_dict = self.bonus
            elif (act_type=='reaction'):
                action_dict = self.reaction
            elif (act_type=='free'):
                action_dict = self.free
            else:
                action_dict = self.special

            if not action_dict:
                log.debug(f'{self._name} has no {act_type} actions')
                return None

            try_list = [True for i in range(5)]
            for i_attempt in range(5):
                bias_list = []
                for i_bias, i_try in enumerate(try_list):
                    if not i_try:
                        continue
                    for i in range(2**i_bias):
                        bias_list.append(2**i_bias)
                log.debugall(f'{self._name} action search attempt {i_attempt}: {try_list}')
                true_bias = random.choice(bias_list)
                possible_actions = []
                for i_action, i_bias in action_dict.items():
                    if (i_bias==true_bias):
                        possible_actions.append(i_action)
                log.debugall(f'{self._name} possible actions={possible_actions}')
                if possible_actions:
                    return random.choice(possible_actions)
                try_list[int(math.log2(true_bias))] = False
            log.debug(f'could not get a random action for {self._name}')
            return None
        # End get_random_action method
    # End actionChooser class

    def take_damage(self, damage, was_crit=False):
        """Will subtract the specified damage from the character's current HP.

        Args:
            - damage    = (dict) The amount of damage the character took
                - Key               | Value
                - {type of damage}  | (int) Damage of that value type
            - was_crit  = (bool, optional) If the damage was from a critical hit. Default=False

        Returns: (tuple)
            - (int) The total damage taken
            - (int) The new current HP of the character
        """
        if not isinstance(damage, dict):
            raise TypeError('arg damage must be an dict')
        total_damage = 0
        for i_type, i_value in damage.items():
            if ('petrified' in self.char_resources.cond):
                total_damage += i_value // 2
            if (i_type in self.char_stats.imm):
                continue
            if (i_type in self.char_stats.res):
                total_damage += i_value // 2
            elif (i_type in self.char_stats.vul):
                total_damage += i_value * 2
            else:
                total_damage += i_value
        log.damage(f'{self._name} takes {total_damage} adjusted damage')
        if ('dying' in self.char_resources.cond):
            self.char_resources._gain_death_save(False, 2 if was_crit else 1)
            return (total_damage, 0)
        return (total_damage, self.char_resources.remove_hp(total_damage, self.team=='pc'))
    # End take_damage method

    def add_attack(self, in_dict):
        """Add attacks to available attacks of character

        Args:
            - in_dict = (dict) Attacks to add
                - Key               | Value
                - {name of attack}  | (int) Bias of attack

        Returns:
            No return value
        """
        if not isinstance(in_dict, dict):
            raise TypeError('arg in_dict must be a dict')
        
        for i_name, i_bias in in_dict.items():
            if (i_name in self.char_attacks):
                log.debugall(f'attack {i_name} already exists for {self._name}')
                continue
            self.char_attacks[i_name] = i_bias
        log.debugall(f'added {in_dict} to {self._name}')
    # End add_attack method

    def set_stats(self, stat_dict):
        """Sets the stats of the character.

        Args:
            - stat_dict = (dict) The key is the attribute to change, the value is the new value. Should keep the same format for each
                attribute in stats object.

        Returns:
            No return value
        """
        self.char_stats.set_stats(stat_dict=stat_dict)
        if ('max_hp' in stat_dict):
            self.char_resources._max_hp = 1*self.char_stats.max_hp
            self.char_resources.hp = min(self.char_resources.hp, self.char_stats.max_hp)
        if ('hit_dice' in stat_dict):
            for i_str in stat_dict['hit_dice']:
                parse_tuple = _parse_d(i_str)
                self.char_resources.hit_dice[parse_tuple[0]] = parse_tuple[1]
        if ('speed' in stat_dict):
            self.char_resources._speed = 1*stat_dict['speed']
            self.char_resources.movement = min(self.char_resources.movement, stat_dict['speed'])
        log.stat(f'set {self._name} stats: {stat_dict}')
    # End set_stats method

    def roll_stat(self, name, adv='norm'):
        """Have the character do a ability check, skill check, or saving throw. Will be affected by conditions.

        Args:
            - name = (str) The stat to roll. If an ability or skill check, just give the name. If a saving throw, give {ability} save
            - adv = (str, optional) If there should be advantage/disadvantage on the roll. One of [norm, adv, dis]. Default=norm.

        Returns:
            (int) The result of the roll
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        if (adv not in ['norm', 'adv', 'dis']):
            raise TypeError('arg adv must be one of [norm, adv, dis]')

        def _overlap(in_set):
            return not (set(self.char_resources.cond).isdisjoint(in_set))
        # End _overlap inner function

        def _convert(in_int):
            return 'adv' if (in_int > 0) else ('dis' if (in_int < 0) else 'norm')
        # End _conver inner function

        true_adv = 1 if (adv=='adv') else (-1 if (adv=='dis') else 0)

        # 20230928 Currently doing a blanket fail for certain conditions, don't know how to handle the specifics yet
        split_list = name.split(' ')
        if (split_list[0] in ABILITIES):
            # Handle saving throws
            if split_list[1]:
                if ((split_list[0] in ['str, dex']) and _overlap({'paralyzed', 'petrified', 'stunned', 'unconscious'})):
                    log.check(f'{self._name} automatically fails saving throw because of a condition')
                    return AUTO_FAIL
                if ((split_list[0]=='dex') and _overlap({'restrained'})):
                    log.check(f'{self._name} has disadvantage on saving throw because of a condition')
                    true_adv -= 1
                return_val = self.char_stats.roll_save(split_list[0], _convert(true_adv))
            
            # Handle ability check
            else:
                if _overlap({'blinded', 'deafened'}):
                    log.check(f'{self._name} automatically fails ability check because of a condition')
                    return AUTO_FAIL
                if _overlap({'charmed', 'frightened', 'poisoned'}):
                    log.check(f'{self._name} has disadvantage on ability check because of a condition')
                    true_adv -= 1
                return_val = self.char_stats.roll_ability(split_list[0], _convert(true_adv))

        # Handle skill check
        elif (split_list[0] in SKILLS):
            if _overlap({'blinded', 'deafened'}):
                log.check(f'{self._name} automatically fails skill check because of a condition')
                return AUTO_FAIL
            if _overlap({'charmed', 'frightened', 'poisoned'}):
                log.check(f'{self._name} has disadvantage on skill check because of a condition')
                true_adv -= 1
            return_val = self.char_stats.roll_skill(split_list[0], _convert(true_adv))
        
        else:
            raise ValueError('arg name was not an ability or skill')

        # Check for bardic inspiration
        if ('bardic_inspiration' in self.char_resources.cond):
            bi_roll = roll_d_str(self.char_resources.cond['bardic_inspiration']._properties)
            log.action(f'{self._name} is using their bardic inspiration and rolled a {bi_roll}')
            return_val += bi_roll
            self.char_resources.remove_condition('bardic_inspiration')

        return return_val
    # End roll_stat method

    def get_advantage(self, is_source):
        """If the character gets or grants advantage due to current condition.

        Args:
            - is_source = (bool) If the character is the source (the one doing an attack) or the target (the one being attacked)

        Returns:
            (int) 1 if there should be advantage, -1 if there should be disadvantage, otherwise 0
        """
        def _overlap(in_set):
            return not (set(self.char_resources.cond).isdisjoint(in_set))
        # End _overlap inner function

        return_val = 0
        # If the character is the source
        if is_source:
            if _overlap({'blinded', 'frightened', 'prone', 'restrained'}):
                log.hit(f'{self._name} has disadvantage because of a condition')
                return_val -= 1
            if _overlap({'invisible'}):
                log.hit(f'{self._name} has advantage because of a condition')
                return_val += 1
        # End source branch

        # If the character is the target
        else:
            if _overlap({'invisible', 'prone'}):
                log.hit(f'{self._name} grants disadvantage because of a condition')
                return_val -= 1
            if _overlap({'blinded', 'paralyzed', 'petrified', 'restrained', 'stunned', 'unconscious'}):
                log.hit(f'{self._name} grants advantage because of a condition')
                return_val += 1
        return max(-1, min(1, return_val))
    # End get_advantage method

    def get_random_attack(self):
        """Gets a random attack of this character, weighted by the biases

        Args:
            No args

        Returns:
            (str) The name of an attack this character can do
        """
        try_list = [True for i in range(5)]
        for i_attempt in range(5):
            bias_list = []
            for i_bias, i_try in enumerate(try_list):
                if not i_try:
                    continue
                for i in range(2**i_bias):
                    bias_list.append(2**i_bias)
            log.debugall(f'{self._name} attack search attempt {i_attempt}: {try_list}')
            true_bias = random.choice(bias_list)
            possible_attacks = []
            for i_attack, i_bias in self.char_attacks.items():
                if (i_bias==true_bias):
                    possible_attacks.append(i_attack)
            log.debugall(f'{self._name} possible attacks={possible_attacks}')
            if possible_attacks:
                return random.choice(possible_attacks)
            try_list[int(math.log2(true_bias))] = False
        raise Exception(f'could not get a random attack for {self._name}')
    # End get_random_attack method

    def get_random_action(self, act_type):
        """Gets a random action this character can do, dependent on what conditions this character has.

        Args:
            - act_type = (str) What action type to get. One of [regular, move, bonus, reaction, free, special]

        Returns:
            - None if there are no actions available of that type, otherwise
            - (str) The name of an action
        """
        if (act_type not in ['regular', 'move', 'bonus', 'reaction', 'free', 'special']):
            raise ValueError('arg act_type is not one of the valid action types')
        if ('death' in self.char_resources.cond):
            log.simulatn(f'{self._name} will do nothing because they are dead')
            return 'nothing' if (act_type=='action') else None

        # Update biases
        self.char_actions.update_bias(self)

        # Get regular action
        if (act_type=='regular'):
            if ('dying' in self.char_resources.cond):
                if ('stabilized' in self.char_resources.cond):
                    log.simulatn(f'{self._name} will do nothing because they are dying but stabilized')
                    return 'nothing'
                log.simulatn(f'{self._name} will do a death save because they are dying')
                return 'death_save'
            log.simulatn(f'{self._name} will search for an available regular action')
            return self.char_actions.get_random_action(act_type='regular')
        # End regular branch

        # Get bonus action
        if (act_type=='bonus'):
            if ('dying' in self.char_resources.cond):
                log.simulatn(f'{self._name} will do nothing because because they are dying')
                return None
            log.simulatn(f'{self._name} will search for available bonus action')
            return self.char_actions.get_random_action(act_type='bonus')
        # End bonus branch

        # Get move action
        if (act_type=='move'):
            if ('prone' in self.char_resources.cond):
                log.simulatn(f'{self._name} can only crawl because they are prone')
                return 'crawl'
            if ('grappling' in self.char_resources.cond):
                log.simulatn(f'{self._name} can only move_while_grappling because they are grappling something')
                return 'move_while_grappling'
            log.simulatn(f'{self._name} will search for an available move action')
            return self.char_actions.get_random_action(act_type='move')
        # End move branch

        log.simulatn(f'{self._name} fell through when looking for a random {act_type} action')
        return None
    # End get_random_action method
# End battleChar class

class battleStage(object):
    """The object that handles all the battleChar and interactions between them.

    Args:
        - in_json = (str, optional) Path of a json to load automaticall add all characters. Default=''

    Classes:
        characterAction:    action that a character can do

    Methods:
        - add_char:                 adds a new character to the battle
        - reset_battle:             restores all characters to full
        - _log_hp:                  logs the current HP of a character
        - log_hp:                   logs the current HP of all characters
        - set_initiative:           sets the initiative order
        - _get_next_in_initiative:  gets the next person in initiative order
        - _remove_valid:            removes character from valid list
        - _get_rand_valid:          get a random character from the valid lists
        - _add_time:                add to estimated time
        - get_targets_for_action:   get the targets for an action
        - char_do_action:           have specified character do an action
        - char_do_random_action:    have the specified character do a random action
        - simulate_round:           simulate one round of combat
        - simulate_to_end:          simulate until end of combat
    """
    def __init__(self, in_json='characters.json'):
        """Init for battleStage

        Attributes:
            - battlevalid       = (bool) If the battle is valid and can be simulated
            - round             = (int) What round the battle is in
            - _name_spacing     = (int) The length of the longest name of all characters
            - characters        = (dict of battleChar objects) All characters in the battle
            - _valid_good       = (list of str) All good characters that can be targeted
            - _valid_bad        = (list of str) All bad characters that can be targeted
            - initiative        = (list of tuple) The initiative order of all characters
                - (str) Name of the character
                - (int) What they rolled for initiative
            - current_turn      = (int) Which character has their turn during the current round
            - estimated_time    = (int) Estimated time that has elapsed over the battle in seconds
            - cached_actions    = (dict of characterAction obj) All actions that have been created already
        """
        log.header('Creating battle stage')
        self.battlevalid = False
        self.round = 0
        self._name_spacing = 1
        self.characters = {}
        self._valid_good = []
        self._valid_bad = []
        if in_json:
            with open(in_json, 'r') as read_file:
                data = json.load(read_file)
                for i_character in data:
                    self.add_char(
                        name=i_character['name'],
                        team=i_character['team'],
                        stats=i_character['stats'],
                        attacks=i_character['attacks'],
                        unique_actions=i_character['actions']['unique_actions'] if ('unique_actions' in i_character) else {},
                        bias=i_character['bias'] if ('bias' in i_character) else {},
                        act_cat=i_character['actions']['inc_category'] if ('inc_category' in i_character['actions']) else [],
                        act_inc=i_character['actions']['inc_action'] if ('inc_action' in i_character['actions']) else [],
                        res_inc=i_character['resource'] if ('resource' in i_character) else [],
                        prop=i_character['property'] if ('property' in i_character) else {},
                        instances=i_character['instances'] if ('instances' in i_character) else 1
                    )
        self.initiative = []
        self.current_turn = ''
        self.estimated_time = 0
        self.cached_actions = {}
        log.header('finished battle stage init\n')
    # End __init__

    class characterAction(object):
        """Handler for an action for a character to do

        Args:
            - name = (str) The name of the action to add, which will be taken from actions.json

        Methods:
            - _do_attack:   do an attack
            - _do_spell:    do a spell
            - _do_move:     do movement
            - _do_stat:     do stat change
            - _do_special:  do a special action
            - do_action:    does this action
        """
        def __init__(self, name):
            """Init of characterAction

            Attributes:
                - _name     = (str) Name of this action
                - targets   = (list of str) Possible targets. One of [self, ally, enemy]
                - _handle   = (str) How the action should be handled. One of [attack, spell, move, stat, contest, special]
                - _cost     = (str) What action type this uses up
                - _spacing  = (int, optional) The spacing for names. Default=10
            """
            log.debugall(f'creating action {name}')
            with open('actions.json', 'r') as read_file:
                data = json.load(read_file)
                for i_category, i_action_dict in data.items():
                    for i_name, i_dict in i_action_dict.items():
                        if (name==i_name):
                            self._name = name
                            if ('targets' in i_dict):
                                self.target = i_dict['targets']
                            else:
                                self.target = []
                            self._handle = i_dict['handle']
                            self._cost = i_dict['type']
                            return
            raise Exception(f'could not find action {name} in actions.json')
        # End __init__

        def _do_attack(self, source, target, in_attack, offhand=False):
            """Have the source character do specified attack on target character

            Args:
                - source    = (battleChar obj) The source of the attack
                - target    = (battleChar obj) The target of the attack
                - in_attack = (attack obj) The attack obj of this attack
                - offhand   = (bool, optional) If this attack was done with the offhand. Default=False.

            Returns:
                (int) The current HP of the target after the attack
            """
            if not isinstance(source, battleChar):
                raise TypeError('arg source must be a battleChar obj')
            if not isinstance(target, battleChar):
                raise TypeError('arg target must be a battleChar obj')
            if not isinstance(in_attack, attack):
                raise TypeError('arg in_attack must be an attack obj')

            # Attack roll
            advantage = source.get_advantage(True) + target.get_advantage(False)
            if (advantage > 0):
                log.hit(f'{source._name} has advantage on their attack roll')
                adv = 'adv'
            elif (advantage < 0):
                log.hit(f'{source._name} has disadvantage on their attack roll')
                adv = 'dis'
            else:
                adv = 'norm'
            roll_result = in_attack.roll_hit(character=source, adv=adv)

            if ((roll_result[0]=='miss') or (roll_result[1]<target.char_stats.ac)):
                log.hit(f'{source._name} misses {target._name}')
                hit = False
            else:
                log.hit(f'{source._name} hits {target._name}')
                hit = True

            # Damage roll
            if hit:
                damage = in_attack.roll_damage(char_obj=source, offhand=offhand, crit=(roll_result[0]=='hit'))
                (act_damage, return_val) = target.take_damage(damage=damage, was_crit=(roll_result[0]=='hit'))
            else:
                act_damage = 0
                return_val = target.char_resources.hp

            # Create picture
            str_list = ['' for i in range(5)]
            # Source
            largest_spacing = max(len(source._name), len(in_attack.name))
            str_list[0] += '='*(largest_spacing + 1)
            str_list[1] += f'{source._name:^{largest_spacing}} '
            str_list[2] += f'{" "*largest_spacing} '
            str_list[3] += f'{in_attack.name:^{largest_spacing}} '
            str_list[4] += '='*(largest_spacing + 1)
            # Hit
            str_list[0] += '='*10
            str_list[1] += ' '*10
            str_list[2] += f'{("CRIT HIT" if (roll_result[0]=="hit") else ("CRIT MISS" if (roll_result[0]=="miss") else f"{roll_result[1]} Hit")):^9} '
            str_list[3] += ' '*10
            str_list[4] += '='*10
            # Left arrow
            str_list[0] += '='*4
            str_list[1] += ' '*4
            str_list[2] += f'--{"-" if hit else ">"} '
            str_list[3] += ' '*4
            str_list[4] += '='*4
            # Damage
            if hit:
                largest_spacing = 0
                line_count = 0
                first_str = ''
                second_str = ''
                third_str = ''
                for i_k, i_v in damage.items():
                    if (line_count==0):
                        first_str = f'{i_v} {i_k}'
                        largest_spacing = max(largest_spacing, len(first_str))
                    if (line_count==1):
                        second_str = f'{i_v} {i_k}'
                        largest_spacing = max(largest_spacing, len(second_str))
                    if (line_count==3):
                        third_str = f'{i_v} {i_k}'
                        largest_spacing = max(largest_spacing, len(third_str))
                        break
                    line_count += 1
                str_list[0] += '='*largest_spacing
                str_list[1] += f'{first_str:^{largest_spacing}}' if (line_count==3) else (' '*largest_spacing)
                str_list[2] += f'{second_str:^{largest_spacing}}' if (line_count==3) else f'{first_str:^{largest_spacing}}'
                str_list[3] += f'{third_str:^{largest_spacing}}' if (line_count==3) else (f'{second_str:^{largest_spacing}}' if (line_count==2) else ' '*largest_spacing)
                str_list[4] += '='*largest_spacing
                # Right arrow
                str_list[0] += '====='
                str_list[1] += '     '
                str_list[2] += ' --> '
                str_list[3] += '     '
                str_list[4] += '====='
            else:
                str_list[0] += '=='
                str_list[1] += 'X '
                str_list[2] += 'X '
                str_list[3] += 'X '
                str_list[4] += '=='
            # Target
            largest_spacing = max(len(target._name), 6)
            str_list[0] += '='*largest_spacing
            str_list[1] += f'{target._name:^{largest_spacing}}'
            str_list[2] += f'{("-" + str(act_damage)):^{largest_spacing}}'
            str_list[3] += f'{(str(return_val) + " HP"):^{largest_spacing}}'
            str_list[4] += '='*largest_spacing
            for i in str_list:
                log.picture(i)

            return return_val
        # End _do_attack method

        def _do_spell(self, source, target=[]):
            """Have the specified character do a spell against the specified target

            Args:
                - source    = (battleChar obj) The character casting the spell
                - target    = (list of battleChar obj, optional) The characters being target by the spell. Default=[]

            Returns:
                (dict) The effects that have happened to all targets
            """
            if not isinstance(source, battleChar):
                raise TypeError('arg source must be a battleChar obj')
            if not isinstance(target, list):
                raise TypeError('arg target must be a list')

            # Create spell; it is assumed that the beginning of the name is 'cast_'
            this_spell = spell(self._name[5:])
            return this_spell.do_spell(source=source, target=target)
        # End _do_spell method

        def _do_move(self, source, distance, difficult=False):
            """Have the specified character move.
            20230928 Currently does nothing to determine terrain types

            Args:
                - source    = (battleChar obj) The character moving
                - distance  = (int) The distance the character is trying to move
                - difficult = (bool, optional) If currently moving through difficult terrain. Default=False.

            Returns:
                (float) The actual distance travelled
            """
            if not isinstance(source, battleChar):
                raise TypeError('arg source must be a battleChar obj')
            divisor = 2 if difficult else 1
            if (self._name in ['climb', 'crawl', 'swim']):
                divisor += 1
            return_val = round(distance / divisor, 2)
            log.action(f'{source._name} moves {return_val} feet ({5*(return_val//5)} squares)')
            return return_val
        # End _do_move method

        def _do_stat(self, source, target):
            """Do a stats action

            Args:
                - source    = (battleChar obj) The source character
                - target    = (battleChar obj) The target character

            Returns:
                (str) Name of the effect or stat change
            """
            if not isinstance(source, battleChar):
                raise TypeError('arg source must be an battleChar obj')
            if not isinstance(target, battleChar):
                raise TypeError('arg target must be an battleChar obj')
            
            if (self._name=='bardic_inspiration'):
                source_level = source.char_stats.class_level['bard']
                if (source_level >= 15):
                    prop = '1d12'
                elif (source_level >= 10):
                    prop = '1d10'
                elif (source_level >= 5):
                    prop = '1d8'
                else:
                    prop = '1d6'
                target.char_resources.add_condition(name='bardic_inspiration', duration='10 minute', prop=prop)
                return 'bardic_inspiration'
        # End _do_stats method

        def _do_special(self, source, pass_arg=None):
            """All special actions that do not fall into other categories.

            Args:
                - source    = (battleChar obj) Character that does this action
                - pass_arg  = (any, optional) Any args that you would need to pass to sub function

            Returns:
                (dict) All characters affected by this action, and what happened to them
            """
            if not isinstance(source, battleChar):
                raise TypeError('arg source must be a battleChar obj')
            if (self._name=='long_rest'):
                source.char_resources.long_rest(source.char_stats)
                return {source._name: 0}
            if (self._name=='short_rest'):
                source.char_resources.short_rest(source.char_stats, spend_dice=pass_arg)
                return {source._name: 0}
            if (self._name=='death_save'):
                return {source._name: source.char_resources.do_death_save()}
            if (self._name=='wild_shape'):
                if not isinstance(pass_arg, str):
                    raise TypeError('arg pass_arg must be a str for wild_shape')
                source.char_resources.add_condition('wild_shape', f'{source.char_stats.class_level["druid"] // 2} hour', pass_arg)
                return {source._name: f'wild shape as {pass_arg}'}
            if (self._name=='drop_wild_shape'):
                source.char_resources.remove_condition('wild_shape')
                return {source._name: 'dropped wild shape'}
        # End _do_special method

        def do_action(self, source, target=[], pass_arg=None):
            """Do this action given the source and target. If an attack or spell with multiple possible targets, will go through the target list in order,
            looping on itself if necessary.

            Args:
                - source    = (battleChar obj) The source of the action
                - target    = (list of battleChar obj, optional) The target of the action. Default=[]
                - pass_arg  = (any, optional) Any args you would need to pass to sub action

            Returns:
                (dict) All characters affected by this action, and what happened to them
            """
            if not isinstance(source, battleChar):
                raise TypeError('arg source must be a battleChar obj')
            if not isinstance(target, list):
                raise TypeError('arg target must be a list of battleChar obj')

            return_val = {}
            if (self._handle == 'attack'):
                target_len = len(target)
                if (target_len == 0):
                    raise ValueError('cannot have an empty target list for attacks')

                # Override pass_arg by action
                if (self._name=='martial_arts'):
                    pass_arg = 'unarmed'

                # Will get random attack if one is not specified
                if not pass_arg:
                    log.simulatn(f'{source._name} is picking a random attack')
                    pass_arg = source.get_random_attack()

                if not isinstance(pass_arg, str):
                    raise TypeError('arg pass_arg needs to be a str for an attack')

                # Override attack
                if (('monk' in source.char_stats.class_level) and (pass_arg=='unarmed')):
                    for i_attack in source.char_attacks:
                        if ('unarmed' in i_attack):
                            pass_arg = i_attack
                            break
                if ('shillelagh' in source.char_resources.cond):
                    if ('club' in pass_arg):
                        pass_arg = 'club_shillelagh'
                    elif ('quarterstaff' in pass_arg):
                        pass_arg = 'quarterstaff_shillelagh'

                if (pass_arg not in source.char_attacks):
                    raise ValueError(f'{source._name} does not have an attack {pass_arg}')

                # Create attack obj
                split_list = pass_arg.split(' ')
                if (len(split_list)==2):
                    this_attack = _create_attack(name=split_list[0], in_json=split_list[1])
                else:
                    this_attack = _create_attack(pass_arg)

                # Get attack count
                attack_count = this_attack._multi
                if (self._name=='extra_attack'):
                    attack_count = 2 * attack_count
                for i in range(attack_count):
                    this_target = target[i%target_len]
                    if not isinstance(this_target, battleChar):
                        raise TypeError('target is not a battleChar')
                    return_val[this_target._name] = self._do_attack(source=source, target=this_target, in_attack=this_attack, offhand=(self._name=='offhand_attack'))
            # End if handle==attack branch

            elif (self._handle == 'spell'):
                return_val = self._do_spell(source=source, target=target)

            elif (self._handle == 'move'):
                return_val[source._name] = self._do_move(source=source, distance=pass_arg)
            # End if handle==move branch

            elif (self._handle == 'stat'):
                for i_target in target:
                    if not isinstance(i_target, battleChar):
                        raise TypeError('target is not a battleChar')
                    return_val[i_target._name] = self._do_stat(source=source, target=i_target)

            else:
                return_val = self._do_special(source=source, pass_arg=pass_arg)
            return return_val
        # End do_action method
    # End characterAction class

    def add_char(self, name, team, stats={}, attacks={}, unique_actions={}, bias={}, act_cat=[], act_inc=[], res_inc=[], prop={}, instances=1):
        """Will add a character to the battle

        Args:
            - name      = (str) The name of the character
            - team      = (str) The team of the character. One of [pc, ally, enemy]
            - stats     = (dict, optional) Stats of the character. See battleChar.set_stats method
            - attacks   = (dict, optional) Attacks of the character. See battleChar.add_attack method
            - actions   = (dict, optional) Actions of the character. See battleChar.actionChooser.add_action method
            - bias      = (dict, optional) Any bias changes for actions. See battleChar.actionChooser.change_bias method
            - act_cat   = (list of str, optional) Which category of actions to automatically include. See battleChar.actionChooser.__init__
            - act_inc   = (list of str, optional) Which individual actions to automatically include. See battleChar.actionChooser.__init__
            - res_inc   = (list of str, optional) Add special resources. See battleChar.resources.add_miscellaneous method
            - prop      = (dict, optional) Add properties. See battleChar.stats.add_property method
            - instances = (int, optional) The number of instances of this character to do. Default=1.

        Returns:
            No return value
        """
        def _create_char(nam):
            if (nam in self.characters):
                raise ValueError(f'character {nam} already exists')
            new_char = battleChar(name=nam, team=team, stat_dict=stats, act_cat=act_cat, act_inc=act_inc)
            if prop:
                new_char.char_stats.add_property(prop)
            if res_inc:
                new_char.char_resources.add_miscellaneous(res_inc)
            if attacks:
                new_char.add_attack(attacks)
            log.debugall(f'{nam} attacks: {new_char.char_attacks}')
            if unique_actions:
                new_char.char_actions.add_action(unique_actions)
            if bias:
                new_char.char_actions.change_bias(bias)
            log.debugall(f'{nam} actions: {new_char.char_actions.get_all_actions()}')
            self.characters[nam] = new_char
            if (team=='enemy'):
                self._valid_bad.append(nam)
            else:
                self._valid_good.append(nam)
            log.battle(f'All good characters: {self._valid_good} | All bad characters: {self._valid_bad}')
        # End _creat_char inner function

        # Get all instance counts to see if PC or instances of this NPC already exists
        unique_dict = {}
        for i_character in self.characters:
            split_list = i_character.split('#')
            if (split_list[0] not in unique_dict):
                unique_dict[split_list[0]] = 1
            else:
                unique_dict[split_list[0]] += 1

        # Create a PC
        if (team=='pc'):
            if (name in unique_dict):
                raise ValueError(f'pc {name} already exists')
            _create_char(name)

        # Create multiple instances of an NPC
        else:
            if not isinstance(instances, int):
                raise TypeError('arg instances must be an int')
            if (instances < 1):
                raise ValueError('arg instances must be > 0')
            if (name in unique_dict):
                lower_range = unique_dict[name]
            else:
                _create_char(name)
                lower_range = 1
                instances -= 1
            for i in range(lower_range, lower_range + instances):
                _create_char(f'{name}#{i}')
        self._name_spacing = max(self._name_spacing, len(name)+2)
    # End add_char method

    def reset_battle(self):
        """Have all characters do a long rest to reset the battle

        Args:
            No args

        Returns:
            No return value
        """
        log.battle('reseting the battle')
        for i_name, i_character in self.characters.items():
            self.char_do_action(i_name, 'long_rest')
        self.estimated_time = 0
    # End reset_battle method

    def _log_hp(self, character):
        """Logs the HP of the specified character

        Args:
            - character = (str) Name of the character to log

        Returns:
            No return value
        """
        if not isinstance(character, str):
            raise TypeError('arg character must be a str')
        if (character not in self.characters):
            raise ValueError(f'{character} is not a valid character')
        char_obj = self.characters[character]
        if not isinstance(char_obj, battleChar):
            raise TypeError(f'{character} has its corresponding obj not as battleChar')
        
        max_hp = char_obj.char_stats.max_hp
        current_hp = char_obj.char_resources.hp
        blocks = int(20 * current_hp / max_hp)
        space = ' ' * (20 - blocks)
        blocks = '|' * blocks
        log.picture(f'{character:>{self._name_spacing}} HP = {current_hp:4} [{space}{blocks}]')
    # End _log_hp method

    def log_hp(self):
        """Logs the HP of every character

        Args:
            No args

        Returns:
            No return value
        """
        pc_list = []
        ally_list = []
        for i_char in self._valid_good:
            if (self.characters[i_char].team=='pc'):
                pc_list.append(i_char)
            else:
                ally_list.append(i_char)
        log.picture('PLAYER CHARACTERS')
        for i_char in pc_list:
            self._log_hp(i_char)
        log.picture('ALLY NON-PLAYER CHARACTERS')
        for i_char in ally_list:
            self._log_hp(i_char)
        log.picture('ENEMY NON-PLAYER CHARACTERS')
        for i_char in self._valid_bad:
            self._log_hp(i_char)
    # End log_hp method

    def set_initiative(self):
        """Have all characters roll for initiative, and save the initiative order. Repopulates attributes _valid_good and _valid_bad.

        Args:
            No args

        Returns:
            No return value
        """
        def by_second(in_val):
            return in_val[1]

        log.battle('all characters roll for initiative')
        self.initiative = []
        self._valid_bad = []
        self._valid_good = []
        for i_character, i_obj in self.characters.items():
            self.initiative.append((i_character, i_obj.char_stats.roll_ability('dex')))
            if (i_obj.team == 'enemy'):
                self._valid_bad.append(i_character)
            else:
                self._valid_good.append(i_character)
        self.initiative.sort(key=by_second, reverse=True)
        log.battle(f'Initiative order: {self.initiative}')
        self.log_hp()
        log.battle('================================================================')
        log.battle('========================= BATTLE START =========================')
        log.battle('================================================================\n')
        self.battlevalid = True
        self.current_turn = self.initiative[0][0]
    # End set_initiative method

    def _get_next_in_initiative(self):
        """Gets the next person in initiative after the current character's turn

        Args:
            No args

        Returns: (tuple)
            - (str) The name of the character who is next
            - (bool) If the last person in initiative was reached
        """
        current_index = -1
        for i, i_tuple in enumerate(self.initiative):
            if (i_tuple[0]==self.current_turn):
                current_index = i
                break
        if (current_index==-1):
            raise Exception('could not find the current character in initiative order; something went wrong')
        if (current_index + 1 == len(self.initiative)):
            return (self.initiative[0][0], True)    # We are at the end of initiative list; start from beginning
        return (self.initiative[current_index + 1][0], False)
    # End _get_next_in_initiative method

    def _remove_valid(self, character):
        """Removes a character from the valid lists so it cannot be a target any more

        Args:
            - character = (str) Name of the character to be removed

        Returns:
            (bool) If upon removing the character, the valid list for that team is empty
        """
        if character in self._valid_good:
            self._valid_good.remove(character)
        elif character in self._valid_bad:
            self._valid_bad.remove(character)
        else:
            raise ValueError(f'{character} was not a valid character to remove')

        for i, i_tuple in enumerate(self.initiative):
            if (i_tuple[0] == character):
                target_index = i
        del self.initiative[target_index]
        log.battle(f'Removed {character} | All good characters: {self._valid_good} | All bad characters: {self._valid_bad}')
        if ((not self._valid_bad) or (not self._valid_good)):
            return True
        return False
    # End _remove_valid method

    def _get_rand_valid(self, team):
        """Will return a random valid character from the specified team

        Args:
            - team = (str) Which team to get from. One of [good, bad, any]

        Returns:
            - None if there are no valid targets on that team, otherwise
            - (str) The name of the character chosen
        """
        if (team == 'good'):
            if not self._valid_good:
                return None
            return random.choice(self._valid_good)
        elif (team == 'bad'):
            if not self._valid_bad:
                return None
            return random.choice(self._valid_bad)
        valid_list = []
        valid_list += list(self._valid_bad)
        valid_list += list(self._valid_good)
        return random.choice(valid_list)
    # End _get_rand_valid method

    def _add_time(self, character, action_handle='attack'):
        """Add to the estimated elapsed time depending on the character and action

        Args:
            - character = (str) The character who is acting
            - action_handle = (str, optional) What kind of action they are doing. One of [attack, spell, move, stat, contest, special]. Default=attack

        Returns:
            (int) The estimated time that the character's turn would have taken
        """
        if (character not in self.characters):
            raise ValueError(f'{character} is not a valid chracter')
        
        if (self.characters[character].team == 'pc'):
            return_val = 10
        else:
            return_val = 4

        if (action_handle=='attack'):
            return_val = int(return_val * 1.5)
        elif (action_handle=='spell'):
            return_val = int(return_val * 2)
        elif (action_handle=='move'):
            return_val = int(return_val * 1.1)
        else:
            pass
        self.estimated_time += return_val
        return return_val
    # End _add_time method

    def get_targets_for_action(self, name):
        """Will look at the specified action, and return what are the valid targets 

        Args:
            - name = (str) The action to get targets

        Return:
            (list of str) What are the valid targets of this action
        """
        if (name not in self.cached_actions):
            self.cached_actions[name] = self.characterAction(name=name)
            log.debugall(f'cached action {name}')
        return self.cached_actions[name].targets
    # End get_targets_for_action method

    def char_do_action(self, source, name, target=[], pass_arg=None):
        """Have the specified character do the action. If the action is not cached, will create a cache of it.

        Args:
            - source    = (str) The character doing the action
            - name      = (str) The name of the action
            - target    = (list of str, optional) The character targets for the action if needed. If Default=[], will get a random valid target if needed.
            - pass_arg  = (str, optional) Any additional args that you would need to pass for the action.

        Returns:
            (int) Estimated number of seconds the action would have taken in real life considering admin
        """
        if (source not in self.characters):
            raise ValueError(f'battle does not have a character {source}')
        source_obj = self.characters[source]
        if not isinstance(source_obj, battleChar):
            raise TypeError(f'{source} has its matching obj not as battleChar')
        if (name not in self.cached_actions):
            self.cached_actions[name] = self.characterAction(name=name)
            log.debugall(f'cached action {name}')
        action_todo = self.cached_actions[name]
        if not isinstance(action_todo, self.characterAction):
            raise TypeError(f'{name} has its matching obj not as battleStage.characterAction')
        if (not source_obj.char_actions.can_do_action(name)):
            raise ValueError(f'{source} cannot do action {name}')
        action_cost = action_todo._cost
        if not isinstance(target, list):
            raise TypeError('arg target must be a list')

        # Conditions check
        def _check_cond(in_str):
            return in_str in source_obj.char_resources.cond
        # End _check_cond inner function
        if (_check_cond('dying') and not _check_cond('stabilized')):
            if (action_cost=='regular'):
                log.action(f'{source} will do death_save because they are dying and not stabilized')
                name = 'death_save'
            else:
                log.action(f'{source} does nothing because they are dying')
                return 0
        elif (_check_cond('incapacitated') and (action_cost != 'movement')):
            log.action(f'{source} is incapacitated and cannot do actions or reactions')
            return 0
        if (action_cost == 'movement'):
            if _check_cond('prone'):
                log.action(f'{source} is prone and can only crawl')
                if ('crawl' not in self.cached_actions):
                    self.cached_actions['crawl'] = self.characterAction('crawl')
                action_todo = self.cached_actions['crawl']
            elif _check_cond('stunned') or _check_cond('unconscious'):
                log.action(f'{source} cannot move because they are stunned or unconscious')
                return 0

        # Determine if targets are valid
        need_target = action_todo.target
        if need_target:
            # If there is no targets specififed and we need one, get a random one
            log.simulatn(f'{source} is determining a valid target')
            if not target:
                if (need_target == ['enemy']):
                    rand_target = self._get_rand_valid('good' if (source_obj.team=='enemy') else 'bad')
                elif (need_target == ['self', 'ally']):
                    rand_target = self._get_rand_valid('bad' if (source_obj.team=='enemy') else 'good')
                elif (need_target == ['ally']):
                    valid_list = []
                    valid_list += self._valid_bad if (source_obj.team=='enemy') else self._valid_good
                    valid_list.remove(source)
                    rand_target = random.choice(valid_list)
                elif (need_target == ['self']):
                    rand_target = source
                else:
                    rand_target = self._get_rand_valid('any')

                if not rand_target:
                    log.simulatn(f'There were no valid targets for {source} doing action {name}')
                    return 0
                true_target = [rand_target]
            # End get random target branch

            # Check all targets
            else:
                true_target = []
                if (need_target == ['enemy']):
                    valid_targets = self._valid_good if (source_obj.team=='enemy') else self._valid_bad
                elif (need_target == ['self', 'ally']):
                    valid_targets = self._valid_bad if (source_obj.team=='enemy') else self._valid_good
                elif (need_target == ['self']):
                    valid_targets = [source]
                else:
                    valid_targets = []
                    valid_targets += self._valid_bad
                    valid_targets += self._valid_good
                log.debugall(f'valid={valid_targets}')
                for i_target in target:
                    if (i_target not in valid_targets):
                        log.debug(f'{source} cannot target {i_target} with {name}')
                    else:
                        true_target.append(i_target)
            obj_list = [self.characters[i] for i in true_target]
        else:
            obj_list = []

        # Determine distance
        if (action_cost=='movement'):
            # Will move full distance if not specified
            if not pass_arg:
                log.simulatn(f'{source} will move using all their movement')
                pass_arg = source_obj.char_resources.movement
            if not isinstance(pass_arg, float):
                raise TypeError('arg pass_arg needs to be an float for movement')
            if (pass_arg < 0):
                raise ValueError('arg pass_arg must be non-negative for movement')

        # Do action
        print_str = f'{source} is doing action {name}'
        if target:
            print_str += f' on targets {target}'
        if pass_arg:
            print_str += f' with {pass_arg}'
        log.action(print_str)
        affected_dict = action_todo.do_action(source=source_obj, target=obj_list, pass_arg=pass_arg)
        log.debug(f'affected by action of {source}: {affected_dict}')
        source_obj.char_resources.add_resource({action_cost: -1 if (action_cost != 'movement') else -1*pass_arg})

        # Check if target should be removed
        if (action_todo._handle=='attack'):
            for i_name, i_hp in affected_dict.items():
                if ((i_hp==0) and ('death' in self.characters[i_name].char_resources.cond)):
                    log.battle(f'removing {i_name} because they are dead')
                    self.battlevalid = not self._remove_valid(i_name)
        if (action_todo._name=='death_save'):
            if (affected_dict[source]['fail'] >= 3):
                log.battle(f'removing {i_name} because they are dead')
                self.battlevalid = not self._remove_valid(i_name)

        # Return time to complete
        return self._add_time(source, action_todo._handle)
    # End char_do_action

    def char_do_random_action(self, source, act_type='regular'):
        """Have the specified character do a random action they can do. Will target only one other character.

        Args:
            - source    = (str) Name of the character to do the action
            - act_type  = (str, optional) The action type to get. One of [regular, move, bonus, reaction, free, special]

        Returns:
            (int) Estimated number of seconds the action would have taken in real life considering admin
        """
        if (source not in self.characters):
            raise ValueError(f'{source} is not a valid character')
        source_obj = self.characters[source]
        if not isinstance(source_obj, battleChar):
            raise TypeError(f'{source} has its matching obj not as battleChar')
        log.simulatn(f'{source} is going to do a {act_type} action')
        random_action = source_obj.get_random_action(act_type=act_type)
        if not random_action:
            log.simulatn(f'{source} has no {act_type} actions available')
            return 0
        return self.char_do_action(source=source, name=random_action)
    # End char_do_random_action method

    def simulate_turn(self, character=''):
        """Simulate the turn of the specified character.

        Args:
            - character = (str, optional) Name of the character to simulate. If Default='', will use the current turn characters

        Returns:
            (int) Estimated number of seconds the turn would have taken in real life considering admin
        """
        if not isinstance(character, str):
            raise TypeError('arg character must be a str')
        if (character == ''):
            character = self.current_turn
        if (character not in self.characters):
            raise ValueError(f'{character} is not a valid character')
        char_obj = self.characters[character]
        if not isinstance(char_obj, battleChar):
            raise TypeError(f'{character} has its obj not a battleChar')
        
        return_val = 0
        log.turn(f'Starting turn of {character} at {round(self.estimated_time / 60, 2)} minutes')
        resources = char_obj.char_resources.start_turn()

        # Do regular actions
        if (resources['regular'] > 0):
            for i in range(resources['regular']):
                return_val += self.char_do_random_action(character, 'regular')
        resources = char_obj.char_resources.get_resources_for_round()

        # Do bonus actions
        if (resources['bonus'] > 0):
            for i in range(resources['bonus']):
                return_val += self.char_do_random_action(character, 'bonus')

        # Do move actions
        if (resources['movement'] > 0):
            return_val += self.char_do_random_action(character, 'move')

        # End turn
        char_obj.char_resources.end_turn()
        log.turn(f'Finished turn of {character} at {round(self.estimated_time / 60, 2)} minutes (took {return_val} seconds)\n')
        return return_val
    # End simulate_turn method

    def simulate_round(self):
        """Will go through all characters in initiative order and have them attack a random valid character

        Args:
            No args

        Returns:
            No return value
        """
        if not self.battlevalid:
            raise Exception('Battle cannot be simulated; do set_initiative() to reset')
        log.round(f'=================== Start of round {self.round:2} ===================')
        elapsed_time = 0
        for i in range(len(self.characters)):
            elapsed_time += self.simulate_turn()
            (next_char, reached_end) = self._get_next_in_initiative()
            self.current_turn = next_char
            if reached_end:
                break
        log.round(f'============= Finished round {self.round} (took {round(elapsed_time / 60, 2)} minutes) =============')
        log.round(f'Battle has taken {round(self.estimated_time / 60, 2)} minutes so far')
        self.log_hp()
        log.round(f'================================================================\n')
        self.round += 1
    # End simulate round method

    def simulate_to_end(self, max_round=100):
        """Will keep doing simulate_round until the battle is over (one side has no more valid targets) or the round limit is hit

        Args:
            - max_round = (int, optional) The maximum number of rounds. Default=100.

        Returns:
            (int) The number of rounds that was simulated
        """
        self.reset_battle()
        self.set_initiative()
        return_val = max_round
        for i in range(max_round):
            self.simulate_round()
            if not self.battlevalid:
                return_val = self.round
                break
        log.battle(f'Finished combat after {return_val} rounds (estimated time={round(self.estimated_time / 60, 2)} minutes)')
        return return_val
    # End simulate_to_end method
# End battleStage class

################################################################################################################################
#=========================================================== CUSTOM ===========================================================
################################################################################################################################

def custom_spell(name, source, target=[], pass_arg=None):
    """The effect of a custom spell. You should create an if-branch for each spell

    Args:
        - name = (str) The name of the spell
        - source = (battleChar obj) The character that is casting the spell
        - target = (list of battleChar obj, optional) The target characters of the spell. Default=[]
        - pass_arg = (any, optional) Any additional arguments that the spell needs. Default=None.

    Returns: (dict) Results for each target
        - Key                           | Value
        - {name of affected character}  | (str) What happened to the character
    """
    if not isinstance(name, str):
        raise TypeError('arg name must be a str')
    if not isinstance(source, battleChar):
        raise TypeError('arg source must be a battleChar obj')
    if not isinstance(target, list):
        raise TypeError('arg target must be a list of battleChar obj')

    if name == 'unstoppable':
        return {f'{source._name}': 'unstoppable condition'}

    raise ValueError(f'could not find custom spell {name}')
# End custom_spell

################################################################################################################################
#============================================================ MAIN ============================================================
################################################################################################################################

def main():
    """Automatically creates a battle and simulates it to the end of combat.

    Args:
        No args

    Returns:
        None
    """
    battle = battleStage()
    try:
        battle.simulate_to_end()
    except Exception as err:
        log.exception('ended early because of exception', exc_info=err)
    log.header('.\n.\n.\n.')
# End main

if __name__ == '__main__':
    main()

# eof