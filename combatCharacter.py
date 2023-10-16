# description:  Contains the combatCharacter class
# author:       Taas, Rendale Mark
# created:      20230925
# last edited:  20231016

"""The combatCharacter class.

Classes:
    combatCharacter
        stats
        resources
        actionChooser
"""

################################################################################################################################
#=========================================================== IMPORTS ===========================================================
################################################################################################################################

import json as _json
import random as _random
import math as _math
from rollFunctions import roll as _roll
import customLogging as _clog

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
TIME_UNITS = {'round':6, 'second':1, 'minute':60, 'hour':3600, 'day':86400, 'sont':3, 'eont':3}
AUTO_SUCCESS = 100
AUTO_FAIL = -100


################################################################################################################################
#====================================================== CUSTOM FUNCTIONS ======================================================
################################################################################################################################

#def custom_condition(cond, cond_type, character, pass_arg=None):
#    """The effect of a custom condition. You should create an if-branch for each condition. See methods condition._effect_on_gain,
#    condition._effect_on_sot, condition._effect_on_eot, condition._effect_on_loss, and condition.effect_on_oct.
#
#    Args:
#        - cond      = (condition obj) The object of the condition
#        - cond_type = (str) The time when the condition is checked. One of [gain, sot, eot, loss, oct]
#        - character = (combatCharacter obj) The character this condition is afflicting
#        - pass_arg  = (any, optional) Any additional args you need to pass to the condition code
#    """
#    if not isinstance(cond, condition):
#        raise TypeError('arg cond must be a condition obj')
#    if (cond_type not in ['gain', 'sot', 'eot', 'loss', 'oct']):
#        raise ValueError("arg cond_type must be one of the following ['gain', 'sot', 'eot', 'loss', 'oct']")
#    if not isinstance(character, combatCharacter):
#        raise TypeError('arg character must be a combatCharacter obj')
#
#    # Create an if-branch for each custom condition below. It should go in the section when the effect wil happen.
#    # The example branch can be removed/overwritten
#    if (cond_type=='gain'):
#        raise ValueError(f'no code for {cond.name} that triggers on gain exists')
#
#    elif (cond_type=='sot'):
#        raise ValueError(f'no code for {cond.name} that triggers on start of turn exists')
#
#    elif (cond_type=='eot'):
#        raise ValueError(f'no code for {cond.name} that triggers on end of turn exists')
#
#    elif (cond_type=='loss'):
#        raise ValueError(f'no code for {cond.name} that triggers on loss exists')
#
#    else:
#        if cond.name=='unstoppable':
#            cond._properties['blocks_left'] -= 1
#            if cond._properties['blocks_left'] <= 0:
#                cond.valid = False
#            return
#        raise ValueError(f'no code for {cond.name} that triggers on other characters turn exists')
## End custom_condition function

################################################################################################################################
#=========================================================== CLASSES ===========================================================
################################################################################################################################

