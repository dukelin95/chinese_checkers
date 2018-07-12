import random
from math import sin, cos, pi, sqrt

# closest to self.end
# amount to jump

class AI():
    def __init__(self, occupied):
        self.occupied = occupied
        self.hex_size = 20
        self.hex_height = 2 * self.hex_size
        self.hex_width = sqrt(3) * self.hex_size
        self.hex_half_width = self.hex_width * 0.5
        self.num_cols = 17 # x dir vvv
        self.num_rows = 13 # y dir >>> 
        self.screen_height = int((0.75 * self.num_cols + 0.25) * self.hex_height)
        self.screen_width = int((0.5 + self.num_rows) * self.hex_width)
        self.neighbors_dir = [(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)]
        self.player_loc = {
            'p1': [],
            'p2': []    
        }
        self.player_dict = {
            'p1': [(4, -8), (3, -7), (4, -7), (2, -6), (3, -6), (4, -6), (1, -5), (2, -5), (3, -5), (4, -5)],
            'p2': [(-4, 8), (-3, 7), (-4, 7), (-2, 6), (-3, 6), (-4, 6), (-1, 5), (-2, 5), (-3, 5), (-4, 5)]
        }
        self.coord_dict = {}
        self.coord_dict[(0, 0)] = self.grid_center()
        self.set_up_dict()
        self.end = (4, -8)

    #TODO
    # go towards self.end
    def best_move(self):
        # pick random piece from p2
        moves = []
        count = []
        for piece in self.player_loc['p2']:
            options = self.get_j_opts(piece) + self.get_n_opts(piece)
            if options:
                moves.append((self.get_best_option(piece, options), piece))
        
        choice = sorted(moves).pop()
        #print choice
        #print '\n'
        #self.player_loc['p2'].append(choice)
        #self.player_loc['p2'].remove(piece)
        return choice[1], choice[0][1]

    def get_best_option(self, piece, options):
        max = (0, (99,99))
        for opt in options:
            dist = self.get_distance(opt, piece) + (15 - (self.get_distance(opt, self.end)))
            if dist > max[0]:
                max = (dist, opt)
        return max

    def grid_center(self):
        x = self.num_cols/2
        y = self.num_rows/2
        return (self.hex_height * (0.5 + (0.75 * x)), ((x % 2) * self.hex_half_width) + ((y * 2 + 1) * self.hex_half_width))

    def get_distance(self, piece, spot):
        ac = self.axial_to_cube(piece)
        bc = self.axial_to_cube(spot)
        return self.cube_distance(ac, bc)

    def set_up_dict(self):
        #set up player dict
        for key in self.occupied:
            self.player_loc[self.occupied[key]].append(key)

        new_hexes = [(0, 0)]
        while new_hexes:
            key = new_hexes.pop(0)
            px_q, px_r = self.coord_dict[key]
            for (q, r) in self.neighbors_dir:
                adj_q, adj_r = (key[0] + q, key[1] + r)
                if not ((adj_q, adj_r) in self.coord_dict):
                    if (abs(adj_q) < 9 and abs(adj_r) < 9):
                        adj_px_q, adj_px_r = self.axial_to_pixel((adj_q, adj_r))
                        self.coord_dict[(adj_q, adj_r)] = (adj_px_q, adj_px_r)
                        new_hexes.append((adj_q, adj_r))

        # self.neighbors_dir = [(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)]
        directions = [(1, -1), (-1, 0), (0, -1)]
        new_hexes = [(0, -5)]
        self.del_grid(directions, new_hexes)

        directions = [(1, -1), (0, -1), (1, 0)]
        new_hexes = [(5, -5)]
        self.del_grid(directions, new_hexes)

        directions = [(-1, 1), (0, -1), (-1, 0)]
        new_hexes = [(-5, 0)]
        self.del_grid(directions, new_hexes)

        directions = [(1, -1), (0, 1), (1, 0)]
        new_hexes = [(5, 0)]
        self.del_grid(directions, new_hexes)

        directions = [(-1, 1), (0, 1), (-1, 0)]
        new_hexes = [(-5, 5)]
        self.del_grid(directions, new_hexes)

        directions = [(-1, 1), (0, 1), (1, 0)]
        new_hexes = [(0, 5)]
        self.del_grid(directions, new_hexes)

    def get_n_opts(self, axial):
        q = axial[0]
        r = axial[1]
            
        options = []
        for dir in self.neighbors_dir:
            neighbor = (q, r)
            neighbor = (neighbor[0] + dir[0], neighbor[1] + dir[1])
            if not neighbor in self.occupied:
                if neighbor in self.coord_dict:
                    options.append(neighbor)
    
        return options

    def get_j_opts(self, axial, prev_piece = (), explored = []):
        q = axial[0]
        r = axial[1]
            
        options = []
        final = []

        for dir in self.neighbors_dir:
            neighbor = (q, r)
            for i in range(1,7):
                neighbor = (neighbor[0] + dir[0], neighbor[1] + dir[1])
                if neighbor in self.occupied:
                    move = (q + (i * 2 * dir[0]), r + (i * 2 * dir[1]))
                    if not move in self.occupied and move in self.coord_dict:
                        able = True
                        while not neighbor == move:
                            neighbor = (neighbor[0] + dir[0], neighbor[1] + dir[1])
                            if neighbor in self.occupied:
                                able = False
                        if able:
                            options.append(move)
                    break

        if prev_piece in options:
            options.remove(prev_piece)

        explored.append(axial)
        if options:
            final = final + options
            for opt in options:
                if not opt in explored:
                    final = final + self.get_j_opts(opt, (q,r), final)
            return final
        else:
            return options

    def del_grid(self, dirs, hexes):
        new_hexes = hexes
        directions = dirs
        while new_hexes:
            start = new_hexes.pop()
            for dir in directions:
                new_key = (start[0] + dir[0], start[1] + dir[1])
                if new_key in self.coord_dict:
                    new_hexes.append(new_key)
            if start in self.coord_dict:
                del self.coord_dict[start]     

    def axial_to_pixel(self, coord):
        q = coord[0]
        r = coord[1]

        x = self.hex_size * (3./2 * r)       
        y = self.hex_size * (sqrt(3) * q  +  sqrt(3)/2 * r)

        c_q, c_r = self.grid_center()

        return (c_q + x, c_r + y)
    
    def axial_to_cube(self, hex):
        x = hex[0]
        z = hex[1]
        y = -x-z
        return (x, y, z)
    
    def cube_distance(self, a, b):
        return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) / 2