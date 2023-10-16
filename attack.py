# description:  Contains the attack class
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20231016

"""The attack class

Classes:
    attack
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import json as _json
from rollFunctions import roll as _roll
import customLogging as _clog
from combatCharacter import combatCharacter as _combatCharacter

################################################################################################################################
#=========================================================== SET UP ===========================================================
################################################################################################################################

ABILITIES = ['str', 'dex', 'con', 'int', 'wis', 'cha']
AUTO_SUCCESS = 100
AUTO_FAIL = -100

################################################################################################################################
#====================================================== CUSTOM FUNCTIONS ======================================================
################################################################################################################################

#def custom_hit_conditons(attack, source, target, pass_arg={}):
#    """Custom hit conditions. See attack._hit_conditions method.
#    Create an if-branch for each custom attack.
#
#    Args:
#        - attack    = (str) The name of the attack
#        - source    = (combatCharacter obj) The character doing the attack
#        - target    = (combatCharacter obj) The target of the attack
#        - pass_arg  = (dict, optional) Any additional information that needs to be check. Default={}
#
#    Returns: (dict) What should be modified to the roll
#        - Key   | Value
#        - adv   | (int) If advantage or disadvantage should be given. A postive number means advantage, a negative number means disadvantage
#        - mod   | (int) Any modifiers to the roll
#    """
#    if not isinstance(attack, str):
#        raise TypeError
#    if not isinstance(source, combatCharacter):
#        raise TypeError('arg source must be a combatCharacter obj')
#    if not isinstance(target, combatCharacter):
#        raise TypeError('arg target must be a combatCharacter obj')
#    if not isinstance(pass_arg, dict):
#        raise TypeError('arg pass_arg must be a dict')
#
#    return_val = {'adv':0, 'mod':0}
#
#    # Create an if-branch for each custom attack below; the example branch can be removed/overwritten
#    if attack == 'custom_attack':
#        log.debugall('custom_attack grants advantage')
#        return_val['adv'] += 1
#        return return_val
#    # End where the custom attack code should go
#
#    log.debug(f'could not find any code for custom attack {attack}')
#
#    # Any additional code because of custom conditions
#    if 'unstoppable' in target.char_conditions:
#        log.conditn(f'{target._name} has unstoppable condition preventing damage')
#        target.char_conditions['unstoppable'].effect_on_oct(target)
#        return_val['mod'] -= AUTO_FAIL
#    # End where custom condition code goes
#
#    return return_val
## End custom_hit_conditions function
#
#def custom_conditional_damage(attack, source, target, crit=False, pass_arg={}):
#    """Custom damage conditions. See attack._conditional_damage method.
#    Create an if-branch for each custom attack.
#
#    Args:
#        - attack    = (str) The name of the attack
#        - source    = (combatCharacter obj) The character doing the attack
#        - target    = (combatCharacter obj) The target of the attack if needed
#        - crit      = (bool, optional) If the attack was a critical hit. Default=False.
#        - pass_arg  = (dict, optional) Any additional information that needs to be check. Default={}
#
#    Returns:
#        (str) In damage string in #d#+# {type} format. E.g. 2d4+3 force. See attack._comprehend_damage_str method.
#    """
#    if not isinstance(attack, str):
#        raise TypeError
#    if not isinstance(source, combatCharacter):
#        raise TypeError('arg source must be a combatCharacter obj')
#    if not isinstance(target, combatCharacter):
#        raise TypeError('arg target must be a combatCharacter obj')
#    if not isinstance(pass_arg, dict):
#        raise TypeError('arg pass_arg must be a dict')
#
#    return_val = ''
#
#    # Create an if-branch for each custom attack below; the example branch can be removed/overwritten
#    if attack == 'custom_attack':
#        log.debugall('custom_attack adds fire damage')
#        return '1d4+1 fire'
#
#    # End where the custom code should go
#
#    log.debug(f'could not find any code for custom attack {attack}')
#    return return_val
## End custom_conditional_damage fuction

