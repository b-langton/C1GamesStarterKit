import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    pmid_dict = {}
    ptop_left_dict = {}
    ptop_right_dict = {}
    last_adapted = ""
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.previous_game_states = {}
        self.filters_to_upgrade = []

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.previous_game_states[game_state.turn_number] = game_state

        self.v_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def v_strategy(self, game_state):
        x, y = map(int, [1,13])
        for unit in game_state.game_map[x,y]:
            if unit.health < 25:
                game_state.attempt_remove([1,13])
        x, y = map(int, [27,13])
        for unit in game_state.game_map[x,y]:
            if unit.health < 25:
                game_state.attempt_remove([27,13])

        for i in self.scored_on_locations:
            if i  == [0,13]: 
                game_state.attempt_spawn(FILTER, [0,13])
                game_state.attempt_upgrade([0,13])
        if game_state.turn_number == 0: 
            game_state.attempt_spawn(SCRAMBLER, [18,4])
        state = json.loads(game_state.serialized_string)
        p1units = state["p1Units"]
        self.build_defences(game_state)
        self.reinforce_defences(game_state)
        gamelib.debug_write(str(p1units))
        area = self.figure_out_attacked(game_state, p1units)
        self.adapt(area, game_state)
        self.build_offenses(game_state)
        if len(self.filters_to_upgrade) > 0:
            self.filters_to_upgrade.sort(key=lambda t: t[1])
            game_state.attempt_upgrade(self.filters_to_upgrade)

    def reinforce_defences(self, game_state): 
        locations = [[2, 11], [24, 11]]
        game_state.attempt_spawn(DESTRUCTOR, locations)
    
    def sum(self, d):
        sum1 = 0 
                
        for num in d.values():
            if num>0:
                sum1 += int(num)
        return sum1
    def figure_out_attacked(self, game_state, units): 
        temp_right = {}
        temp_mid = {}
        temp_left = {}
        for i, unit_types in enumerate(units):
            gamelib.debug_write("i:",i, "unit_types:", unit_types, )
            
            for uinfo in unit_types:
                
                sx, sy, shp = uinfo[:3]
                x, y = map(int, [sx, sy])
                hp = float(shp)
                # This depends on RM and UP always being the last types to be processed
                if x <= 9: 
                    if (x,y) in self.ptop_left_dict: 
                        self.ptop_left_dict[(x,y)] = self.ptop_left_dict[(x,y)] - hp
                    temp_left[(x,y)] = hp
                
                elif x> 9 and x <= 18:
                    if (x,y) in self.pmid_dict: 
                            self.pmid_dict[(x,y)] = self.pmid_dict[(x,y)] - hp
                    temp_mid[(x,y)] = hp

                else: 
                    if (x,y) in self.ptop_right_dict:
                        self.ptop_right_dict[(x,y)] = self.ptop_right_dict[(x,y)] - hp
                    temp_right[(x,y)] = hp
        sumleft = self.sum(self.ptop_left_dict)
        summid = self.sum(self.pmid_dict)
        sumright = self.sum(self.ptop_right_dict)

        self.pmid_dict = temp_mid
        self.ptop_right_dict = temp_right
        self.ptop_left_dict = temp_left
        gamelib.debug_write(temp_left.keys(), temp_left.values())
        gamelib.debug_write(sumleft, summid, sumright)

        if sumright > summid and sumright > sumleft and sumright > 0:
            gamelib.debug_write("top_right")
            self.last_adapted = "top_right"
            return "top_right"
        elif summid > sumleft and summid > sumright and summid > 0: 
            gamelib.debug_write("mid")
            self.last_adapted = "mid"
            return "mid"
        elif sumleft > 0:
            gamelib.debug_write("top_left")
            self.last_adapted = "top_left"
            return "top_left"
        return "no damage taken"
                     

       
    def adapt(self, area,  game_state): 
        if game_state.get_resource(CORES)<=5:
            return
        if area == "no damage taken":
            area = self.last_adapted
        if area == "top_left": 
            locations = [[2, 12], [4, 12], [1, 12], [4, 11], [5, 11], [7, 11], [6,12]]
            filter_locations = [[6,11], [7,10], [8,9]]
            
            game_state.attempt_spawn(DESTRUCTOR, locations, 2)
            for i in filter_locations: 
                game_state.attempt_spawn(FILTER, [i])
                game_state.attempt_upgrade([i])
        if area == "middle": 
            filter_locations = [[9,8], [10,7], [11,6], [12,5]]
            locations = [[7, 11], [8, 8], [9, 7], [10, 6], [11, 5], [12, 4]]
            game_state.attempt_spawn(DESTRUCTOR, locations, 2)
            game_state.attempt_upgrade(filter_locations)
        if area == "top_right": 
            filter_locations = [[24,13], [23,13], [22,11], [23,12], [21,10]]
            locations = [[23, 12], [24, 12], [23, 11], [22, 10], [22, 9]]
           
            for i in range(len(filter_locations)): 
                game_state.attempt_spawn(DESTRUCTOR, [locations[i]])
                game_state.attempt_spawn(FILTER, [filter_locations[i]])
                game_state.attempt_upgrade(filter_locations[i])

       

    def starter_strategy(self, game_state):
        
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defenses
        self.build_reactive_defense(game_state)

        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        locations = [[11, 11], [13,11], [8,10], [4,10], [19,11]]
        
       
    
        # Now let's analyze the enemy base to see where their defenses are concentrated.
        # If they have many units in the front we can build a line for our EMPs to attack them at long range.
        if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14,15]) > 15:
            self.emp_line_strategy(game_state)
        else:
            # They don't have many units in the front so lets figure out their least defended area and send Pings there.

            # Only spawn Ping's every other turn
            # Sending more at once is better since attacks can only hit a single ping at a time
            if game_state.turn_number % 2 == 1:
                # To simplify we will just check sending them from back left and right
                ping_spawn_location_options = [[13, 0], [14, 0], [2,11], [6,7], [22,8], [19,5]]
                best_location = self.least_damage_spawn_location(game_state, ping_spawn_location_options)
                game_state.attempt_spawn(PING, best_location, 1000)

            # Lastly, if we have spare cores, let's build some Encryptors to boost our Pings' health.
            encryptor_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
            game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)
        gamelib.debug_write(game_state._build_stack, game_state._deploy_stack)
      
    

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place destructors that attack enemy units
        destructor_locations = [[0, 13], [2, 12], [25, 12], [26, 12], [4, 12]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
        
        # Place filters in front of destructors to soak up damage for them
        filter_locations = [[1, 13], [25, 13], [26, 13], [27, 13], [5, 12], [6, 11], [25, 11], [7, 10], [24, 10], [8, 9], [23, 9], [9, 8], [22, 8], [10, 7], [21, 7], [11, 6], [20, 6], [12, 5], [19, 5], [13, 4], [18, 4], [14, 3], [17, 3], [15, 2], [16, 2]]
        if game_state.turn_number < 2:
            game_state.attempt_spawn(FILTER, filter_locations)
        else:
            # replace any deleted filters with upgraded filters
            for loc in filter_locations:
                if game_state.can_spawn(FILTER, loc):
                    self.filters_to_upgrade.append(loc)
                    game_state.attempt_spawn(FILTER, [loc])

        upgrade_locations = [[1, 13], [25, 13], [26, 13], [27, 13], [5, 12]]
      
        # upgrade filters so they soak more damage
        game_state.attempt_upgrade(upgrade_locations)

    def build_offenses(self, game_state):
        if game_state.turn_number == 0:
            game_state.attempt_spawn(SCRAMBLER, [[16, 2]])
            game_state.attempt_spawn(PING, [[16, 2]]*4)
            return
        
        if game_state.get_resource(BITS, 1) >= 10:
            game_state.attempt_spawn(SCRAMBLER, [[8, 5]])

        encryptors_locations = [[5, 10], [6, 10], [6, 9], [7, 9], [7, 8], [8, 8], [8, 7], [9, 7], [9, 6], [10, 6], [10, 5], [11, 5], [11, 4], [12, 4], ]

        for loc in encryptors_locations:
            if game_state.get_resource(CORES, 0) < 12:
                break
            game_state.attempt_spawn(ENCRYPTOR, [loc])
            game_state.attempt_upgrade([loc])

        bits = game_state.get_resource(BITS, 0)
        num_spawns = int(bits // 5)

        reqd_spawns = 4 if (game_state.turn_number > 30 and game_state.enemy_health > 25) else 2

        if num_spawns >= reqd_spawns:
            ping_locations = [[15, 1]]
            emp_locations = [[13, 0]]
            
            game_state.attempt_spawn(PING, ping_locations * 2 * num_spawns)
            game_state.attempt_spawn(EMP, emp_locations * num_spawns)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        if len(self.scored_on_locations)>0:
            location = self.scored_on_locations[-1]
            gamelib.debug_write("Attempting Build", location)
            # Build destructor one space above so that it doesn't block our own edge spawn locations
            build_locations = [[location[0], location[1]+1], [location[0] + 1, location[1]], [location[0]-1, location[1]]]
            filter_build_locations = [[i[0], i[1] + 1] for i in build_locations]
            game_state.attempt_spawn(DESTRUCTOR, build_locations)
            game_state.attempt_spawn(FILTER, filter_build_locations)

    def stall_with_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own firewalls 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining bits to spend lets send out scramblers randomly.
        while game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(SCRAMBLER, deploy_location)
            """
            We don't have to remove the location since multiple information 
            units can occupy the same space.
            """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        ##for x in range(27, 5, -1):
         ##   game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        if game_state.turn_number % 2 == 1:
         game_state.attempt_spawn(EMP, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if path != None:
                damage = 0
                for path_location in path:
                    # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                    damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
                damages.append(damage)
                possible_locations= game_state.game_map.get_locations_in_range(location, 3.5)
                for location_unit in possible_locations:
                    for unit in game_state.game_map[location_unit]:
                        damages.append(-1*gamelib.GameUnit(FILTER, game_state.config).damage_i)
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