class combatCharacter(object):
    """Character that is within the combat.

    Args:
        - name      = (str) The name of this character
        - in_log    = (customLogging.custom_logger obj) The log to use for all messages
        - team      = (str) The team the character is on. One of [pc, ally, enemy]
        - stat_dict = (dict, optional) The stats to automatically add. See stats.set_stats method. Default={}.
        - act_cat   = (list of str, optional) Which category of actions to automatically include. Default=[].
        - act_inc   = (list of str, optional) Which individual actions to automatically include. Default=[].

    Classes:
        - stats             :object to hold the stats for this character
        - resources         :object to hold the resources for this character
        - condition         :object to hold a condition of this character
        - actionChooser     :object that gives a character's available actions and the bias they will choose that action

    Methods:
        - _random_by_bias       :Will look through a bias dict and get a random element from it

        - add_attack            :add an attack to the character
        - take_damage           :have character take damage
        - add_condition         :adds condition to character
        - remove_condition      :removes condition of character
        - check_all_conditions  :do check_condtion method on all conditions

        - char_roll_stat        :have a character do a roll for a stat

        - start_turn            :refill all resources that replenish on their turn, and trigger certain start of turn effects
        - end_turn              :end the turn of the character, which will end certain effects

        - update_act_bias_res   :updates the action biases due to resources of this character
        - get_random_attack     :gets a random attack this character can do
        - get_random_action     :gets a random action dependent on characters conditions
    """
    def __init__(self, name, in_log, team, stat_dict={}, act_cat=[], act_inc=[]):
        """Init for combatCharacter

        Args:
            - name      = (str) The name of this character
            - in_log    = (customLogging.custom_logger obj) The log to use for all messages
            - team      = (str) The team the character is on. One of [pc, ally, enemy]
            - stat_dict = (dict, optional) The stats to automatically add. See stats.set_stats method. Default={}.
            - act_cat   = (list of str, optional) Which category of actions to automatically include. Default=[].
            - act_inc   = (list of str, optional) Which individual actions to automatically include. Default=[].
        
        Attributes:
            - _name             = (str) The character's name
            - _log              = (customLogging.custom_logger obj) The log for all messages
            - team              = (str) The character's team. One of [pc, ally, enemy]

            - _roll             = (rollFunctions.roll obj) The functions for rolling
            - char_stats        = (stats obj) The stats of this character
            - char_resources    = (resources obj) The resources of this character
            - char_actions      = (actionChooser obj) The actions available to this character
            - char_attacks      = (dict) The attacks of the character
                - Key               | Value
                - {name of attack}  | (int) Bias of this attack
            - char_conditions   = (dict) The current conditions of the character
                - Key                   | Value
                - {name of condition}   | (condition obj) The handling of this condition
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        self._name = name
        if not isinstance(in_log, _clog.custom_logger):
            raise TypeError('arg in_log must be a customLogging.custom_logger obj')
        self._log = in_log
        if (team == 'pc'):
            self.team = 'pc'
        elif (team == 'ally'):
            self.team = 'ally'
        else:
            self.team = 'enemy'

        # Create objects for character
        self._roll = _roll(self._log)
        self.char_stats = self.stats(name=name, in_char=self)
        self.char_stats.set_stats(stat_dict=stat_dict)
        self.char_resources = self.resources(name=name, in_char=self)
        self.char_actions = self.actionChooser(name=name, in_char=self, in_json='actions.json', category=act_cat, include_action=act_inc)

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

        self._log.debug(f'Created character {name} on team {team}')

        # Create condition dict
        self.char_conditions = {}
    # End __init__

    def _random_by_bias(self, bias_dict):
        """Will look through a bias dict and get a random element from it.

        Args:
            - bias_dict = (dict) The bias dict
                - Key           | Value
                - {any name}    | (int) The bias of this key; one of [16,8,4,2,1,0]

        Returns:
            - None if there were no possible selections (only happens if the dict is empty or has the wrong bias values), otherwise
            - (str) The key that was selected
        """
        if not isinstance(bias_dict, dict):
            raise TypeError('arg bias_dict must be a dict')

        try_list = [True for i in range(5)]
        # Will do up to 5 attempts, with each element of try_list being set to false if there is a miss
        for i_attempt in range(5):
            # Prepare weighted list
            bias_list = []
            for i_bias, i_try in enumerate(try_list):
                if not i_try:
                    continue
                for i in range(2**i_bias):
                    bias_list.append(2**i_bias)

            self._log.debugall(f'{self._name} search attempt {i_attempt}: {try_list}')
            true_bias = _random.choice(bias_list)   # Get random bias from weighted list
            possible_list = []
            for i_name, i_bias in bias_dict.items():
                if (i_bias==true_bias):
                    possible_list.append(i_name)  # Only consider items that have the decided bias
            self._log.debugall(f'{self._name} possible={possible_list}')
            # If there is a possibility space, choose from it
            if possible_list:
                return _random.choice(possible_list)
            # Else this attempt failed; retry without this bias
            try_list[int(_math.log2(true_bias))] = False

        self._log.debug(f'could not get a random item for {self._name}')
        return None
    # End _random_by_bias method

    ################################################################
    #============================ STATS ============================
    ################################################################

    class stats(object):
        """The stats of this character. In general, values that remain fairly static are stored here.
        There should only be one instance of this in a character.

        Args:
            - name      = (str) The character's name
            - in_char   = (combatCharacter obj) The character that this obj is an attribute of

        Methods:
            - add_property      :add properties to attribute property
            - set_stats         :set the stats of the character

            - get_mod           :get the modifier of an ability of the character
            - roll_ability      :have the character roll for an ability check
            - roll_skill        :have the character roll for a skill check
            - roll_save         :have the character roll for a saving throw
            - get_spell_save    :get the spell save DC for this character
        """
        def __init__(self, name, in_char):
            """Init of stats

            Args:
                - name      = (str) The character's name
                - in_char   = (combatCharacter obj) The character that this obj is an attribute of

            Attributes:
                - _name         = (str) The character's name
                - _char         = (combatCharacter obj) The combatCharacter that this obj belongs to

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
                - hit_dice      = (dict) This character's hit dice
                    - Key                   | Value
                    - {int of die faces}    | (int) The number of dice this character has of this size
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
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if not isinstance(in_char, combatCharacter):
                raise TypeError('arg in_char must be a combatCharacter obj')
            if (name != in_char._name):
                raise ValueError('arg name must be the same name as the attribute in arg in_char')
            self._name = name
            self._char = in_char

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
            self.hit_dice = {i:0 for i in range(6, 14, 2)}
            self.tot_hd = 0
            self.saves = []
            self.speed = 30
            self.spellcast = ''
            self.slots = {i:0 for i in range(1, 10)}
            self.tools = []
            self.imm = []
            self.res = []
            self.vul = []
            self.condimm = []
            self.property = {}
        # End __init__

        ################################
        #======== CHANGE STATS ========
        ################################

        def add_property(self, in_dict):
            """Adding additional property to stats, in attribute property. Also used to update the properties.

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
                    if (i_class == 'cleric'):
                        add_list += ['light_armor', 'medium_armor', 'shield', 'simple_weapon']
                    if (i_class == 'druid'):
                        add_list += ['light_armor', 'medium_armor', 'shield', 'club', 'dagger', 'dart', 'javelin', 'mace', 'quarterstaff', 'scimitar', 'sickle', 'sling', 'spear', 'herbalism_kit']
                    if (i_class == 'fighter'):
                        add_list += ['light_armor', 'medium_armor', 'heavy_armor', 'shield', 'simple_weapon', 'martial_weapon']
                    if (i_class == 'monk'):
                        add_list += ['simple_weapon', 'shortsword']
                    if (i_class == 'rogue'):
                        add_list += ['light_armor', 'simple_weapon', 'hand_crossbow', 'longsword', 'rapier', 'shortsword', 'thieves_tools']
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
            if ('expert' in stat_dict):
                self.expert = stat_dict['expert']
            if ('ac' in stat_dict):
                self.ac = stat_dict['ac']
            if ('max_hp' in stat_dict):
                if isinstance(stat_dict['max_hp'], str):
                    self.max_hp = self._char._roll.roll_d_str(stat_dict['max_hp'])
                else:
                    self.max_hp = stat_dict['max_hp']
            if ('hit_dice' in stat_dict):
                self.hit_dice = {i:0 for i in range(6, 14, 2)}
                self.tot_hd = 0
                for i_str in stat_dict['hit_dice']:
                    parse_tuple = self._char._roll._parse_d(i_str)
                    self.hit_dice[parse_tuple[0]] = parse_tuple[1]
                    self.tot_hd += parse_tuple[1]
            if ('saves' in stat_dict):
                self.saves = stat_dict['saves']
            if ('speed' in stat_dict):
                self.speed = stat_dict['speed']
            if ('spellcast' in stat_dict):
                self.spellcast = stat_dict['spellcast']
            if ('slots' in stat_dict):
                self.slots = {i:0 for i in range(1, 10)}
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
            self._char._log.debug(f'updated stats of {self._name}')
        # End set stats method

        ################################
        #========== GET STATS ==========
        ################################

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

        def roll_ability(self, ability, adv=0, suppress=False, apply_joat=True):
            """Will have the character make an ability check of the specified ability

            Args:
                - ability       = (str) The ability score to that the character is to roll for. One of [str, dex, con, int, wis, cha]
                - adv           = (int, optional) If there should be advantage/disadvantage on the roll. Advantage > 0, disadvantage < 0. Default=0
                - suppress      = (bool, optional) If the log message should be supressed. Default=False.
                - apply_joat    = (bool, optional) If check for bard feature Jack of All Trades should be done. Default=True.

            Returns:
                (int) The result of the roll
            """
            if (ability not in ABILITIES):
                raise ValueError(f'{ability} is not an ability')
            return_val = self._char._roll.roll_20(adv=adv) + self.get_mod(ability=ability)
            if (apply_joat and ('bard' in self.class_level)):
                if (self.class_level['bard'] >= 2):
                    return_val += self.prof // 2
            if not suppress:
                self._char._log.check(f'{self._name} rolls a {return_val} for a {ability} check')
            return return_val
        # End roll_ability method

        def roll_skill(self, skill, adv=0):
            """Will have the character make a skill check of the specified skill

            Args:
                - skill = (str) The skill that the character is to roll for
                - adv   = (int, optional) If there should be advantage/disadvantage on the roll. Advantage > 0, disadvantage < 0. Default=0

            Returns:
                (int) The result of the roll
            """
            if (skill not in SKILLS):
                raise ValueError(f'{skill} is not a skill')
            return_val = self.roll_ability(SKILLS[skill], adv=adv, suppress=True, apply_joat=False)
            if (skill in self.expert):
                return_val += 2 * self.prof
            elif (skill in self.skills):
                return_val += self.prof
            elif ('bard' in self.class_level):
                if (self.class_level['bard'] >= 2):
                    return_val += self.prof // 2
            self._char._log.check(f'{self._name} rolls a {return_val} for a {skill} check')
            return return_val
        # End roll_skill method

        def roll_save(self, ability, adv=0):
            """Will have the character make a saving throw of the specified ability. Note that bard feature Jack of All Trades does not apply to
            saving throws.

            Args:
                - ability   = (str) The ability score to that the character is to roll for. One of [str, dex, con, int, wis, cha]
                - adv       = (int, optional) If there should be advantage/disadvantage on the roll. Advantage > 0, disadvantage < 0. Default=0

            Returns:
                (int) The result of the roll
            """
            return_val = self.roll_ability(ability=ability, adv=adv, suppress=True, apply_joat=False) + (self.prof if ability in self.saves else 0)
            self._char._log.save(f'{self._name} rolls a {return_val} for a {ability} saving throw')
            return return_val
        # End roll_save method

        def get_spell_save(self):
            """Gets the spell save DC for this character.

            Args:
                No args

            Returns:
                (int) -1 if this character does not have a spell casting ability, otherwise their spell save DC
            """
            if not self.spellcast:
                self._char._log.stat(f'{self._name} does not have a spellcasting ability')
                return -1
            return self.get_mod(self.spellcast) + self.prof + 8
        # End get_spell_save method
    # End stats class

    ################################################################
    #========================== RESOURCES ==========================
    ################################################################

    class resources(object):
        """The resources of this character. These are values that will constantly change during battle. Anything that has
        a duration should also be stored here.
        There should only be one instance of this in a character.

        Args:
            - name      = (str) The character's name
            - in_char   = (combatCharacter obj) The character obj of this character

        Methods:
            - add_miscellaneous         :add new key to attribute miscellaneous

            - add_resource              :update attributes
            - restore_all_slots         :restore all spell slots
            - heal_hp                   :restore HP to the character
            - remove_hp                 :remove HP from the character

            - long_rest                 :refill all resources that replenish on a long rest
            - short_rest                :refill all resources that replenish on a short rest

            - _gain_death_save          :have the character gain a death save roll
            - do_death_save             :have character do a death save

            - get_resources_for_round   :get all the resources the character has for the round
            - get_next_available_slot   :get the next available spell slot
        """
        def __init__(self, name, in_char):
            """Init of resources

            Args:
                - name      = (str) The character's name
                - in_char   = (stats obj) The character obj of this character

            Attributes:
                - _name             = (str) The character's name
                - _char             = (combatCharacter obj) The stats of this character

                - hp                = (int) The current HP of the character
                - temp_hp           = (int) The temporary HP of the character
                - regular_action    = (int) The number of regular actions the character has
                - bonus_action      = (int) The number of bonus actions the character has
                - movement          = (float) The number of feet this character has for movement
                - reaction          = (int) The number of reactions this character has
                - hit_dice          = (dict of int) The number of dice in the Hit Dice pool for the character
                - spell_slots       = (dict of int) The number of Spell Slots of each spell level for the character
                - death_saves       = (dict of int) The number of death save successes and failures
                    - Key       | Value
                    - success   | (int) The number of successful death saves
                    - fail      | (int) The number of failed death saves

                - bardic_insp       = (int) The number of bardic inspirations this character has
                - channel_div       = (int) The number of channel divinity this character has
                - wild_shape        = (int) The number of wild shapes this character has
                - second_wind       = (int) The number of second winds the character has
                - action_surge      = (int) The number of action surges the character has

                - miscellaneous     = (dict of int) Any other miscellaneous resources
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if not isinstance(in_char, combatCharacter):
                raise TypeError('arg in_char must be a combatCharacter object')
            if (in_char._name != name):
                raise ValueError('arg name must match the name in arg in_char')
            self._name = name
            self._char = in_char

            self.hp = 1*in_char.char_stats.max_hp
            self.temp_hp = 0
            self.regular_action = 1
            self.bonus_action = 1
            self.movement = float(in_char.char_stats.speed)
            self.reaction = 1
            self.hit_dice = {}
            self.hit_dice = in_char.char_stats.hit_dice.copy()
            self.spell_slots = in_char.char_stats.slots.copy()
            self.death_saves = {'success':0, 'fail':0}

            # Class resources
            self.bardic_insp = 0
            self.channel_div = 0
            self.wild_shape = 0
            self.second_wind = 0
            self.action_surge = 0
            self.sneak_attack = 0

            self.miscellaneous = {}
        # End __init__

        ################################
        #======== NEW RESOURCE ========
        ################################

        def add_miscellaneous(self, in_list):
            """Adds new keys to attribute miscellaneous. This key will be initialized to 1.

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

        ################################
        #======= CHANGE RESOURCE =======
        ################################

        def add_resource(self, in_dict):
            """Add resources to the character, updating the attributes. Also used to remove resources.
            HP handling is done by heal_hp and remove_hp methods, not this one.

            Args:
                - in_dict   = (dict) Resources to change. If negative, will remove resources instead.
                    - Key       | Value
                    - temp_hp   | (int) Increase temp HP
                    - regular   | (int) Increase regular actions
                    - bonus     | (int) Increase bonus actions
                    - reaction  | (int) Increase reaction
                    - movement  | (int or float) Increase movement
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
                if not isinstance(in_dict['temp_hp'], int):
                    raise TypeError('arg in_dict["temp_hp"] must be an int')
                self.temp_hp += in_dict['temp_hp']
                self._char._log.resource(f'{self._name} now has {self.temp_hp} temporary HP')

            if ('regular' in in_dict):
                if not isinstance(in_dict['regular'], int):
                    raise TypeError('arg in_dict["regular"] must be an int')
                self.regular_action = max(0, self.regular_action + in_dict['regular'])
                self._char._log.resource(f'{self._name} now has {self.regular_action} regular actions')

            if ('bonus' in in_dict):
                if not isinstance(in_dict['bonus'], int):
                    raise TypeError('arg in_dict["bonus"] must be an int')
                self.bonus_action = max(0, self.bonus_action + in_dict['bonus'])
                self._char._log.resource(f'{self._name} now has {self.bonus_action} bonus actions')

            if ('reaction' in in_dict):
                if not isinstance(in_dict['reaction'], int):
                    raise TypeError('arg in_dict["reaction"] must be an int')
                self.reaction = max(0, self.reaction + in_dict['reaction'])
                self._char._log.resource(f'{self._name} now has {self.reaction} reactions')

            if ('movement' in in_dict):
                if not isinstance(in_dict['movement'], (int, float)):
                    raise TypeError('arg in_dict["movement"] must be an int or float')
                if ('grappled' in self._char.char_conditions):
                    self._char._log.resource(f'{self._name} cannot gain any speed because they are grappled')
                else:
                    self.movement = max(0.0, self.movement + float(in_dict['movement']))
                    self._char._log.resource(f'{self._name} now has {self.movement} feet of movement')

            if ('hit_dice' in in_dict):
                if not isinstance(in_dict['hit_dice'], dict):
                    raise TypeError('arg in_dict["hit_dice"] must be an dict')
                valid_faces = range(2, 14, 2)
                for i_faces, i_count in in_dict['hit_dice'].items():
                    if (i_faces not in valid_faces):
                        continue
                    if not isinstance(i_count, int):
                        raise TypeError('arg in_dict["hit_dice"][{faces}] must be an int')
                    self.hit_dice[i_faces] = max(0, min(self._char.char_stats.hit_dice[i_faces], self.hit_dice[i_faces] + i_count))
                self._char._log.resource(f'{self._name} now has {self.hit_dice} hit dice')

            if ('slots' in in_dict):
                if not isinstance(in_dict['slots'], dict):
                    raise TypeError('arg in_dict["slots"] must be an dict')
                valid_levels = range(1,10)
                for i_level, i_count in in_dict['slots'].items():
                    if (i_level not in valid_levels):
                        continue
                    if not isinstance(i_count, int):
                        raise TypeError('arg in_dict["slots"][{level}] must be an int')
                    self.spell_slots[i_level] = max(0, min(self._char.char_stats.slots[i_level], self.spell_slots[i_level] + i_count))
                self._char._log.resource(f'{self._name} now has {self.spell_slots} spell slots')
        # End add_resource method

        def restore_all_slots(self):
            """Restores all the spell slots of the character

            Args:
                No args

            Returns:
                No return value
            """
            restore_count = 0
            for i_slot, i_count in self._char.char_stats.slots.items():
                self.spell_slots[i_slot] = 1*i_count
                restore_count += i_count
            if restore_count:
                self._char._log.resource(f'{self._name} restored all of their spell slots')
        # End restore_all_slots method

        def heal_hp(self, amount):
            """Heal the specified amount of HP to the character

            Args:
                - amount = (int) The amount to heal. If less than 0, will heal to max.

            Returns:
                (int) The new current HP of the character
            """
            if not isinstance(amount, int):
                raise TypeError('arg amount must be an int')

            if ('death' in self._char.char_conditions):
                self._char._log.resource('cannot heal a dead character')
                return 0

            if (amount < 0):
                self.hp = 1*self._char.char_stats.max_hp
                self._char._log.resource(f'{self._name} was healed to full HP={self.hp}')
            else:
                self.hp = min(self._char.char_stats.max_hp, self.hp + amount)
                self._char._log.resource(f'{self._name} was healed {amount} to HP={self.hp}')

            if ((self.hp>0) and ('dying' in self._char.char_conditions)):
                self._char.remove_condition('dying')
            return self.hp
        # End heal_hp method

        def remove_hp(self, amount):
            """Remove the specified amount of HP to the character. This should only be for PCs, or NPCs with the important key in
            attribute self.char_stats.property

            Args:
                - amount = (int) The amount to remove. Must be non-negative.

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
                if ((self._char.team=='pc') or ('important' in self._char.char_stats.property)):
                    if (abs(remainder)>=self._char.char_stats.max_hp):
                        self._char.add_condition('death', 'indefinite')
                        self._char._log.conditn(f'{self._name} is now dead after losing {amount} HP (excess was >= max HP)')
                    else:
                        self._char.add_condition('dying', 'indefinite')
                        self._char._log.conditn(f'{self._name} is now dying after losing {amount} HP')
                else:
                    self._char.add_condition('death', 'indefinite')
                    self._char._log.conditn(f'{self._name} is now dead after losing {amount} HP')
            else:
                self._char._log.resource(f'{self._name} has {self.hp} HP after losing {amount} HP')
            return self.hp
        # End remove_hp method

        ################################
        #=========== RESTING ===========
        ################################

        def long_rest(self):
            """The character will do a long rest, regaining all resources that come with it

            Args:
                No args

            Returns:
                No return value
            """
            if (self.hp == 0):
                self._char._log.resource(f'{self._name} cannot do long rest because they have 0 HP')
                return

            # Character cannot recieve benefit of a long rest if they are dead
            if ('death' in self._char.char_conditions):
                return

            # Replenish HP
            self.heal_hp(-1)

            # Replenish hit dice
            if self._char.char_stats.tot_hd:
                replenish_count = max(self._char.char_stats.tot_hd // 2, 1)
                full_break = False
                for i_faces in range(12, 4, -2):
                    if (self._char.char_stats.hit_dice[i_faces] <= 0):
                        continue
                    for i in range(self._char.char_stats.hit_dice[i_faces]):
                        if (replenish_count==0):
                            full_break = True
                            break
                        if (self.hit_dice[i_faces] >= self._char.char_stats.hit_dice[i_faces]):
                            self.hit_dice[i_faces] = 1*self._char.char_stats.hit_dice[i_faces] # Clip to max just in case
                            break
                        self.hit_dice[i_faces] += 1
                        replenish_count -= 1
                    if full_break:
                        break
                self._char._log.resource(f'{self._name} restored {replenish_count} hit dice')

            # Replenish class features
            for i_class, i_level in self._char.char_stats.class_level.items():
                if (i_class == 'bard'):
                    self.bardic_insp = max(1, self._char.char_stats.get_mod('cha'))
                    self.restore_all_slots()
                    self._char._log.resource(f'{self._name} restored their bard features after a long rest')
                if (i_class == 'cleric'):
                    if (i_level >= 18):
                        self.channel_div = 3
                    elif (i_level >= 6):
                        self.channel_div = 2
                    else:
                        self.channel_div = 1
                    self.restore_all_slots()
                    self._char._log.resource(f'{self._name} restored their cleric features after a long rest')
                if (i_class == 'druid'):
                    self.wild_shape = 2
                    self.restore_all_slots()
                    self._char._log.resource(f'{self._name} restored their druid features after a long rest')
                if (i_class == 'fighter'):
                    self.second_wind = 1
                    if (i_level >= 2):
                        self.action_surge = 2 if i_level >= 17 else 1
                    self._char._log.resource(f'{self._name} restored their fighter features after a long rest')
                if (i_class == 'warlock'):
                    self.restore_all_slots()
                    self._char._log.resource(f'{self._name} restored their warlock features after a long rest')

            # Replenish unique resources
            for i_k in self.miscellaneous:
                if (i_k == 'psionic_dice_regain'):
                    self.miscellaneous[i_k] = 1
                    self._char._log.resource(f'{self._name} restored their one psionic dice regain after a long rest')
                if (i_k == 'psionic_energy'):
                    self.miscellaneous[i_k] = 2*self._char.char_stats.prof
                    self._char._log.resource(f'{self._name} restored all of their psionic dice after a long rest')
                if (i_k == 'warding_flare'):
                    self.miscellaneous[i_k] = min(1, self._char.char_stats.get_mod('wis'))
                    self._char._log.resource(f'{self._name} restored their warding flare after a long rest')
        # End long_rest method

        def short_rest(self, spend_dice=[]):
            """The character will do a short rest, regaining all resources that come with it

            Args:
                - spend_dice = (list of str, optional) The list of #d# string of hit dice to spend to heal. If Default=[], will skip spending hit dice.

            Returns:
                No return value
            """
            if (self.hp == 0):
                self._char._log.resource(f'{self._name} cannot do short rest because they have 0 HP')
                return
            if not isinstance(spend_dice, list):
                raise TypeError('arg spend_dice must be a list')

            if spend_dice:
                heal_total = 0
                for i_str in spend_dice:
                    parse_tuple = self._char._roll._parse_d(i_str)
                    if (parse_tuple[0] not in self.hit_dice):
                        self._char._log.debug(f'{self._name} does not have a d{parse_tuple[0]} hit die')
                        continue
                    for i in range(parse_tuple[1]):
                        if (self.hit_dice[parse_tuple[0]]==0):
                            break
                        self.hit_dice[parse_tuple[0]] -= 1
                        heal_total += self._char._roll.roll_d(parse_tuple[0]) + self._char.char_stats.get_mod('con')
                self._char._log.resource(f'{self._name} is using {spend_dice} hit dice to heal')
                self.heal_hp(heal_total)

            # Replenish class features
            for i_class, i_level in self._char.char_stats.class_level.items():
                if (i_class == 'cleric'):
                    if (i_level >= 18):
                        self.channel_div = 3
                    elif (i_level >= 6):
                        self.channel_div = 2
                    else:
                        self.channel_div = 1
                    self._char._log.resource(f'{self._name} restored some cleric features after a short rest')
                if (i_class == 'druid'):
                    self.wild_shape = 2
                    self._char._log.resource(f'{self._name} restored some druid features after a short rest')
                if (i_class == 'fighter'):
                    self.second_wind = 1
                    if (i_level >= 2):
                        self.action_surge = 2 if i_level >= 17 else 1
                    self._char._log.resource(f'{self._name} restored some fighter features after a short rest')
                if (i_class == 'warlock'):
                    self.restore_all_slots()
                    self._char._log.resource(f'{self._name} restored their warlock features after a short rest')

            # Replenish unique resources
            for i_k in self.miscellaneous:
                if (i_k == 'psionic_dice_regain'):
                    self.miscellaneous[i_k] = 1
                    self._char._log.resource(f'{self._name} restored their one psionic dice regain after a short rest')
        # End short_rest method

        ################################
        #========= DEATH SAVES =========
        ################################

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
            self._char._log.resource(f'{self._name} death saves = {self.death_saves}')

            if (self.death_saves['success'] >= 3):
                self._char._log.conditn(f'{self._name} will stabilize after 3 death save successes')
                self._char.add_condition('stabilized', 'indefinite')
            elif (self.death_saves['fail'] >= 3):
                self._char.remove_condition('dying')
                self._char.add_condition('death', 'indefinite')
                self._char._log.conditn(f'{self._name} is now dead after 3 death save failures')
            elif ((self.death_saves['fail'] > 0) and ('stabilized' in self._char.char_conditions)):
                self._char.remove_condition('stabilized')
                self._char._log.conditn(f'{self._name} is no longer stabilized after gaining a death save fail')
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
            if ('dying' not in self._char.char_conditions):
                raise Exception('cannot do death save on character that is not dying')
            if ('stabilized' in self._char.char_conditions):
                self._char._log.debug(f'{self._name} is already stabilized and does not need to do death saves')
                return {"success":0, "fail":0}

            death_roll = self._char._roll.roll_20()
            if (death_roll==20):
                self._char._log.save(f'{self._name} critically succeeds on their death save')
                self.heal_hp(1)
                return {"success":0, "fail":0}

            if (death_roll>=10):
                self._char._log.save(f'{self._name} succeeds on death save')
                self._gain_death_save(True)
            elif (death_roll==1):
                self._char._log.save(f'{self._name} critically fails their death save')
                self._gain_death_save(False, count=2)
            else:
                self._char._log.save(f'{self._name} fails their death save')
                self._gain_death_save(False)
            return self.death_saves
        # End do_death_save method

        ################################
        #======= ROUND HANDLING =======
        ################################

        def get_resources_for_round(self):
            """Will get all resources the character has for the round

            Args:
                No args

            Returns: (dict) The resources the character has
                - Key       | Value
                - regular   | (int) How many regular actions they have
                - bonus     | (int) How many bonus actions they have
                - reaction  | (int) How many reactions they have
                - movement  | (int) How many feet of movement they have
                - slots     | (dict of int) How many spell slots per level they have
            """
            return_val = {}
            return_val['regular'] = 1*self.regular_action
            return_val['bonus'] = 1*self.bonus_action
            return_val['reaction'] = 1*self.reaction
            return_val['movement'] = 1.0*self.movement
            return_val['slots'] = self.spell_slots.copy()
            self._char._log.debugall(f'{self._name} round resources={return_val}')
            return return_val
        # End get_resources_for_round method

        def get_next_available_slot(self, min_level):
            """Given a specified spell level, return the next available spell slot that level or higher. For example:
                - min_level = 3
                - spell_slots = {1:2, 2:0, 3:0, 4:2, 5:3}
                - return = 4

            Args:
                - min_level = (int) The minimum spell slot level to get. Must be in 1 to 9 inclusive

            Returns:
                (int) 0 if there are no levels available, otherwise the next available spell slot that level or higher
            """
            if not isinstance(min_level, int):
                raise TypeError('arg min_level must be an int')
            if (min_level not in range(1, 10)):
                raise ValueError('arg min_level must be in 1 to 9 inclusive')
            
            for i in range(9, 0, -1):
                if (i < min_level):
                    return 0
                if (self.spell_slots[i] > 0):
                    return i
            return 0
        # End get_next_available_slot method
    # End resources class

    ################################################################
    #========================== CONDITION ==========================
    ################################################################

    class condition(object):
        """A condition that afflicts a character.

        Args:
            - name      = (str) Name of this condtion
            - duration  = (str) Duration of this condition in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                eont (end of next turn)]. Example: 2 round or 3 minute. If is the str 'indefinite', will create it as one that will not remove after a set time.
            - in_char   = (combatCharacter obj) The condition this character is afflicting
            - prop      = (any, optional) Any additional information that is needed for this condition

        Methods:
            - check_condition   :after a certain amount of time has passed, check to see if the condition is done or not
            - add_time          :add more time to the condtion

            - _effect_on_gain   :effects when gaining a condition
            - _effect_on_sot    :effects when the character is at the start of their turn
            - _effect_on_eot    :effects when the character is at the end of their turn
            - _effect_on_loss   :effects when losing a condition
            - effect_on_oct     :effects that trigger when checked on Other Character's Turn
        """
        def __init__(self, name, duration, in_char, prop=None):
            """Init for condition

            Args:
                - name      = (str) Name of this condtion. If it starts with c_, it is a custom condition.
                - duration  = (str) Duration of this condition in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                    eont (end of next turn)]. Example: 2 round or 3 minute. If is the str 'indefinite', will create it as one that will not remove after a set time.
                - in_char   = (combatCharacter obj) The condition this character is afflicting
                - prop      = (any, optional) Any additional information that is needed for this condition

            Attributes:
                - name          = (str) Name of this condition
                - _custom       = (bool) If this condition is a custom one
                - _char         = (combatCharacter obj) The character that this condition is afflicting
                - indefinite    = (bool) If this condition is indefinite, i.e. has no end
                - unit          = (str) Time unit used for condition duration
                - remaining     = (float) Time remaining for condition, in unit above
                - valid         = (bool) If the condition is valid because there is still time remaining on its duration
                - _properties   = (any) Any properties that should go with this condtion
                - _stored       = (dict) Any values that need to be stored for later
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if name.startswith('c_'):
                self.name = name[2:]
                self._custom = True
            else:
                self.name = name
                self._custom = False
            if not isinstance(duration, str):
                raise TypeError('arg duration must be a str')
            if not isinstance(in_char, combatCharacter):
                raise TypeError('arg in_char must be a combatCharacter obj')
            self._char = in_char
            self._properties = prop
            self.valid = True

            if (duration=='indefinite'):
                self.indefinite = True
                self.unit = ''
                self.remaining = 0
                return
            self.indefinite = False

            split_list = duration.split(' ')
            if (len(split_list)!=2):
                raise ValueError('arg duration is not in the right format: # unit')
            if (split_list[1] not in ['round', 'second', 'minute', 'hour', 'day', 'sont', 'eont']):
                raise ValueError('arg duration had an invalid unit')
            self.unit = split_list[1]
            if (not split_list[0].isnumeric()):
                raise ValueError('arg duration did not have a number for time')
            self.remaining = float(split_list[0])

            self._stored = {}
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
                self._char._log.conditn(f'{self.name} continues as an indefinite condition')
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
            # sont and eont will not lose time with round and second
            elif (self.unit=='sont'):
                if (unit in ['minute', 'hour', 'day']):
                    self.remaining -= (TIME_UNITS[unit]/TIME_UNITS['sont'])*amount
            elif (self.unit=='eont'):
                if (unit in ['minute', 'hour', 'day']):
                    self.remaining -= (TIME_UNITS[unit]/TIME_UNITS['eont'])*amount
            else:
                self.remaining -= (TIME_UNITS[unit]/TIME_UNITS[self.unit])*amount

            if self.remaining <= 0:
                self._char._log.conditn(f'{self.name} has ended')
                self.valid = False
                return True
            self._char._log.conditn(f'{self.name} has {round(self.remaining, 2)} {self.unit}(s) remaining')
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
                self._char._log.debug(f'cannot add time to an indefinite condition {self.name}')
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
            self._char._log.conditn(f'{self.name} now lasts for {self.remaining} {self.unit}(s)')
        # End add_time method

        ################################
        #====== CONDITION EFFECTS ======
        ################################

        def _effect_on_gain(self):
            """Condition effects that trigger when a character gains the specified condition. There should be a correspondence between this method and _effect_on_loss.

            Args:
                No args

            Returns:
                No return value
            """
            # Custom effect