################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class attack(object):
    """Logic for performing an attack.

    Args:
        - name          = (str) Name of the attack
        - in_log        = (customLogging.custom_logger obj) The log for all messages
        - in_roll       = (rollFunctions.roll obj) The functions for all rolling
        - in_json       = (str, optional) The path of the json where the attack is. Default=attacks.json.

    Methods:
        - _comprehend_damage_str    :parse a damage string

        - _hit_conditions           :check conditions of character to modify hit
        - _hit_proficiency          :check proficiencies of character to see if they can add their proficiency modifier
        - roll_hit                  :have the attack roll to hit

        - _conditional_damage       :get damage that only happens given certain conditions
        - _additional_damage        :get additional damage that matches type
        - roll_damage               :have the attack roll for damage
    """
    def __init__(self, name, in_log, in_roll, in_json='attacks.json'):
        """Init for attack

        Args:
            - name          = (str) Name of the attack
            - in_log        = (customLogging.custom_logger obj) The log for all messages
            - in_roll       = (rollFunctions.roll obj) The function for all rolling
            - in_json       = (str, optional) The path of the json where the attack is. Default=attacks.json.

        Attributes:
            - name          = (str) The name of the attack
            - _log          = (customLogging.custom_logger obj) The log for all the messages
            - _roll         = (rollFunctions.roll obj) The obj containing all roll functions
            - _custom       = (bool) If this attack was a custom attack

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
        if not isinstance(in_log, _clog.custom_logger):
            raise TypeError('arg in_log must be a customLogging.custom_logger')
        self._log = in_log
        if not isinstance(in_roll, _roll):
            raise TypeError('arg in_roll must be a rollFunctions.roll obj')
        self._roll = in_roll
        if not isinstance(in_json, str):
            raise TypeError('arg in_json must be a str')
        self._custom = in_json != 'attacks.json'

        self._log.debugall(f'attempting to create attack {name} from {in_json}')
        with open(in_json, 'r') as read_file:
            data = _json.load(read_file)
            if not isinstance(data, list):
                raise TypeError(f'data in {in_json} must be a list')
            for i_attack in data:
                if not isinstance(i_attack, dict):
                    raise TypeError(f'values in data list in {in_json} must be a dict')
                if (name==i_attack['name']):
                    self._ability = i_attack['ability']
                    self._damage = []
                    for i in i_attack['damagedice']:
                        parse_list = i.split(' ')
                        parse_tuple = self._roll._parse_d(parse_list[0])
                        self._damage.append({
                            'num':parse_tuple[1], 'fac':parse_tuple[0], 'mod':parse_tuple[2],
                            'abl':parse_list[1] if parse_list[1] in ABILITIES else '',
                            'typ':parse_list[-1]
                        })
                    self._prof = set(i_attack['type'])
                    self._hitmod = i_attack['hitmod']
                    self._multi = i_attack['multi']
                    if ('properties' in i_attack):
                        self._properties = i_attack['properties']
                    else:
                        self._properties = []
                    break
            else:
                raise ValueError(f'could not find attack {name} in {in_json}')

        self._last_used = ''
    # End __init__

    def _comprehend_damage_str(self, in_str):
        """Parse a damage string and get the relevant information

        Args:
            - in_str = (str) The string to comprehend. In format #d#+# {ability} {type}. See _parse_d function. E.g. 1d8+1 str slashing

        Returns: (dict) The information of that string
            - Key   | Value
            - num   | (int) The number of dice to roll
            - fac   | (int) The number of faces on an individual die
            - mod   | (int) The flat modifier to add to the damage
            - abl   | (str) The ability modifier of the attacker to add to the damage. One of ['', str, dex, con, int, wis, cha].
            - typ   | (str) The type of damage
        """
        if not isinstance(in_str, str):
            raise TypeError('arg in_str must be a str')

        str_split = in_str.split(' ')
        parse_tuple = self._roll._parse_d(str_split[0])
        if (len(str_split)==3):
            if (str_split[1] not in ABILITIES):
                raise ValueError(f'damage string had {str_split[1]} which is not an ability')
            mod_ability = str_split[1]
            damage_type = str_split[2]
        else:
            mod_ability = ''
            damage_type = str_split[1]

        return {
            'num': parse_tuple[1],
            'fac': parse_tuple[0],
            'mod': parse_tuple[2],
            'abl': mod_ability,
            'typ': damage_type
        }
    # End _comprehend_damage_str method

    ################################################################
    #========================= ATTACK HIT =========================
    ################################################################

    def _hit_conditions(self, source, target, pass_arg={}):
        """Will look at the current conditions of the attacking character, and see if the hit should be modified in any way. Will also check the conditions of the target as well as any
        environmental conditions.

        Args:
            - source    = (combatCharacter obj) The character doing the attack
            - target    = (combatCharacter obj) The target of the attack
            - pass_arg  = (dict, optional) Any additional information that needs to be check. Default=None

        Returns: (dict) What should be modified to the roll
            - Key   | Value
            - adv   | (int) If advantage or disadvantage should be given. Advantage is > 0, disadvantage is < 0.
            - mod   | (int) Any modifiers to the roll
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, _combatCharacter):
            raise TypeError('arg target must be a combatCharacter obj')
        if not isinstance(pass_arg, dict):
            raise TypeError('arg pass_arg must be a dict')

        def _overlap(set_1, set_2):
            if not isinstance(set_1, set):
                raise TypeError('arg set_1 must be a set')
            if not isinstance(set_2, set):
                raise TypeError('arg set_2 must be a set')
            return not set_1.isdisjoint(set_2)
        # End _overlap inner function

        return_val = {'adv': 0, 'mod': 0}

        # Check custom hit conditions
