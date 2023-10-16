#!/usr/bin/env python3
# description:  Script to simulate DnD combat
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20231016

"""Script that will simulate DnD combat.
To do:
    Movement
    Wild shape
    Equipped weapon on character

Functions:
    custom_hit_conditions
    custom_conditional_damage
    custom_spell
    custom_condition
    _create_attack
Classes:
    attack
    spell
    action
    combat
        characterAction
Main in this file
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import time
import random
import json
import argparse
import customLogging
from rollFunctions import roll
from combatCharacter import combatCharacter
from action import action

################################################################################################################################
#=========================================================== SET UP ===========================================================
################################################################################################################################

parser = argparse.ArgumentParser()
parser.add_argument('--json', dest='charJson', action='store', default='characters.json', help='Which json to load for the characters')
parser.add_argument('--num', '-n', type=int, dest='numRounds', action='store', default=100, help='The maximum number of rounds to simulate')
parser.add_argument('--noPict', dest='noPicture', action='store_true', help='If the attack picture should be generated')
parser.add_argument('--log', type=str, dest='logLevel', action='store', default='roll', help='What level the log file should be')
parser.add_argument('--console', type=str, dest='consoleLevel', action='store', default='action', help='What level the console output should be')

if not customLogging.os.path.exists('./logs'):
    customLogging.os.mkdir('./logs')
    print('Created logs folder')


################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class combat(object):
    """The object that handles all the characters and interactions between them.

    Args:
        - in_log        = (customLogging.custom_logger obj) Log for all output
        - in_json       = (str, optional) Path of a json to load automaticall add all characters. Default=characters.json
        - max_round     = (int, optional) The desired number of rounds to simulate, provided there are no overrides. See combat.simulate_to_end method. Default=10.
        - no_pictures   = (bool, optional) If there should be no attack pictures generated. Default=False.

    Classes:
        characterAction:    action that a character can do

    Methods:
        - add_char                  :adds a new character to the battle
        - _remove_valid             :removes character from valid list
        - _get_rand_valid           :get a random character from the valid lists

        - _add_time                 :add to estimated time
        - _create_action            :create an action obj and put in cache
        - _get_action               :get action obj from cache
        - get_targets_for_action    :get the targets for an action
        - char_do_action            :have specified character do an action
        - char_do_random_action     :have the specified character do a random action

        - _log_hp                   :logs the current HP of a character
        - log_combat_hp             :logs the current HP of all characters

        - reset_battle              :restores all characters to full
        - set_initiative            :sets the initiative order
        - _get_next_in_initiative   :gets the next person in initiative order

        - _pc_dying                 :will check if any player characters are dying

        - simulate_turn             :simulate the turn of a character
        - simulate_round            :simulate one round of combat
        - simulate_to_end           :simulate until end of combat
    """
    def __init__(self, in_log, in_json='characters.json', max_round=10, no_pictures=False):
        """Init for combat

        Args:
            - in_log        = (customLogging.custom_logger obj) Log for all output
            - in_json       = (str, optional) Path of a json to load automaticall add all characters. Default=characters.json
            - max_round     = (int, optional) The desired number of rounds to simulate, provided there are no overrides. See combat.simulate_to_end method. Default=10.
            - no_pictures   = (bool, optional) If there should be no attack pictures generated. Default=False.

        Attributes:
            - log               = (customLogging.custom_logger obj) Log for all output
            - roll              = (rollFunctions.roll obj) All functions for dice rolls

            - _default_max      = (int) The default number of rounds to simulate to. See simulate_to_end method
            - _pict             = (bool) If there should be attack pictures

            - battlevalid       = (bool) If the battle is valid and can be simulated
            - round             = (int) What round the battle is in
            - _name_spacing     = (int) The length of the longest name of all characters

            - characters        = (dict of combatCharacter objects) All characters in the battle
            - _valid_good       = (list of str) All good characters that can be targeted
            - _valid_bad        = (list of str) All bad characters that can be targeted

            - initiative        = (list of tuple) The initiative order of all characters
                - (str) Name of the character
                - (int) What they rolled for initiative
            - current_turn      = (int) Which character has their turn during the current round
            - estimated_time    = (int) Estimated time that has elapsed over the battle in seconds

            - cached_actions    = (dict of action obj) All actions that have been created already
            - environment       = (dict) The current status combat environment
                - Key           | Value
                - {status name} | (any) The value for this status key
        """
        if not isinstance(in_log, customLogging.custom_logger):
            raise TypeError(f'arg in_log must be a customLogging.custom_logger obj')
        self.log = in_log
        self.roll = roll(in_log=in_log)
        self.log.header('Creating battle stage')
        if not isinstance(max_round, int):
            raise TypeError('arg max_round must be an int')
        if (max_round <= 0):
            self.log.warning('Overriding arg max_round because it was <= 0')
            max_round = 10
        self._default_max = max_round
        self._pict = not bool(no_pictures)
        self.battlevalid = False
        self.round = 1
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
        self.environment = {}
        self.log.header('finished battle stage init\n')
    # End __init__

    ################################################################
    #====================== HANDLE CHARACTERS ======================
    ################################################################

    def add_char(self, name, team, stats={}, attacks={}, unique_actions={}, bias={}, act_cat=[], act_inc=[], res_inc=[], prop={}, instances=1):
        """Will add a character to the battle

        Args:
            - name      = (str) The name of the character
            - team      = (str) The team of the character. One of [pc, ally, enemy]
            - stats     = (dict, optional) Stats of the character. See combatCharacter.set_stats method
            - attacks   = (dict, optional) Attacks of the character. See combatCharacter.add_attack method
            - actions   = (dict, optional) Actions of the character. See combatCharacter.actionChooser.add_action method
            - bias      = (dict, optional) Any bias changes for actions. See combatCharacter.actionChooser.change_bias method
            - act_cat   = (list of str, optional) Which category of actions to automatically include. See combatCharacter.actionChooser.__init__
            - act_inc   = (list of str, optional) Which individual actions to automatically include. See combatCharacter.actionChooser.__init__
            - res_inc   = (list of str, optional) Add special resources. See combatCharacter.resources.add_miscellaneous method
            - prop      = (dict, optional) Add properties. See combatCharacter.stats.add_property method
            - instances = (int, optional) The number of instances of this character to do. Default=1.

        Returns:
            No return value
        """
        def _create_char(nam):
            if (nam in self.characters):
                raise ValueError(f'character {nam} already exists')
            new_char = combatCharacter(name=nam, in_log=self.log, team=team, stat_dict=stats, act_cat=act_cat, act_inc=act_inc)
            if prop:
                new_char.char_stats.add_property(prop)
            if res_inc:
                new_char.char_resources.add_miscellaneous(res_inc)
            if attacks:
                new_char.add_attack(attacks)
            self.log.debugall(f'{nam} attacks: {new_char.char_attacks}')
            if unique_actions:
                new_char.char_actions.add_action(unique_actions)
            if bias:
                new_char.char_actions.change_bias(bias)
            self.log.debugall(f'{nam} actions: {new_char.char_actions.get_all_actions()}')
            self.characters[nam] = new_char
            if (team=='enemy'):
                self._valid_bad.append(nam)
            else:
                self._valid_good.append(nam)
            self.log.battle(f'All good characters: {self._valid_good} | All bad characters: {self._valid_bad}')
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
        self.log.battle(f'Removed {character} | All good characters: {self._valid_good} | All bad characters: {self._valid_bad}')
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

    ################################################################
    #======================= COMBAT ACTIONS =======================
    ################################################################

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
            return_val = 12
        else:
            return_val = 5

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

    def _create_action(self, act_name):
        """Creates an action obj and stores it in the cache

        Args:
            - act_name = (str) The name of the action

        Returns:
            (action obj) The action that was just created
        """
        if not isinstance(act_name, str):
            raise TypeError('arg act_name must be a str')
        if (act_name in self.cached_actions):
            raise ValueError(f'action {act_name} is already cached')
        split_list = act_name.split(' ', maxsplit=1)
        if (len(split_list) == 2):
            self.cached_actions[act_name] = action(name=split_list[0], in_log=self.log, in_roll=self.roll, in_json=split_list[1], do_pict=self._pict)
        else:
            self.cached_actions[act_name] = action(name=act_name, in_log=self.log, in_roll=self.roll, do_pict=self._pict)
        self.log.debugall(f'cached action {act_name}')
        return self.cached_actions[act_name]
    # End _create_action method

    def _get_action(self, act_name):
        """Will get the specified action from the cache. If the action is not in the cache, will add to cache.

        Args:
            - act_name = (str) Name of the action to get

        Returns:
            (action obj) The obj of this action in the cache
        """
        if not isinstance(act_name, str):
            raise TypeError('arg act_name must be str')
        if (act_name not in self.cached_actions):
            return self._create_action(act_name=act_name)
        return self.cached_actions[act_name]
    # End _get_action method

    def get_targets_for_action(self, act_name, source):
        """Will look at the specified action, and return what are the valid targets. Will if a good character is to target another good character,
        will skip over ally NPCs so that they do not become targets of any buffs.

        Args:
            - act_name  = (str) The action to get targets
            - source    = (str) The character doing this action

        Return:
            (list of str) What are the valid targets of this action
        """
        if not isinstance(act_name, str):
            raise TypeError('arg act_name must be an str')
        action_obj = self._get_action(act_name=act_name)
        if not isinstance(action_obj, action):
            raise TypeError(f'key "{act_name}" had its value not an action obj')
        if not isinstance(source, str):
            raise TypeError('arg source must be an str')
        source_obj = self.characters[source]
        if not isinstance(source_obj, combatCharacter):
            raise TypeError(f'key "{source}" had its value not a combatCharacter obj')

        # Return by specific actions
        if (act_name == 'stabilize'):
            return self.environment['dying_pc'] if ('dying_pc' in self.environment) else []

        if (action_obj.target == ['enemy']):
            return self._valid_good if (source_obj.team=='enemy') else self._valid_bad
        elif (action_obj.target == ['self', 'ally']):
            # Skip over NPCs
            if (source_obj.team == 'pc'):
                return_val = []
                for i_character in self._valid_good:
                    char_obj = self.characters[i_character]
                    if not isinstance(char_obj, combatCharacter):
                        raise TypeError(f'key "{i_character}" has its value not a combatCharacter obj')
                    if (char_obj.team == 'pc'):
                        return_val.append(i_character)
                return return_val
            return self._valid_bad if (source_obj.team=='enemy') else self._valid_good
        elif (action_obj.target == ['ally']):
            return_val = self._valid_bad.copy() if (source_obj.team=='enemy') else self._valid_good.copy()
            return_val.remove(source)
            return return_val
        elif (action_obj.target == ['self']):
            return [source]
        else:
            return_val = []
            return_val += self._valid_bad
            return_val += self._valid_good
            return return_val
    # End get_targets_for_action method

    def char_do_action(self, source, act_name, target=[], additional={}):
        """Have the specified character do the action.

        Args:
            - source        = (str) The character doing the action
            - act_name      = (str) The name of the action
            - target        = (list of str, optional) The character targets for the action if needed. If Default=[], will get a random valid target if needed.
            - additional    = (dict, optional) Any additional args that you would need to pass to the action. Default={}.

        Returns:
            (int) Estimated number of seconds the action would have taken in real life considering admin
        """
        if (source not in self.characters):
            raise ValueError(f'battle does not have a character {source}')
        source_obj = self.characters[source]
        if not isinstance(source_obj, combatCharacter):
            raise TypeError(f'key "{source}" has its value not a combatCharacter obj')
        if not isinstance(act_name, str):
            raise TypeError('arg act_name must be a str')
        action_obj = self._get_action(act_name=act_name)
        if not isinstance(action_obj, action):
            raise TypeError(f'key "{act_name}" has its value not a action obj')
        if (not source_obj.char_actions.can_do_action(act_name)):
            raise ValueError(f'{source} cannot do action {act_name}')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list of str')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')
        
        action_cost = action_obj.cost

        # Conditions check to override the action that is being taken
        def _check_cond(in_str):
            return in_str in source_obj.char_conditions
        # End _check_cond inner function

        if (_check_cond('dying') and not _check_cond('stabilized')):
            if (action_cost=='regular'):
                self.log.action(f'{source} will do death_save because they are dying and not stabilized')
                action_obj = self._get_action('death_save')
                if not isinstance(action_obj, action):
                    raise TypeError(f'key "{act_name}" has its value not a action obj')
            else:
                self.log.action(f'{source} does nothing because they are dying')
                return 0

        elif (_check_cond('incapacitated') and (action_cost != 'movement')):
            self.log.action(f'{source} is incapacitated and cannot do actions or reactions')
            return 0

        if (action_cost == 'movement'):
            if _check_cond('prone'):
                self.log.action(f'{source} is prone and can only crawl')
                action_obj = self._get_action('crawl')
                if not isinstance(action_obj, action):
                    raise TypeError(f'key "{act_name}" has its value not a action obj')
            elif _check_cond('stunned') or _check_cond('unconscious'):
                self.log.action(f'{source} cannot move because they are stunned or unconscious')
                return 0

        # Determine if targets are valid
        true_target = []
        target_obj_list = []
        need_target = action_obj.target
        if need_target:
            # If there is no targets specififed and we need one, get a random one
            if not target:
                self.log.simulatn(f'{source} is determining a valid target')
                true_target = self.get_targets_for_action(act_name=act_name, source=source)
                if not true_target:
                    self.log.simulatn(f'there were no valid targets for {source} to do {act_name} when it needs a target')
                    return 0
                target_obj_list = [self.characters[random.choice(true_target)]]

            # Check all targets
            else:
                true_target = []
                for i_target in target:
                    if ((i_target not in self._valid_bad) or (i_target not in self._valid_good)):
                        continue
                    true_target.append(i_target)
                if not true_target:
                    self.log.simulatn(f'there were no valid targets for {source} to do {act_name} when it needs a target')
                    return 0
                target_obj_list = [self.characters[i] for i in true_target]

        true_additional = additional.copy()

        # Determine attack
        if (action_obj._handle == 'attack'):
            # Will get random attack if none is provided
            if ('attack' not in additional):
                self.log.simulatn(f'{source} will use a random attack')
                true_additional['attack'] = source_obj.get_random_attack()
                if (true_additional['attack'] == ''):
                    self.log.simulatn(f'{source} has no attack to use')
                    return 0

        # Determine distance
        if (action_cost=='movement'):
            # Will move full distance if not specified
            if ('distance' not in additional):
                self.log.simulatn(f'{source} will move using all their movement')
                true_additional['distance'] = source_obj.char_resources.movement

        # Do action
        print_str = f'{source} is doing action {act_name}'
        if target_obj_list:
            print_str += ' on targets ['
            for i in target_obj_list:
                print_str += f'{i._name} '
            print_str += ']'
        if true_additional:
            print_str += f' with {true_additional}'
        self.log.action(print_str)
        affected_dict = action_obj.do_action(source=source_obj, target=target_obj_list, additional=true_additional)
        self.log.debug(f'affected by action of {source}: {affected_dict}')
        source_obj.char_resources.add_resource({action_cost: -1 if (action_cost != 'movement') else -1*true_additional['distance']})

        # Check if target should be removed
        if (action_obj._handle=='attack'):
            for i_name, i_hp in affected_dict.items():
                if ('death' in self.characters[i_name].char_conditions):
                    self.log.battle(f'removing {i_name} because they are dead')
                    self.battlevalid = not self._remove_valid(i_name)
        if (action_obj._name=='death_save'):
            if (affected_dict[source]['fail'] >= 3):
                self.log.battle(f'removing {i_name} because they are dead after three death save failures')
                self.battlevalid = not self._remove_valid(i_name)

        # Return time to complete
        return self._add_time(source, action_obj._handle)
    # End char_do_action

    def char_do_random_action(self, source, act_type='regular'):
        """Have the specified character do a random action they can do. Will target only one other character.

        Args:
            - source    = (str) Name of the character to do the action
            - act_type  = (str, optional) The action type to get. One of [regular, movement, bonus, reaction, free]. Default='regular'

        Returns:
            (int) Estimated number of seconds the action would have taken in real life considering admin
        """
        if (source not in self.characters):
            raise ValueError(f'{source} is not a valid character')
        source_obj = self.characters[source]
        if not isinstance(source_obj, combatCharacter):
            raise TypeError(f'{source} has its matching obj not as combatCharacter')
        if (act_type not in ['regular', 'movement', 'bonus', 'reaction', 'free']):
            raise ValueError('arg act_type must be in [regular, movement, bonus, reaction, free]')

        self.log.simulatn(f'{source} is going to do a random {act_type} action')
        random_action = source_obj.get_random_action(act_type=act_type)
        if not random_action:
            self.log.simulatn(f'{source} has no {act_type} actions available')
            return 0
        return self.char_do_action(source=source, act_name=random_action)
    # End char_do_random_action method

    ################################################################
    #========================== PICTURES ==========================
    ################################################################

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
        if not isinstance(char_obj, combatCharacter):
            raise TypeError(f'{character} has its corresponding obj not as combatCharacter')

        current_hp = char_obj.char_resources.hp
        if ('death' in char_obj.char_conditions):
            bar = f'{"DEAD":^25}'
        elif ('dying' in char_obj.char_conditions):
            death_saves = char_obj.char_resources.death_saves
            info = f'S:{death_saves["success"]} F:{death_saves["fail"]}'
            bar = f'{info:^25}'
        else:
            max_hp = char_obj.char_stats.max_hp
            blocks = int(25 * current_hp / max_hp)
            space = ' ' * (25 - blocks)
            blocks = '|' * blocks
            bar = f'{space}{blocks}'
        self.log.picture(f'{character:>{self._name_spacing}} HP = {current_hp:4} [{bar}]')
    # End _log_hp method

    def log_combat_hp(self):
        """Logs the HP of every character

        Args:
            No args

        Returns:
            No return value
        """
        pc_list = []
        ally_list = []
        enemy_list = []
        for i_name, i_obj in self.characters.items():
            if (i_obj.team=='pc'):
                pc_list.append(i_name)
            elif (i_obj.team=='ally'):
                if (i_name in self._valid_good):
                    ally_list.append(i_name)
            else:
                if (i_name in self._valid_bad):
                    enemy_list.append(i_name)

        self.log.picture('PLAYER CHARACTERS')
        for i_char in pc_list:
            self._log_hp(i_char)
        self.log.picture('ALLY NON-PLAYER CHARACTERS')
        for i_char in ally_list:
            self._log_hp(i_char)
        self.log.picture('ENEMY NON-PLAYER CHARACTERS')
        for i_char in enemy_list:
            self._log_hp(i_char)
    # End log_combat_hp method

    ################################################################
    #=========================== SET UP ===========================
    ################################################################

    def reset_battle(self):
        """Have all characters do a long rest to reset the battle (attribute round=1, estimated_time=0).

        Args:
            No args

        Returns:
            No return value
        """
        self.log.battle('reseting the battle')
        for i_name  in self.characters.keys():
            self.char_do_action(i_name, 'long_rest')
        self.round = 1
        self.estimated_time = 0
    # End reset_battle method

    def set_initiative(self):
        """Have all characters roll for initiative, and save the initiative order. Repopulates attributes _valid_good and _valid_bad.

        Args:
            No args

        Returns:
            No return value
        """
        def by_second(in_val):
            return in_val[1]

        self.log.battle('all characters roll for initiative')
        self.initiative = []
        self._valid_bad = []
        self._valid_good = []
        for i_character, i_obj in self.characters.items():
            if not isinstance(i_obj, combatCharacter):
                raise TypeError(f'key "{i_character}" had its value not a combatCharacter obj')
            self.initiative.append((i_character, i_obj.char_stats.roll_ability('dex')))
            if (i_obj.team == 'enemy'):
                self._valid_bad.append(i_character)
            else:
                self._valid_good.append(i_character)
        self.initiative.sort(key=by_second, reverse=True)
        self.log.battle(f'Initiative order: {self.initiative}')
        self.log_combat_hp()
        self.log.battle('================================================================')
        self.log.battle('========================= BATTLE START =========================')
        self.log.battle('================================================================\n')
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

    ################################################################
    #========================= ENVIRONMENT =========================
    ################################################################

    def _pc_dying(self):
        """Will go through all player characters and see if any are dying. This will update attribute environment.

        Args:
            No args

        Returns:
            No return value
        """
        for i_name, i_obj in self.characters.items():
            if not isinstance(i_obj, combatCharacter):
                raise TypeError(f'{i_name} has its corresponding obj not a combatCharacter')
            if (i_obj.team != 'pc'):
                continue

            dying_list = []
            if (('dying' in i_obj.char_conditions) and ('stabilized' not in i_obj.char_conditions)):
                dying_list.append(i_name)
            if dying_list:
                self.log.envrmnt('There is a PC that needs to be stabilized')
                self.environment['dying_pc'] = dying_list
            elif ('dying_pc' in self.environment):
                del self.environment['dying_pc']
    # End _pc_dying method

    ################################################################
    #====================== COMBAT SIMULATION ======================
    ################################################################

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
        if not isinstance(char_obj, combatCharacter):
            raise TypeError(f'key "{character}" has its value not a combatCharacter obj')
        
        return_val = 0
        self.log.turn(f'Starting turn of {character} at {round(self.estimated_time / 60, 2)} minutes')
        resources = char_obj.start_turn()
        self._pc_dying()
        cost_order = char_obj.update_act_bias(self.environment)

        # Iterate through [free, movement, regular, bonus, special] by default, or whatever order determined by update_act_bias
        for i_cost in cost_order:
            if (i_cost == 'free'):
                # For now only doing one free action
                return_val += self.char_do_random_action(character, 'free')
            elif (i_cost == 'movement'):
                # For now only doing one movement action
                return_val += self.char_do_random_action(character, 'movement')
            elif (i_cost == 'special'):
                # TODO
                pass
            else:
                # For all other actions, do as many times as they have resources for
                for i in range(resources[i_cost]):
                    return_val += self.char_do_random_action(character, i_cost)
            resources = char_obj.char_resources.get_resources_for_round()

        # End turn
        char_obj.end_turn()
        self.log.turn(f'Finished turn of {character} at {round(self.estimated_time / 60, 2)} minutes (took {return_val} seconds)\n')
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
        self.log.round(f'=================== Start of round {self.round:2} ===================')
        self.log.round(f'Initiative order: {self.initiative}\n')
        elapsed_time = 0
        for i in range(len(self.characters)):
            elapsed_time += self.simulate_turn()
            (next_char, reached_end) = self._get_next_in_initiative()
            self.current_turn = next_char
            if reached_end:
                break
        self.log.round(f'============= Finished round {self.round} (took {round(elapsed_time / 60, 2)} minutes) =============')
        self.log.round(f'Battle has taken {round(self.estimated_time / 60, 2)} minutes so far')
        self.log_combat_hp()
        self.log.round(f'================================================================\n')
        self.round += 1
    # End simulate round method

    def simulate_to_end(self, max_round=0):
        """Will keep doing simulate_round until the battle is over (one side has no more valid targets) or the round limit is hit

        Args:
            - max_round = (int, optional) The maximum number of rounds. If < 1, will use attribute _default_max. Default=0.

        Returns:
            (int) The number of rounds that was simulated
        """
        self.reset_battle()
        self.set_initiative()
        if (max_round < 1):
            max_round = self._default_max
        return_val = 1*max_round
        for i in range(max_round):
            self.simulate_round()
            if not self.battlevalid:
                return_val = self.round
                break
        else:
            self.log.battle(f'Ending early because hit round limit={self._default_max}')
        self.log.battle(f'Finished combat after {return_val} rounds (estimated time={round(self.estimated_time / 60, 2)} minutes)')
        return return_val
    # End simulate_to_end method
# End combat class

################################################################################################################################
#============================================================ MAIN ============================================================
################################################################################################################################

def main(in_json='', max_round=0, no_pictures=False, log_level='', console_level=''):
    """Automatically creates a battle and simulates it to the end of combat.

    Args:
        - in_json       = (str, optional) The json to load the characters. Default=''
        - max_round     = (int, optional) The maximum number of rounds to simulate. Default=0.
        - no_pictures   = (bool, optional) If the attack and spell pictures should be omitted. Default=False.
        - log_level     = (str, optional) The level the log file should create messages. These levels can be found in customLogging. Default=''
        - console_level = (str, optional) The level the console should create messages. Like above. Default=''

    Returns:
        None
    """
    args = parser.parse_args()
    current_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
    if (log_level or console_level):
        if (log_level):
            if (log_level not in customLogging._LEVEL_DICT):
                raise ValueError('arg log_level was not a valid level')
        else:
            log_level = 'roll'
        if (console_level):
            if (console_level not in customLogging._LEVEL_DICT):
                raise ValueError('arg console_level was not a valid level')
        else:
            console_level = 'picture'
        main_log = customLogging.create_custom_logger_with_handler(
            'battle', f'./logs/battle{current_time}.log',
            log_level, console_level,
            False, False
        )
    else:
        if (args.logLevel not in customLogging._LEVEL_DICT):
            raise ValueError('option --log not a valid level')
        if (args.consoleLevel not in customLogging._LEVEL_DICT):
            raise ValueError('option --console not a valid level')
        main_log = customLogging.create_custom_logger_with_handler(
            'battle', f'./logs/battle{current_time}.log',
            args.logLevel, args.consoleLevel,
            False, False
        )

    if (in_json or max_round):
        if (in_json):
            if not isinstance(in_json, str):
                raise TypeError('arg in_json must be a str')
            if (not in_json.endswith('.json')):
                main_log.warning('arg in_json was not a path to a json, will load no characters')
                in_json = ''
        else:
            # If max_round is provided, but in_json is not, automaticaly load characters.json
            in_json = 'characters.json'
        battle = combat(in_log=main_log, in_json=in_json, max_round=max_round, no_pictures=no_pictures)
    else:
        battle = combat(main_log, args.charJson, args.numRounds, args.noPicture)
    try:
        battle.simulate_to_end()
    except Exception as err:
        main_log.exception('ended early because of exception', exc_info=err)
# End main

if __name__ == '__main__':
    main()

# eof