#            if self._custom:
#                return custom_condition(self.name, 'gain', character)

            if (self.name in ['grappled', 'restrained']):
                self._stored['speed'] = 1*self._char.char_stats.speed
                self._char.char_stats.set_stats({'speed': 0})
                self._char.char_resources.movement = 0.0
                self._char._log.conditn(f'{self._char._name} had their speed set to 0 because of {self.name}')
                return
            if (self.name == 'stabilized'):
                self._char.char_resources.death_saves = {'success':0, 'fail':0}
                self._char._log.conditn(f'{self._char._name} resets their death save count after being stabilized')
                return
        # End _effect_on_gain method

        def _effect_on_sot(self):
            """Condition effects that trigger when at the start of the character's turn.

            Args:
                No args

            Returns:
                No return value
            """
            # Custom effect
#            if self._custom:
#                return custom_condition(self.name, 'sot', character)

            if (self.name in ['grappled', 'restrained']):
                self._char.char_resources.movement = 0.0
                self._char._log.conditn(f'{self._char._name} has 0 feet of movement because they have {self.name}')
                return
        # End _effect_on_sot method

        def _effect_on_eot(self):
            """Condition effects that trigger when at the end of the character's turn.

            Args:
                No args

            Returns:
                No return value
            """
            # Custom effect
