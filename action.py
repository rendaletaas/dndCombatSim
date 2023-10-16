# description:  Contains the action class
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20231016

"""The action class.

Classes:
    action
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import json as _json
from rollFunctions import roll as _roll
import customLogging as _clog
from combatCharacter import combatCharacter as _combatCharacter
from attack import attack as _attack
from spell import spell as _spell

################################################################################################################################
#=========================================================== SET UP ===========================================================
################################################################################################################################

################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class action(object):
    """An action that happens between characters.

    Args:
        - name      = (str) The name of this action
        - in_log    = (customLogging.custom_logger obj) The log for all the messages
        - in_roll   = (rollFunctions.roll obj) The functions for all rolling
        - in_json   = (str, optional) The path of the json to load the action. Default=actions.json
        - do_pict   = (bool, optional) If pictures should be created. Default=True.

    Methods:
        - _log_attack_picture   :log the picture for an attack
        - _check_targets        :will look at all targets and see if they are valid
        - do_action             :will do this action
        - _do_attack            :handling for an attack action
        - _do_spell             :handling for a spell action
        - _do_movement          :handling for a movement action
        - _do_auto              :handling for an auto action
        - _do_contest           :handling for a contest action
        - _do_special           :handling for a special action
    """
    def __init__(self, name, in_log, in_roll, in_json='actions.json', do_pict=True):
        """Init for action

        Args:
            - name      = (str) The name of this action
            - in_log    = (customLogging.custom_logger obj) The log for all the messages
            - in_roll   = (rollFunctions.roll obj) The functions for all rolling
            - in_json   = (str, optional) The path of the json to load the action. Default=actions.json
            - do_pict   = (bool, optional) If pictures should be created. Default=True.

        Attributes:
            - _name     = (str) The name of this action
            - _log      = (customLogging.custom_logger obj) The log for all the messages
            - _roll     = (rollFunctions.roll obj) The rolling functions
            - _pict     = (bool) If the pictures should be created
            - cost      = (str) The cost of this action. One of [regular, bonus, movement, reaction]
            - target    = (list of str) The possible targets of this action. Each element is in [self, ally, enemy]
            - _handle   = (str) How this action will be handled. One of [attack, spell, movement, auto, contest, special]

            - _cache    = (dict) The cache of all attack obj or spell obj used by this action
                - Key                       | Value
                - {name of attack or spell} | (attack obj or spell obj) The obj of this attack or spell
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
        self._pict = bool(do_pict)
        if not isinstance(in_json, str):
            raise TypeError('arg in_json must be a str')
        self._cache = {}

        self._log.debugall(f'attempting to create action {name} in {in_json}')
        with open(in_json, 'r') as read_file:
            data = _json.load(read_file)
            if not isinstance(data, dict):
                raise TypeError(f'data in {in_json} must be a dict')
            for i_category, i_action_dict in data.items():
                if not isinstance(i_action_dict, dict):
                    raise TypeError(f'value for key {i_category} in {in_json} was not a dict')
                for i_name, i_dict in i_action_dict.items():
                    if (name==i_name):
                        if (i_dict['type'] not in ['regular', 'bonus', 'movement', 'reaction', 'special']):
                            raise TypeError(f'value for key type in {name} in {in_json} must be in ["regular", "bonus", "movement", "reaction", "special"]')
                        self.cost = i_dict['type']
                        if ('targets' in i_dict):
                            for i in i_dict['targets']:
                                if (i not in ['self', 'ally', 'enemy']):
                                    raise ValueError(f'value for key targets in {name} in {in_json} must have its elements in ["self", "ally", "enemy"]')
                            self.target = i_dict['targets']
                        else:
                            self.target = []
                        if (i_dict['handle'] not in ['attack', 'spell', 'movement', 'auto', 'contest', 'special']):
                            raise ValueError(f'value for key handle in {name} in {in_json} must have its elements in ["attack", "spell", "movement", "auto", "contest", "special"]')
                        self._handle = i_dict['handle']
                        return
        raise ValueError(f'could not find action {name} in {in_json}')
    # End __init__

    def _log_attack_picture(self, source, target, in_attack, crit, attack_roll, hit, damage, actual_damage, hp):
        """Have the source character do specified attack on target character

        Args:
            - source        = (str) The name of the attacker
            - target        = (str) The name of the attacker
            - in_attack     = (str) The name of the attack
            - crit          = (str) If the attack was a crit
            - attack_roll   = (int) The result of the attack roll
            - hit           = (bool) If the attack was a hit
            - damage        = (dict) The damage of the attack
            - actual_damage = (int) The actual damage the target took
            - hp            = (int) The HP of the target after the attack

        Returns:
            No return value
        """
        str_list = ['' for i in range(5)]
        # Source
        largest_spacing = max(len(source), len(in_attack))
        str_list[0] += '='*(largest_spacing + 1)
        str_list[1] += f'{source:^{largest_spacing}} '
        str_list[2] += f'{" "*largest_spacing} '
        str_list[3] += f'{in_attack:^{largest_spacing}} '
        str_list[4] += '='*(largest_spacing + 1)

        # Hit
        str_list[0] += '='*11
        str_list[1] += ' '*11
        str_list[2] += f'{("CRIT HIT" if (crit=="hit") else ("CRIT MISS" if (crit=="miss") else f"{attack_roll} to hit")):^10} '
        str_list[3] += ' '*11
        str_list[4] += '='*11

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
                if (line_count==1):
                    second_str = f'{i_v} {i_k}'
                if (line_count==2):
                    third_str = f'{i_v} {i_k}'
                    break
                line_count += 1
            largest_spacing = max(len(first_str), len(second_str), len(third_str))
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

        # No damage
        else:
            str_list[0] += '======'
            str_list[1] += 'X     '
            str_list[2] += 'X     '
            str_list[3] += 'X     '
            str_list[4] += '======'

        # Target
        largest_spacing = max(len(target), 6)
        str_list[0] += '='*largest_spacing
        str_list[1] += f'{target:^{largest_spacing}}'
        str_list[2] += f'{("-" + str(actual_damage)):^{largest_spacing}}'
        str_list[3] += f'{(str(hp) + " HP"):^{largest_spacing}}'
        str_list[4] += '='*largest_spacing

        # Log
        for i in str_list:
            self._log.picture(i)
    # End _log_attack_picture method

    def _check_targets(self, source, target_list):
        """Will look at all the targets and see if they are valid.

        Args:
            - source        = (combatCharacter obj) The source of the action
            - target_list   = (list of combatCharacter obj) All of the targets to check

        Returns:
            (list of combatCharacter obj) All of the targets that were valid
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target_list, list):
            raise TypeError('arg target_list must be a list')
        
        return_val = []
        for i_target in target_list:
            if not isinstance(i_target, _combatCharacter):
                self._log.error('arg target_list had an element that was not a combatCharacter obj')
                continue
            source_on_good = source.team in ['pc', 'ally']

            if (self.target == ['self']):
                if (i_target._name == source._name):
                    return_val.append(i_target)
                else:
                    self._log.warning(f'{source._name} must target self; cannot target {i_target._name}')

            elif (self.target == ['enemy']):
                if source_on_good:
                    if (i_target.team == 'enemy'):
                        return_val.append(i_target)
                    else:
                        self._log.warning(f'{source._name} must target an enemy; cannot target {i_target._name}')
                else:
                    if (i_target.team in ['pc', 'ally']):
                        return_val.append(i_target)
                    else:
                        self._log.warning(f'{source._name} must target an enemy; cannot target {i_target._name}')

            elif (self.target == ['ally']):
                if source_on_good:
                    if ((i_target.team in ['pc', 'ally']) and (i_target._name != source._name)):
                        return_val.append(i_target)
                    else:
                        self._log.warning(f'{source._name} must target an ally excluding self; cannot target {i_target._name}')
                else:
                    if ((i_target.team == 'enemy') and (i_target._name != source._name)):
                        return_val.append(i_target)
                    else:
                        self._log.warning(f'{source._name} must target an ally excluding self; cannot target {i_target._name}')

            elif ((self.target == ['self', 'ally']) or (self.target == ['ally', 'self'])):
                if source_on_good:
                    if (i_target.team in ['pc', 'ally']):
                        return_val.append(i_target)
                    else:
                        self._log.warning(f'{source._name} must target an ally; cannot target {i_target._name}')
                else:
                    if (i_target.team == 'enemy'):
                        return_val.append(i_target)
                    else:
                        self._log.warning(f'{source._name} must target an ally; cannot target {i_target._name}')

            else:
                return_val.append(i_target)
        return return_val
    # End _check_targets method

    def do_action(self, source, target=[], additional={}):
        """Will do this action.

        Args:
            - source        = (combatCharacter obj) The character that is doing the action
            - target        = (list of combatCharacter obj, optional) The characters that are being targeted by the action for attack or spell. Default=[]
            - additional    = (dict) Any additional args that you need to provide to the action.
                - Key       | Value
                - attack    | (str) The name of the attack to use. ONLY needed for an attack action.
                - upcast    | (int, optional) The spell slot to use for the spell if wanting to upcast. ONLY needed for a spell action. Will use lowest available level if not provided.
                - distance  | (int or float) The distance to travel. ONLY needed for a movement action.

        Returns: (dict) The results of the action
            - Key                   | Value
            - {name of the target}  | (str) What happened to the character
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list of combatCharacter obj')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')

        true_targets = self._check_targets(source=source, target_list=target)

        # Attack branch
        if (self._handle == 'attack'):
            if not true_targets:
                self._log.warning(f'{source._name} did not have any valid targets in arg target for an attack')
                return {}
            # Handle special attacks
            if (self._name == 'martial_arts'):
                true_attack = 'unarmed'
            else:
                if ('attack' not in additional):
                    raise ValueError('arg additional must have a key "attack" for an attack action')
                true_attack = additional['attack']
            return self._do_attack(source=source, target=true_targets, in_attack=true_attack, additional=additional)
        # End attack branch

        # Spell branch
        elif (self._handle == 'spell'):
            if not true_targets:
                self._log.warning(f'{source._name} did not have any valid targets in arg target for spell {self._name}')
                return {}
            # Casting of spells will have the action start with cast_
            if (self._name.startswith('cast_')):
                spell_name = self._name[5:]
                split_list = spell_name.split(' ', maxsplit=1)
                if (len(split_list) == 2):
                    spell_name = split_list[0]
                self._log.action(f'{source._name} casts spell {spell_name}')
            # Casting of channel divinity will start with cd_
            elif (self._name.startswith('cd_')):
                spell_name = self._name[3:]
                self._log.action(f'{source._name} uses Channel Divinity {spell_name}')
                source.char_resources.channel_div -= 1
            # Must be some spell-like feature
            else:
                spell_name = self._name
                self._log.action(f'{source._name} uses spell-like feature {spell_name}')
            return self._do_spell(source=source, target=true_targets, in_spell=spell_name, additional=additional)
        # End spell branch

        # Movement branch
        elif (self._handle == 'movement'):
            if ('distance' not in additional):
                raise ValueError('arg additional must have key "distance" for a movement action')
            return self._do_movement(source=source, distance=additional['distance'], additional=additional)

        # Auto branch
        elif (self._handle == 'auto'):
            return self._do_auto(source=source, additional=additional)

        # Contest branch
        elif (self._handle == 'contest'):
            return self._do_contest(source=source, target=true_targets, additional=additional)

        # Special branch; catch all
        else:
            return self._do_special(source=source, target=true_targets, additional=additional)
    # End do_action method

    def _do_attack(self, source, target, in_attack, additional={}):
        """Handling of an attack action

        Args:
            - source        = (combatCharacter obj) The character that is attacking
            - target        = (list of combatCharacter obj) The characters that are being attacked. Will iterate through the targets for multiattacks. Otherwise will only attack the first.
            - in_attack     = (str) The name of the attack
            - additional    = (dict, optional) Any additional args for the attack. Default={}

        Returns: (dict) The results of the attack
            - Key                   | Value
            - {name of the target}  | (str) The new HP of the target
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list of combatCharacter obj')
        if not isinstance(in_attack, str):
            raise TypeError('arg in_attack must be a str')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')

        # Override attacks
        if (('monk' in source.char_stats.class_level) and (in_attack=='unarmed')):
            for i_attack in source.char_attacks:
                if ('unarmed' in i_attack):
                    in_attack = i_attack
                    break
        elif ('shillelagh' in source.char_conditions):
            if ('club' in in_attack):
                in_attack = 'club_shillelagh'
            elif ('quarterstaff' in in_attack):
                in_attack = 'quarterstaff_shillelagh'

        # Check this character has this attack
        if (in_attack not in source.char_attacks):
            raise ValueError(f'{source._name} does not have an attack called {in_attack}')
        
        # Parse attack name for json
        att_json = ''
        split_list = in_attack.split(' ', maxsplit=1)
        if (len(split_list) == 2):
            in_attack = split_list[0]
            att_json = split_list[1]

        # Create attack obj
        if (in_attack in self._cache):
            attack_obj = self._cache[in_attack]
            if not isinstance(attack_obj, _attack):
                raise TypeError(f'key "{in_attack}" had its value not an attack obj')
        else:
            if att_json:
                attack_obj = _attack(name=in_attack, in_log=self._log, in_roll=self._roll, in_json=att_json)
            else:
                attack_obj = _attack(name=in_attack, in_log=self._log, in_roll=self._roll)
            self._cache[in_attack] = attack_obj

        # Get attack count
        attack_count = 1*attack_obj._multi
        if (self._name == 'extra_attack'):
            attack_count = 2*attack_count
        elif (self._name == 'extra_attack_3'):
            attack_count = 3*attack_count
        elif (self._name == 'extra_attack_4'):
            attack_count = 4*attack_count

        # Check if offhand
        if ('offhand' in self._name):
            additional.update({'offhand':True})

        # Iterate through targets
        return_val = {}
        target_len = len(target)
        for i in range(attack_count):
            this_target = target[i % target_len]
            if not isinstance(this_target, _combatCharacter):
                raise TypeError('each element in arg target must be a combatCharacter obj')
            self._log.action(f'{source._name} attacks {this_target._name} with {attack_obj.name}')
            adv = 0

            # Get target reaction
            if ('warding_flare' in this_target.char_resources.miscellaneous):
                if (
                    (this_target.char_resources.reaction > 0) and
                    (this_target.char_resources.miscellaneous['warding_flare'] > 0)
                ):
                    self._log.action(f'{this_target._name} is using their reaction Warding Flare to impose disadvantage')
                    adv -= 1
                    this_target.char_resources.miscellaneous['warding_flare'] -= 1
                    this_target.char_resources.add_resource({'reaction':-1})

            # Attack roll
            roll_result = attack_obj.roll_hit(source=source, target=this_target, pass_arg=additional, adv=adv)
            if (
                (roll_result[0] == 'miss') or
                (roll_result[1] < this_target.char_stats.ac)
            ):
                self._log.hit(f'{source._name} misses {this_target._name}')
                hit = False
            else:
                self._log.hit(f'{source._name} hits {this_target._name}')
                hit = True

            # Damage roll
            if hit:
                damage = attack_obj.roll_damage(source=source, target=this_target, crit=(roll_result[0]=='hit'), adv=adv, pass_arg=additional)
                (actual_damage, new_hp) = this_target.take_damage(damage=damage, was_crit=(roll_result[0]=='hit'))
            else:
                damage = {}
                actual_damage = 0
                new_hp = this_target.char_resources.hp

            # Picture
            if self._pict:
                self._log_attack_picture(
                    source=source._name, target=this_target._name, in_attack=attack_obj.name,
                    crit=roll_result[0], attack_roll=roll_result[1], hit=hit,
                    damage=damage, actual_damage=actual_damage, hp=new_hp
                )

            return_val.update({f'{this_target._name}': f'now has {new_hp} HP'})

        return return_val
    # End _do_attack method

    def _do_spell(self, source, target, in_spell, additional={}):
        """Handling of a spell action

        Args:
            - source        = (combatCharacter obj) The character that is casting the spell
            - target        = (list of combatCharacter obj) The characters that are being targeted by the spell
            - in_spell      = (str) The spell that is being cast
            - additional    = (dict, optional) Any additional args that you need to provide to the spell. Default={}

        Returns: (dict) The results of the spell
            - Key                   | Value
            - {name of the target}  | (str) What happened to the target
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a combatCharacter obj')
        if not isinstance(in_spell, str):
            raise TypeError('arg in_spell must be a str')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')

        # Parse spell name for json
        spell_json = ''
        split_list = in_spell.split(' ', maxsplit=1)
        if (len(split_list) == 2):
            in_spell = split_list[0]
            spell_json = split_list[1]

        # Create spell obj
        if (in_spell in self._cache):
            spell_obj = self._cache[in_spell]
            if not isinstance(spell_obj, _spell):
                raise TypeError(f'key "{in_spell}" had its value not a spell obj')
        else:
            if spell_json:
                spell_obj = _spell(name=in_spell, in_log=self._log, in_roll=self._roll, in_json=spell_json, spell_picture=self._pict)
            else:
                spell_obj = _spell(name=in_spell, in_log=self._log, in_roll=self._roll, spell_picture=self._pict)
            self._cache[in_spell] = spell_obj

        # If not a cantrip, check for spell slots
        if (spell_obj.level > 0):
            next_slot = source.char_resources.get_next_available_slot(spell_obj.level)
            if (next_slot == 0):
                self._log.error(f'{source._name} has no spell slots at level {spell_obj.level} or higher to cast {spell_obj._name}')
                return {}
            if ('upcast' in additional):
                if not isinstance(additional['upcast'], int):
                    raise ValueError('arg additional["upcast"] must be an int')
                upcast = additional['upcast']
            else:
                upcast = 0
        else:
            next_slot = 0
            upcast = 0
        return spell_obj.do_spell(source=source, target=target, upcast=max(next_slot, upcast), pass_arg=additional)
    # End _do_spell method

    def _do_movement(self, source, distance, additional={}):
        """Handling of a movement action

        Args:
            - source        = (combatCharacter obj) The character that is moving
            - distance      = (int) How far the character will try to move. Must be > 0.
            - additional    = (dict, optional) Any additional args that you need to provide to the spell. Default={}

        Returns: (dict) The results of the spell
            - Key                   | Value
            - {name of the source}  | (str) Where the source is now located
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(distance, (int, float)):
            raise TypeError('arg distance must be an int or a float')
        if (distance <= 0):
            raise ValueError('arg distance must be > 0')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')
        
        divisor = 2 if ('difficult' in additional) else 1
        if (self._name in ['climb', 'crawl', 'swim']):
            divisor += 1
        actual_dist = round(distance / divisor, 2)
        self._log.action(f'{source._name} moves {actual_dist} feet ({5*(actual_dist//5)} squares)')
        return {f'{source._name}': f'{actual_dist} feet to LOCATION'}
    # End _do_movement method

    def _do_auto(self, source, additional={}):
        """Handling of a auto action (certain actions that target self)

        Args:
            - source        = (combatCharacter obj) The character that is doing the auto action
            - additional    = (dict, optional) Any additional args that you need to provide to the action. Default={}

        Returns: (dict) The results of the action
            - Key                   | Value
            - {name of the source}  | (str) Any changes to the source
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')

        def _build_ret(in_str):
            return {f'{source._name}': in_str}
        # End _build_ret inner function

        if (self._name == 'long_rest'):
            source.char_resources.long_rest()
            return _build_ret('long rest')
        if (self._name == 'short_rest'):
            source.char_resources.short_rest()
            return _build_ret('short rest')
        if (self._name == 'death_save'):
            return _build_ret(f'death saves: {source.char_resources.do_death_save()}')
        if (self._name == 'dodge'):
            source.add_condition('dodge', '1 sont')
            return _build_ret('dodging attacks and spells')
        if (self._name == 'wild_shape'):
            if ('wild_shape' not in additional):
                raise ValueError('arg additional must have key "wild_shape" for auto action wild_shape')
            source.add_condition('wild_shape', f'{source.char_stats.class_level["druid"]//2} hour', additional['wild_shape'])
            return _build_ret(f'wild shape into {additional["wild_shape"]}')
        if (self._name == 'drop_wild_shape'):
            source.remove_condition('wild_shape')
            return _build_ret('dropped wild shape')

        raise Exception(f'could not find any code for auto action {self._name}')
    # End _do_auto method

    def _do_contest(self, source, target=[], additional={}):
        """Handling of a contest action

        Args:
            - source        = (combatCharacter obj) The character that is attempting the contest
            - target        = (list of combatCharacter obj, optional) The character(s) that are opposing the source, if needed. Default=[]
            - additional    = (dict, optional) Any additional args that you need to provide to the action. Default={}

        Returns: (dict) The results of the contest
            - Key                   | Value
            - {name of the source}  | (str) Any changes to the source
            - {name of the target}  | (str) Any changes to the target(s)
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list of combatCharacter obj')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')
        return {}
    # End _do_contest method

    def _do_special(self, source, target=[], additional={}):
        """Handling of a special action

        Args:
            - source        = (combatCharacter obj) The character that is doing the special action
            - target        = (list of combatCharacter obj, optional) The character(s) that are the targets of the action, if needed. Default=[]
            - additional    = (dict, optional) Any additional args that you need to provide to the action. Default={}

        Returns: (dict) The results of the action
            - Key                   | Value
            - {name of the target}  | (str) Any changes to the target
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, list):
            raise TypeError('arg target must be a list of combatCharacter obj')
        if not isinstance(additional, dict):
            raise TypeError('arg additional must be a dict')

        # Actions that have a singular target, will use only the first character in the list
        try:
            single_target = target[0]
        except:
            raise ValueError(f'{self._name} must have a target')
        if not isinstance(single_target, _combatCharacter):
            raise TypeError('each element in arg target must be a combatCharacter obj')

        if (self._name == 'stabilize'):
            single_target.add_condition('stabilized', 'indefinite')
            return {f'{single_target._name}': 'now stabilized'}
        if (self._name == 'bardic_inspiration'):
            level = source.char_stats.class_level['bard']
            dice = '1d12' if (level>=15) else ('1d10' if (level>=10) else ('1d8' if (level>=5) else '1d6'))
            single_target.add_condition(name='bardic_inspiration', duration='10 minute', prop=dice)
            return {f'{single_target._name}': f'got {dice} bardic inspiration'}

        raise Exception(f'could not find any code for special action {self._name}')
    # End _do_special method
# End action class

# eof