#        if self._custom:
#            return_val = custom_hit_conditons(attack=self.name, source=source, target=target, pass_arg=pass_arg)

        # Check attacker conditions
        if _overlap(set(source.char_conditions), {'blinded', 'frightened', 'prone', 'restrained'}):
            self._log.hit(f'{source._name} has disadvantage because of a condition')
            return_val['adv'] += -1
        if _overlap(set(source.char_conditions), {'invisible'}):
            self._log.hit(f'{source._name} has advantage because of a condition')
            return_val['adv'] += 1

        # Check target conditions
        if _overlap(set(target.char_conditions), {'invisible'}):
            self._log.hit(f'{target._name} grants disadvantage because of a condition')
            return_val['adv'] -= 1
        if _overlap(set(target.char_conditions), {'prone'}):
            if ('in5ft' in pass_arg):
                self._log.hit(f'{target._name} grants advantage because they are prone and was hit within 5 ft')
                return_val['adv'] += 1
            else:
                self._log.hit(f'{target._name} grants disadvantage because they are prone and was not hit within 5 ft')
                return_val['adv'] -= 1
        if ('dodge' in target.char_conditions):
            self._log.hit(f'{target._name} grants disadvantage because they are dodging')
            return_val['adv'] -= 1
        if _overlap(set(target.char_conditions), {'blinded', 'paralyzed', 'petrified', 'restrained', 'stunned', 'unconscious'}):
            self._log.hit(f'{target._name} grants advantage because of a condition')
            return_val['adv'] += 1

        # Check for bardic inspiration
        if ('bardic_inspiration' in source.char_conditions):
            bi_roll = self._roll.roll_d_str(source.char_conditions['bardic_inspiration']._properties)
            self._log.action(f'{source._name} is using their bardic inspiration and rolled a {bi_roll}')
            return_val['mod'] += bi_roll
            source.remove_condition('bardic_inspiration')
        
        # Handle ability modifier
        if (
            ('finesse' in self._properties) or
            (('monk_weapon' in self._properties) and ('monk' in source.char_stats.class_level))
        ):
            use_ability = 'dex' if (source.char_stats.dex > source.char_stats.str) else 'str'
            self._last_used = use_ability
            self._log.hit(f'{source._name} is using {use_ability} for {self.name}')
            ability_mod = source.char_stats.get_mod(use_ability)
        else:
            ability_mod = source.char_stats.get_mod(self._ability)
        self._log.debugall(f'{source._name} ability mod={ability_mod}')
        return_val['mod'] += ability_mod

        # Handle properties
        if (('simple_ranged_weapon' in self._prof) or ('martial_ranged_weapon' in self._prof)):
            if ('fighting_style' in source.char_stats.property):
                if (source.char_stats.property['fighting_style']=='archery'):
                    self._log.debug(f'{source._name} gets a +2 due to archery')
                    return_val['mod'] += 2

        return return_val
    # End _hit_conditons method

    def _hit_proficiency(self, character):
        """Will check the proficiencies of the attacker and see if they have proficiencies with this attack

        Args:
            - character = (combatCharacter obj) The attacking character

        Returns:
            (int) The modifier to the roll
        """
        if not isinstance(character, _combatCharacter):
            raise TypeError('arg character must be a combatCharacter obj')
        return_val = character.char_stats.prof
        if (self._prof=={"all"}):
            self._log.debugall(f'characters are always proficient with {self.name}; mod={return_val}')
            return return_val
        else:
            is_prof = not self._prof.isdisjoint(set(character.char_stats.tools))
            if is_prof:
                self._log.debug(f'{character._name} is proficient with {self.name}, mod={return_val}')
                return return_val
            else:
                self._log.hit(f'{character._name} is not proficient with {self.name}')
                return 0
    # End _hit_proficiency method

    def roll_hit(self, source, target, pass_arg={}, adv=0):
        """Will do an attack roll with this attack

        Args:
            - source    = (combatCharacter obj) The character doing this attack
            - target    = (combatCharacter obj) The target of the attack
            - pass_arg  = (dict, optional) Any additional arguments to pass to the hit. Default={}
            - adv       = (int, optional) If the attack roll has advantage or disadvantage. Advantage is 1, disadvantage is -1. Default=0

        Returns: (tuple)
            - (str) If the hit was a critical hit/miss. One of [norm, hit, miss]
            - (int) The total rolled for the attack roll
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg character must be a combatCharacter obj')
        if not isinstance(target, _combatCharacter):
            raise TypeError('arg character must be a combatCharacter obj')
        if not isinstance(pass_arg, dict):
            raise TypeError('arg pass_arg must be a dict')
        if not isinstance(adv, int):
            raise TypeError('arg adv must be an int')

        total_mod = 0
        hit_mod = self._hit_conditions(source=source, target=target, pass_arg=pass_arg)
        total_mod += hit_mod['mod']

        # Roll d20
        roll = self._roll.roll_20(adv + hit_mod['adv'])
        if (roll == 1):
            self._log.hit(f'{source._name} using {self.name} rolled a critical miss!')
            return ('miss', 0)
        crit_threshold = 20
        if ('crit_threshold' in source.char_stats.property):
            self._log.debug(f'{source._name} crits on {source.char_stats.property} or higher')
            crit_threshold = source.char_stats.property['crit_threshold']
        if (roll >= crit_threshold):
            self._log.hit(f'{source._name} using {self.name} rolled a critical hit!')
            return ('hit', 20)

        # Get total
        total_mod += self._hit_proficiency(character=source) + self._hitmod
        self._log.hit(f'{source._name} using {self.name} rolled a {roll}+{total_mod} to hit')
        return ('norm', roll + total_mod)
    # End roll_hit method

    ################################################################
    #======================== ATTACK DAMAGE ========================
    ################################################################

    def _conditional_damage(self, source, target, crit=False, pass_arg={}):
        """Will look at the current conditions of the attacker, and add any other sources of damage. Will also check the conditions of the target as well as any environmental conditions.
        Immunities, resistances, and vulnerabilities are handled by _combatCharacter.take_damage method.

        Args:
            - source    = (combatCharacter obj) The attacking character
            - target    = (combatCharacter obj) The character being attacked
            - crit      = (bool, optional) If the attack was a critical hit
            - pass_arg  = (dict, optional) Any additional information that needs to be checked. Default={}

        Returns:
            (list of str) Each list element must be in the #d#+# format
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, _combatCharacter):
            raise TypeError('arg target must be a combatCharacter obj')
        if not isinstance(pass_arg, dict):
            raise TypeError('arg pass_arg must be a dict')

        return_val = []

        # Get custom damage