#            if self._custom:
#                return custom_condition(self.name, 'eot', character)
            return
        # End _effect_on_eot method

        def _effect_on_loss(self):
            """Condition effects that trigger when a character loses the specified condition. There should be a correspondence between this method and _effect_on_gain.

            Args:
                No args

            Returns:
                No return value
            """
            # Custom effect
#            if self._custom:
#                return custom_condition(self.name, 'loss', character)

            if (self.name in ['grappled', 'restrained']):
                self._char.char_stats.set_stats({'speed': 1*self._stored['speed']})
                self._char.char_resources.movement = 1*self._stored['speed']
                self._char._log.conditn(f'{self._char._name} regains their normal speed after losing {self.name}')
                return
            if (self.name == 'dying'):
                self._char.char_resources.death_saves = {'success':0, 'fail':0}
                self._char._log.conditn(f'{self._char._name} resets their death save count')
                return
        # End _effect_on_loss method

        def effect_on_oct(self, pass_arg=None):
            """Conditions effects that will happen on an other character's turn i.e. an effect on a target that happens on the source's turn.

            Args:
                - pass_arg  = (any, optional) Any args that need to be passed to the condition. Default=None.

            Returns:
                No return value
            """
            # Custom effect
#            if self._custom:
#                return custom_condition(name=self.name, cond_type='oct', character=character, pass_arg=pass_arg)
            return
        # End effect_on_oct method
    # End condition class

    ################################################################
    #======================== ACTIONCHOOSER ========================
    ################################################################

    class actionChooser(object):
        """The available actions of a character and the bias they are likely to pick each one.
        There should only be one instance of this in a character.

        Args:
            - name              = (str) The name of the character
            - in_char           = (combatCharacter obj) The combatCharacter that this obj is an attribute of
            - in_json           = (str) Path of a json to load all default actions
            - category          = (list of str, optional) Which categories to automatically include in the above json. Default=[]
            - include_action    = (list of str, optional) All other optional actions to load. These actions must be in the above
                json. Default=[]

        Methods:
            - add_action            :adds a new action for the character
            - remove_action         :removes an action this character has
            - change_bias           :change the bias of an action
            - update_act_bias_cond  :have character consider their conditions to update their biases

            - get_all_actions       :gets all actions the character can do
            - can_do_action         :checks to see if character can do such an action
            - _get_random_action     :will get a random action that this character can do
        """
        def __init__(self, name, in_char, in_json, category=[], include_action=[]):
            """Init of actionChooser

            Args:
                - name              = (str) The name of the character
                - in_char           = (combatCharacter obj) The combatCharacter that this obj is an attribute of
                - in_json           = (str) Path of a json to load all default actions
                - category          = (list of str, optional) Which categories to automatically include in the above json. Default=[]
                - include_action    = (list of str, optional) All other optional actions to load. These actions must be in the above
                    json. Default=[]

            Attributes:
                - _name     = (str) The name of the character
                - _char     = (combatCharacter) The combatCharacter that this obj is an attribute of
                - actions   = (dict) All actions available to this character
                    - Key       | Value
                    - regular   | (dict) All regular actions
                        - Key               | Value
                        - {name of action}  | (int) The bias of that action
                    - movement  | (dict) All movement actions; same format as regular
                    - bonus     | (dict) All bonus actions; same format as regular
                    - reaction  | (dict) All reactions; same format as regular
                    - free      | (dict) All free actions; same format as regular
                    - special   | (dict) All special actions; same format as regular
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if not isinstance(in_char, combatCharacter):
                raise TypeError('arg in_char must be a combatCharacter obj')
            if (name != in_char._name):
                raise ValueError('arg name must be the same name as attribute in arg in_char')
            self._name = name
            self._char = in_char
            if not isinstance(category, list):
                raise TypeError('arg category must be a list of str')
            if not isinstance(include_action, list):
                raise TypeError('arg include_action must be a list of str')
            self.actions = {
                'regular': {},
                'movement': {},
                'bonus': {},
                'reaction': {},
                'free': {},
                'special': {}
            }

            with open(in_json, 'r') as read_file:
                data = _json.load(read_file)
                if not isinstance(data, dict):
                    raise TypeError(f'data in {in_json} must be a dict of categories')
                for i_category, i_action_dict in data.items():
                    if not isinstance(i_action_dict, dict):
                        raise TypeError(f'value of a category in {in_json} must be a dict')
                    for i_action, i_dict in i_action_dict.items():
                        if not (
                            (i_category == 'default') or
                            (i_category in category) or
                            (i_action in include_action)
                        ):
                            continue

                        if (i_dict['type'] not in ['regular', 'movement', 'bonus', 'reaction', 'free', 'special']):
                            raise ValueError(f'value of key "type" in action {i_action} in {in_json} must be in [regular, movement, bonus, reaction, free, special]')
                        self.actions[i_dict['type']][i_action] = i_dict['bias']
            self._char._log.debugall(f'{self._name} actions={self.get_all_actions().keys()}')
        # End __init__

        ################################
        #====== ACTIONS HANDLING ======
        ################################

        def add_action(self, in_dict):
            """Adds new actions for the character

            Args:
                - in_dict = (dict) The actions to add
                    - Key           | Value
                    - {action name} | (dict) Attributes of this attack
                        - Key   | Value
                        - bias  | (int) The bias of the action
                        - type  | (str) The type this action is. One of [regular, movement, bonus, reaction, free]

            Returns:
                No return value
            """
            if not isinstance(in_dict, dict):
                raise TypeError('arg in_dict must be a dict')

            for i_action, i_dict in in_dict.items():
                if (i_dict['type'] not in ['regular', 'movement', 'bonus', 'reaction', 'free']):
                    raise ValueError(f'value type for {i_action} must be in [regular, movement, bonus, reaction, free]')
                if (i_action in self.actions[i_dict['type']]):
                    raise ValueError(f'{self._name} already has a {i_dict["type"]} action named {i_action}')
                self.actions[i_dict['type']][i_action] = i_dict['bias']
            self._char._log.debugall(f'{self._name} now has actions = {in_dict}')
        # End add_action method

        def remove_action(self, name, act_type):
            """Remove the specified action

            Args:
                - name      = (str) The name of the action
                - act_type  = (str) The type of the action. One of [regular, movement, bonus, reaction, free, special]

            Returns:
                No return value
            """
            if not isinstance(name, str):
                raise TypeError('arg name must be a str')
            if (act_type not in ['regular', 'movement', 'bonus', 'reaction', 'free']):
                raise ValueError('arg act_type must in [regular, movement, bonus, reaction, free]')
            if (name not in self.actions[act_type]):
                self._char._log.debugall(f'{self._name} had no {act_type} action called {name} to remove')
                return
            del self.actions[act_type][name]
            self._char._log.debugall(f'{self._name} no longer has a {act_type} action {name}')
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
                for i_type, i_dict in self.actions.items():
                    if (i_name not in i_dict):
                        self._char._log.debugall(f'{self._name} did not have a {i_type} action called {i_name}')
                        continue
                    self.actions[i_type][i_name] = i_bias
                    break
                else:
                    self._char._log.debug(f'{self._name} did not have an action called {i_name}')
            self._char._log.debug(f'updated action biases of {self._name}')
        # End change_bias method

        def update_act_bias_cond(self):
            """Will look through all conditions of the character, then update action biases because of this

            Args:
                No args

            Returns:
                No return value
            """
            update_dict = {}
            if ('druid' in self._char.char_stats.class_level):
                if ('shillelagh' in self._char.char_conditions):
                    update_dict['cast_shillelagh'] = 0
                elif ('cast_shillelagh' in self.actions['bonus']):
                    update_dict['cast_shillelagh'] = 16

            self.change_bias(update_dict)
        # End update_act_bias_cond method

        def update_act_bias_res(self):
            """Will look at the character's resources, then update their action biases because of this

            Args:
                No args

            Returns:
                No return value
            """
            update_dict = {}
            all_actions = self.get_all_actions()

            # Check channel divinity
            if (self._char.char_resources.channel_div > 0):
                for i_action in all_actions.keys():
                    if (i_action.startswith('cd_')):
                        update_dict[i_action] = 0

            self.change_bias(update_dict)
        # End update_act_bias_res method

        ################################
        #======== ACTIONS INFO ========
        ################################

        def get_all_actions(self):
            """Get all actions of this character

            Args:
                No args

            Returns: (dict) All actions of this character
                - Key               | Value
                - {name of action}  | (str) Type of action
            """
            return_val = {}
            for i_type, i_dict in self.actions.items():
                for i_action in i_dict.keys():
                    return_val[i_action] = i_type
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

        def _get_random_action(self, act_type):
            """Gets a random action of this character, weighted by the biases

            Args:
                - act_type = (str) The type of the action. One of [regular, movement, bonus, reaction, free]

            Returns:
                - None if there are no actions available, otherwise
                - (str) The name of an action this character can do
            """
            if (act_type not in ['regular', 'movement', 'bonus', 'reaction', 'free']):
                raise ValueError('arg act_type must in [regular, movement, bonus, reaction, free]')

            if not self.actions[act_type]:
                self._char._log.debug(f'{self._name} has no {act_type} actions')
                return None

            self._char._log.simulatn(f'{self._name} will look for a {act_type} action')
            return_val = self._char._random_by_bias(self.actions[act_type])
            if not return_val:
                self._char._log.debug(f'could not get a random {act_type} action for {self._name}')
            return return_val
        # End _get_random_action method
    # End actionChooser class

    ################################################################
    #=========================== MODIFY ===========================
    ################################################################

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
                self._log.debug(f'attack {i_name} already exists for {self._name}')
                continue
            self.char_attacks[i_name] = i_bias
        self._log.debug(f'added {in_dict.keys()} to {self._name}')
    # End add_attack method

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
            if ('petrified' in self.char_conditions):
                total_damage += i_value // 2
            if (i_type in self.char_stats.imm):
                continue
            if (i_type in self.char_stats.res):
                total_damage += i_value // 2
            elif (i_type in self.char_stats.vul):
                total_damage += i_value * 2
            else:
                total_damage += i_value
        self._log.damage(f'{self._name} takes {total_damage} adjusted damage')
        if ('dying' in self.char_conditions):
            self.char_resources._gain_death_save(self, False, 2 if was_crit else 1)
            return (total_damage, 0)
        return (total_damage, self.char_resources.remove_hp(total_damage))
    # End take_damage method

    def add_condition(self, name, duration, prop=''):
        """Adds a condition to the character. If character already has the condition, will add more time to its remaining time. Certain conditions will
        also cause the character to gain other conditions. Make sure that you also have those conditions removed in remove_condition method.

        Args:
            - name      = (str) Name of this condtion
            - duration  = (str) Duration of this condition in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                eont (end of next turn)]. Example: 2 round or 3 minute. Can be 'indefinite' if there is no duration
            - prop      = (str, optional) Any properties that should go with the condition. Default=''

        Returns:
            No return value
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        if (name in self.char_conditions):
            cond_obj = self.char_conditions[name]
            if not isinstance(cond_obj, combatCharacter.condition):
                raise TypeError(f"{self._name} had condition {name}'s value not a combatCharacter.condition obj")
            self._log.conditn(f'Adding {duration} for {name} on {self._name}')
            return cond_obj.add_time(duration=duration)
        
        new_cond = combatCharacter.condition(name=name, duration=duration, in_char=self, prop=prop)
        self.char_conditions[name] = new_cond
        if (duration=='indefinite'):
            self._log.conditn(f'{self._name} now has condition {name} indefinitely')
        else:
            self._log.conditn(f'{self._name} now has condition {name} for {duration}')

        # Effects on gain
        new_cond._effect_on_gain()

        # Certain conditions will also cause the character to gain other conditions
        if (name=='dying'):
            self.add_condition('unconscious', 'indefinite')
        if (name in ['paralyzed', 'petrified', 'stunned', 'unconscious']):
            self.add_condition('incapacitated', 'indefinite')
        if (name=='unconscious'):
            self.add_condition('prone', 'indefinite')

        # Certain conditions will remove other conditions
        if (name=='incapacitated'):
            self.remove_condition('dodge')
    # End add_condition method

    def remove_condition(self, name):
        """Remove the specified condtion from the character

        Args:
            - name = (str) Name of the condition to remove

        Returns:
            No return value
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        if (name not in self.char_conditions):
            self._log.conditn(f'Could not remove {name} from {self._name} because they did not have such a condition')
        cond_obj = self.char_conditions[name]
        if not isinstance(cond_obj, combatCharacter.condition):
            raise TypeError(f"{self._name} had condition {name}'s value not a combatCharacter.condtion obj")
        
        cond_obj._effect_on_loss()
        del self.char_conditions[name]

        # Certain conditions should be removed when losing other conditions
        if (name=='dying'):
            self.remove_condition('unconscious')
        if (name in ['paralyzed', 'petrified', 'stunned', 'unconscious']):
            self.remove_condition('incapacitated')

        self._log.conditn(f'{self._name} no longer has {name}')
    # End remove_condition method

    def check_all_conditions(self, time_passed):
        """Will check all conditions with the specified time passing.

        Args:
            - time_passed = (str) Amount of time that has passed in # {unit} format. Possible units are [round, second, minute, hour, day, sont (start of next turn),
                eont (end of next turn)]. Example: 2 round or 3 minute.

        Returns:
            (int) How many conditions remain on the character
        """
        if self.char_conditions:
            self._log.conditn(f'Checking conditions of {self._name}')
            delete_list = []
            for i_name, i_condition in self.char_conditions.items():
                if not isinstance(i_condition, combatCharacter.condition):
                    raise TypeError(f'key {i_name} has its corresponding value not a combatCharacter.condition obj')
                condition_end = i_condition.check_condition(time_passed=time_passed)
                if ((condition_end) or (not i_condition.valid)):
                    delete_list.append(i_name)
            for i_name in delete_list:
                self.remove_condition(i_name)
            return len(self.char_conditions)

        return 0
    # End check_all_conditions method

    ################################################################
    #======================== ABILITY ROLLS ========================
    ################################################################

    def char_roll_stat(self, name, adv=0):
        """Have the character do a ability check, skill check, or saving throw. Will be affected by conditions.

        Args:
            - name  = (str) The stat to roll. If an ability or skill check, just give the name. If a saving throw, give {ability} save
            - adv   = (int, optional) If there should be advantage/disadvantage on the roll. Advantage > 0, disadvantage < 0. Default=0

        Returns:
            (int) The result of the roll
        """
        if not isinstance(name, str):
            raise TypeError('arg name must be a str')
        if not isinstance(adv, int):
            raise TypeError('arg adv must be an int')

        def _overlap(in_set):
            return not (set(self.char_conditions).isdisjoint(in_set))
        # End _overlap inner function

        # 20230928 Currently doing a blanket fail for certain conditions, don't know how to handle the specifics yet
        split_list = name.split(' ')
        if (split_list[0] in ABILITIES):
            # Handle saving throws
            if split_list[1]:
                if ((split_list[0] in ['str, dex']) and _overlap({'paralyzed', 'petrified', 'stunned', 'unconscious'})):
                    self._log.save(f'{self._name} automatically fails saving throw because of a condition')
                    return AUTO_FAIL
                if (split_list[0]=='dex'):
                    if _overlap({'restrained'}):
                        self._log.save(f'{self._name} has disadvantage on dex saving throw because of restrained')
                        adv -= 1
                    elif _overlap({'dodge'}):
                        self._log.save(f'{self._name} had advantage on dex saving throw because they are dodging')
                        adv += 1
                return_val = self.char_stats.roll_save(split_list[0], adv=adv)
            
            # Handle ability check
            else:
                if _overlap({'blinded', 'deafened'}):
                    self._log.check(f'{self._name} automatically fails ability check because of a condition')
                    return AUTO_FAIL
                if _overlap({'charmed', 'frightened', 'poisoned'}):
                    self._log.check(f'{self._name} has disadvantage on ability check because of a condition')
                    adv -= 1
                return_val = self.char_stats.roll_ability(split_list[0], adv=adv)

        # Handle skill check
        elif (split_list[0] in SKILLS):
            if _overlap({'blinded', 'deafened'}):
                self._log.check(f'{self._name} automatically fails skill check because of a condition')
                return AUTO_FAIL
            if _overlap({'charmed', 'frightened', 'poisoned'}):
                self._log.check(f'{self._name} has disadvantage on skill check because of a condition')
                adv -= 1
            return_val = self.char_stats.roll_skill(split_list[0], adv=adv)
        
        else:
            raise ValueError('arg name was not an ability or skill')

        # Check for bardic inspiration
        if ('bardic_inspiration' in self.char_conditions):
            cond_obj = self.char_conditions['bardic_inspiration']
            if not isinstance(cond_obj, combatCharacter.condition):
                raise TypeError(f"{self._name} had condition bardic_inspiration's value not a combatCharacter.condition obj")
            bi_roll = self._roll.roll_d_str(cond_obj._properties)
            self._log.action(f'{self._name} is using their bardic inspiration and rolled a {bi_roll}')
            return_val += bi_roll
            self.remove_condition('bardic_inspiration')

        return return_val
    # End char_roll_stat method

    ################################################################
    #============================ TURN ============================
    ################################################################

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
        self.char_resources.regular_action = 1
        self.char_resources.bonus_action = 1
        self.char_resources.reaction = 1
        self.char_resources.movement = float(self.char_stats.speed)

        # Restore class resources
        if ('rogue' in self.char_stats.class_level):
            self.char_resources.sneak_attack = 1

        # Restore unique resources
        if ('genies_wrath' in self.char_resources.miscellaneous):
            self.char_resources.miscellaneous['genies_wrath'] = 1

        self.check_all_conditions('1 sont')
        return self.char_resources.get_resources_for_round()
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

    ################################
    #========= SIMULATION =========
    ################################

    def update_act_bias(self, env_dict):
        """Will update the character's action biases due to their conditions, resources, and the environment. Will then return the order of actions that the character
        wants to do them.

        Args:
            - env_dict = (dict) The status of the combat environment

        Returns:
            (list of str) The order in which they want to take their actions. The default order is [free, movement, regular, bonus, special]. Any return value will be a
            permutation of these five elements.
        """
        if not isinstance(env_dict, dict):
            raise TypeError('arg env_dict must be a dict')

        return_val = ['free', 'movement', 'regular', 'bonus', 'special']
        update_dict = {}

        # Check conditions
        self.char_actions.update_act_bias_cond()
        # Check resources
        self.char_actions.update_act_bias_res()

        # Check bonus action buffs
        if (('cast_shillelagh' in self.char_actions.get_all_actions()) and ('shillelagh' not in self.char_conditions)):
            return_val = ['free', 'movement', 'bonus', 'regular', 'special']

        # Check environment
        if ('dying_pc' in env_dict):
            self._log.debugall(f'{self._name} may try to stabilize')
            update_dict.update({'stabilize': 16})
        else:
            self._log.debugall(f'{self._name} will no longer try to stabilize')
            update_dict.update({'stabilize': 0})

        if update_dict:
            self.char_actions.change_bias(update_dict)
        return return_val
    # End update_act_bias_res method

    def get_random_attack(self):
        """Gets a random attack of this character, weighted by the biases

        Args:
            No args

        Returns:
            (str) The name of an attack this character can do. Will return '' if no attack cannot be found
        """
        return_val = self._random_by_bias(self.char_attacks)
        if not return_val:
            self._log.debug(f'could not get a random attack for {self._name}')
            return ''
        return return_val
    # End get_random_attack method

    def get_random_action(self, act_type):
        """Gets a random action this character can do depending on the biases. If they have certain conditions, it will override the return value.

        Args:
            - act_type = (str) What action type to get. One of [regular, movement, bonus, reaction, free]

        Returns:
            - None if there are no actions available of that type, otherwise
            - (str) The name of an action
        """
        if (act_type not in ['regular', 'movement', 'bonus', 'reaction', 'free']):
            raise ValueError('arg act_type must be in [regular, movement, bonus, reaction, free]')

        def override_msg(msg):
            self._log.simulatn(f'{self._name} {msg}')
        # End override_msg inner function

        # Handle death and dying
        if ('death' in self.char_conditions):
            override_msg('will do nothing because they are dead')
            return None
        if ('dying' in self.char_conditions):
            if ('stabilized' in self.char_conditions):
                override_msg('will do nothing because they are dying but stabilized')
                return None
            if (act_type=='regular'):
                override_msg('will do a death save because they are dying')
                return 'death_save'
            override_msg('cannot do a {act_type} action because they are dying')
            return None
        
        # Handle conditions
        if ('unconscious' in self.char_conditions):
            override_msg('will do nothing because they are unconscious')
            return None
        if ('petrified' in self.char_conditions):
            override_msg('will do nothing because they are petrified')
            return None
        if ('paralyzed' in self.char_conditions):
            override_msg('will do nothing because they are paralyzed')
            return None
        if ('stunned' in self.char_conditions):
            override_msg('will do nothing because they are stunned')
            return None

        # Get regular action
        if (act_type=='regular'):
            if ('incapacitated' in self.char_conditions):
                override_msg('cannot do a regular action because they are incapacitated')
                return None
        # End regular branch

        # Get movement action
        if (act_type=='movement'):
            if ('prone' in self.char_conditions):
                self._log.simulatn(f'{self._name} can only crawl because they are prone')
                return 'crawl'
            if ('grappling' in self.char_conditions):
                self._log.simulatn(f'{self._name} can only move_while_grappling because they are grappling something')
                return 'move_while_grappling'
        # End movement branch

        # Get bonus action
        if (act_type=='bonus'):
            if ('incapacitated' in self.char_conditions):
                override_msg('cannot do a bonus action because they are incapacitated')
                return None
        # End bonus branch

        # Get reaction
        if (act_type=='reaction'):
            if ('incapacitated' in self.char_conditions):
                override_msg('cannot do a reaction because they are incapacitated')
                return None
        # End bonus branch

        return self.char_actions._get_random_action(act_type=act_type)
    # End get_random_action method
# End combatCharacter class

# eof