#        if self._custom:
#            custom_str = custom_conditional_damage(attack=self.name, source=source, target=target, pass_arg=pass_arg)
#            if custom_str:
#                return_val.append(custom_str)

        if ('genies_wrath' in source.char_resources.miscellaneous):
            if (source.char_resources.miscellaneous['genies_wrath']):
                self._log.action(f'{source._name} is using genies wrath to increase damage')
                split_list = source.char_stats.property['patron'].split('_')
                if (split_list[-1]=='dao'):
                    genie_type = 'm_bludgeoning'
                elif (split_list[-1]=='djinni'):
                    genie_type = 'thunder'
                elif (split_list[-1]=='efreeti'):
                    genie_type = 'fire'
                elif (split_list[-1]=='marid'):
                    genie_type = 'cold'
                else:
                    raise ValueError(f'{source._name} has an invalid genie patron')
                return_val.append(f'0d0+{source.char_stats.prof} {genie_type}')
                source.char_resources.miscellaneous['genies_wrath'] = 0

        return return_val
    # End _conditional_damage method

    def _additional_damage(self, source, target, adv, pass_arg={}):
        """Adds additional damage that matches the type of the attack

        Args:
            - source    = (combatCharacter obj) The attacking character
            - target    = (combatCharacter obj) The character being attacked
            - adv       = (int) If the attack had advantage or disadvantage. Advantage if > 0, disadvantage < 0.
            - pass_arg  = (dict) Any additional args that needs to be passed

        Returns:
            (int) The damage to add
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, _combatCharacter):
            raise TypeError('arg target must be a combatCharacter obj')
        if not isinstance(adv, int):
            raise TypeError('arg adv must be an int')
        if not isinstance(pass_arg, dict):
            raise TypeError('arg pass_arg must be a dict')
        
        return_val = 0

        # Sneak attack
        if source.char_resources.sneak_attack:
            if (('finesse' in self._properties) or ('simple_ranged_weapon' in self._prof) or ('martial_ranged_weapon' in self._prof)):
                if ((adv>0) or ('adj_enemy' in pass_arg)):
                    rogue_level = source.char_stats['rogue']
                    extra = self._roll.roll_d_str(f'{(rogue_level + 1) // 2}d6')
                    self._log.damage(f'{source._name} is using sneak attack to increase damage by {extra}')
                    source.char_resources.sneak_attack = 0
                    return_val += extra
                else:
                    self._log.debugall(f'{source._name} cannot use sneak attack because they dont have advantage or an enemy adjacent to target')
            else:
                self._log.debugall(f'{source._name} cannot use sneak attack on a weapon without finesse or not-ranged')

        return return_val
    # End _additional_damage method

    def roll_damage(self, source, target, crit=False, adv=0, pass_arg={}):
        """Will do a damage roll with this attack

        Args:
            - source    = (combatCharacter) The attacking character
            - target    = (combatCharacter) The targeted character
            - crit      = (bool, optional) If the attack was a critical hit
            - adv       = (int, optional) If the attack had advantage or disadvantage. Advantage if > 0, disadvantage < 0. Default=0
            - pass_arg  = (any, optional) Any additional information that needs to be checked. Default={}

        Returns:
            - (dict) All the damage of the attack, by type
                - Key               | Value
                - {type of damage}  | (int) Total value of damage of that type
        """
        if not isinstance(source, _combatCharacter):
            raise TypeError('arg source must be a combatCharacter obj')
        if not isinstance(target, _combatCharacter):
            raise TypeError('arg target must be a combatCharacter obj')
        if not isinstance(adv, int):
            raise TypeError('arg adv must be an int')
        if not isinstance(pass_arg, dict):
            raise TypeError('arg pass_arg must be a dict')

        damage_list = self._damage.copy()

        # Get conditional damage
        str_list = self._conditional_damage(source=source, target=target, crit=crit, pass_arg=pass_arg)
        self._log.debugall(f'cond_damage={str_list}')
        for i in str_list:
            damage_list.append(self._comprehend_damage_str(i))

        # Iterate through all damage
        return_val = {}
        for i_damage in damage_list:
            if (i_damage['typ'] not in return_val):
                return_val[i_damage['typ']] = 0

            roll = 0
            # Get additional damage
            roll += self._additional_damage(source=source, target=target, adv=adv, pass_arg=pass_arg)

            # Roll for damage
            roll += self._roll.roll_d(i_damage['fac'], (2 if crit else 1) * i_damage['num'])

            # Handle finesse and monk_weapon properties
            use_ability = i_damage['abl']
            if (bool(self._last_used) and (i_damage['abl'] in ['str', 'dex'])):
                self._log.debug(f'using {self._last_used} since {source._name} used it for the attack roll')
                use_ability = self._last_used

            # Get ability mod
            ability_mod = source.char_stats.get_mod(use_ability) if use_ability else 0
            if ('offhand' in pass_arg):
                self._log.debug(f'{source._name} is attacking with their offhand')
                ability_mod = min(ability_mod, 0)

            # Get total and add to dict
            self._log.debugall(f'type={i_damage["typ"]} roll={roll} mod={i_damage["mod"]} ability={ability_mod}')
            return_val[i_damage['typ']] += (roll + i_damage['mod'] + ability_mod)
        # End i_damage in damage_list for loop

        # Log damage
        printstr = f'{self.name} did'
        for i_key, i_value in return_val.items():
            printstr += f' {i_value} {i_key} +'
        self._log.damage(printstr[:-1] + 'damage')
        return return_val
    # End roll_damage method
# End attack class

# eof