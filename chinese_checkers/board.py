# Build board
import pygame
from pygame.locals import *
import time
from math import sin, cos, pi, sqrt
from AIs import *

# https://www.redblobgames.com/grids/hexagons/
# 233.8268590217984

# read Q learning, Markov Decision Process
class Board():
    def __init__(self, mode = ''):
        self.mode = mode
        self.going = True
        self.hex_size = 20
        self.hex_height = 2 * self.hex_size
        self.hex_width = sqrt(3) * self.hex_size
        self.hex_half_width = self.hex_width * 0.5
        self.num_cols = 17 # x dir vvv
        self.num_rows = 13 # y dir >>> 
        self.screen_height = int((0.75 * self.num_cols + 0.25) * self.hex_height)
        self.screen_width = int((0.5 + self.num_rows) * self.hex_width)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Chinese Checkers")
        self.neighbors_dir = [(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)] # clockwise from NE
        self.coord_dict = {} # axial coord is key to center of hex
        self.coord_dict[(0, 0)] = self.grid_center() # center
        self.set_up_dict()
        self.player_dict = {
            'p1': sorted([(4, -8), (3, -7), (4, -7), (2, -6), (3, -6), (4, -6), (1, -5), (2, -5), (3, -5), (4, -5)]),
            'p2': sorted([(-4, 8), (-3, 7), (-4, 7), (-2, 6), (-3, 6), (-4, 6), (-1, 5), (-2, 5), (-3, 5), (-4, 5)])
        }
        self.player_colors = {
            'p1' : (255, 0, 0),# red
            'p2' : (255, 255, 0) # yellow
        }
        self.occupied = {}
        self.displayed_opts = []
        self.piece_selected = 0
        self.moving = False
        self.jumping = False
        self.init_board()
        self.j_options = []
        self.n_options = []
        self.state = 'fresh'
        self.move_made = False

    def set_up_dict(self):
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
    
    def grid_center(self):
        x = self.num_cols/2
        y = self.num_rows/2
        return (self.hex_height * (0.5 + (0.75 * x)), ((x % 2) * self.hex_half_width) + ((y * 2 + 1) * self.hex_half_width))

    # generator to get the six points around center of hexagon
    def hex_points(self, x, y):
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = pi/180 * angle_deg
            yield y + self.hex_size * cos(angle_rad), x + self.hex_size * sin(angle_rad)                
    
    # generator to get all centers 
    def hex_centers(self):
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                # ((y%2) * self.hex_half_width) => even rows start at edge, odd start at with half width ahead
                yield self.hex_height * (0.5 + (0.75 * x)), ((x % 2) * self.hex_half_width) + ((y * 2 + 1) * self.hex_half_width)

    def pygame_colours(self):
        while True:
            yield 255, 0, 0 # red
            yield 255, 255, 0 # yellow
            yield 0, 0, 255 # blue
            yield 0, 255, 0 # green
    
    # pixel to q, r coordinates
    def pixel_to_axial(self, point):
        x = point[1] - (self.screen_height/2.0)
        y = point[0] - (self.screen_width/2.0)
        
        q = (-1./3 * x + 1/sqrt(3) * y) / self.hex_size
        r = (2./3 * x) / self.hex_size
        
        return self.hex_round((q, r))

    # q, r coordinates to pixel x, y
    def axial_to_pixel(self, coord):
        q = coord[0]
        r = coord[1]

        x = self.hex_size * (3./2 * r)       
        y = self.hex_size * (sqrt(3) * q  +  sqrt(3)/2 * r)

        c_q, c_r = self.grid_center()

        return (c_q + x, c_r + y)

    # returns one step moves
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

    # only returns jumping options
    def get_j_opts(self, axial, prev_piece = ()):
        q = axial[0]
        r = axial[1]
            
        options = []

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

        return options

    # currently handles 2 players, and red as human and yellow as AI if AI 
    def handle_key_event(self, event):
        position = event.pos
        q, r = self.pixel_to_axial(position)
        
        if self.state == 'first':
            if (q, r) in self.n_options:        
                for opt in self.j_options + self.n_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 0), list(self.hex_points(x, y)))    
                self.make_move(self.piece_selected, (q, r))
                self.state = 'fresh'
                self.move_made = True
                
            elif (q, r) in self.j_options:
                for opt in self.j_options + self.n_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 0), list(self.hex_points(x, y)))    
                self.make_move(self.piece_selected, (q, r))    
                self.move_made = True                            
                self.j_options = self.get_j_opts((q, r), self.piece_selected)
                self.n_options = []

                if self.j_options:
                    self.state = 'jump'
                    self.piece_selected = (q, r)
                else:
                    self.state = 'fresh'

                for opt in self.j_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 255), list(self.hex_points(x, y)))
            else:
                self.state = 'fresh'
                for opt in self.j_options + self.n_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 0), list(self.hex_points(x, y)))    
            
        elif self.state == 'jump': 
            if (q,r) in self.j_options:
                for opt in self.j_options + self.n_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 0), list(self.hex_points(x, y)))    
                self.make_move(self.piece_selected, (q, r))  
                self.move_made = True                              
                self.j_options = self.get_j_opts((q, r), self.piece_selected)
                self.n_options = []
                if self.j_options:
                    self.state = 'jump'
                    self.piece_selected = (q, r)
                else:
                    self.state = 'fresh'
                for opt in self.j_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 255), list(self.hex_points(x, y)))
            else:
                self.state = 'fresh'
                for opt in self.j_options + self.n_options:
                    x, y = self.coord_dict[opt]
                    pygame.draw.polygon(self.screen, (0, 0, 0), list(self.hex_points(x, y)))    
   
        else:
            if self.move_made:
                self.move_made = False
                if self.mode == 'AI':
                    ai = AI(self.occupied)
                    piece, move = ai.best_move()
                    self.make_move(piece, move)  
            if (q, r) in self.coord_dict:
                if (q, r) in self.occupied:
                    self.n_options = self.get_n_opts((q, r))
                    self.j_options = self.get_j_opts((q, r))
                    if self.j_options or self.n_options:
                        self.state = 'first'
                        self.piece_selected = (q, r)
                    for opt in self.j_options + self.n_options:
                        x, y = self.coord_dict[opt]
                        self.displayed_opts.append((x,y))
                        pygame.draw.polygon(self.screen, (0, 0, 255), list(self.hex_points(x, y)))          

    # moves piece to axial and cleans up board and occupied dict
    def make_move(self, piece, axial):
        x, y = self.coord_dict[piece]
        color = self.player_colors[self.occupied[piece]]
        pygame.draw.polygon(self.screen, (0, 0, 0), list(self.hex_points(x, y)))
        x, y = self.coord_dict[axial]
        pygame.draw.polygon(self.screen, color, list(self.hex_points(x, y)))
        self.occupied[axial] = self.occupied[piece]
        del self.occupied[piece]
        winner = self.check_win()
        if winner:
            print("WINNER: " +  str(winner))
            self.going = False

    # draw coordinates on board
    def draw_coord(self):
        myfont = pygame.font.SysFont("monospace", 10)
        
        for key in self.coord_dict.keys():
            x, y = self.coord_dict[key]
            label = myfont.render(str(key[0]) + " " + str(key[1]), 1, (255,255,255))
            self.screen.blit(label, (y - self.hex_half_width + 5, x - 5))
    
    def check_win(self):
        # get all occupied spots
        current_board = {
            'p1': [],
            'p2': []    
        }
        for key in self.occupied:
            current_board[self.occupied[key]].append(key)

        # check if any player has taken over other's spot
        #self.player_dict = {
        #    'p1': [(4, -8), (3, -7), (4, -7), (2, -6), (3, -6), (4, -6), (1, -5), (2, -5), (3, -5), (4, -5)],
        #    'p2': [(-4, 8), (-3, 7), (-4, 7), (-2, 6), (-3, 6), (-4, 6), (-1, 5), (-2, 5), (-3, 5), (-4, 5)]
        #}
        if sorted(current_board['p1']) == self.player_dict['p2']:
            return 'p1'
        if sorted(current_board['p2']) == self.player_dict['p1']:
            return 'p2'
        
        return ''

    # set up pieces on board and set up occupied dict
    def init_board(self):
        for key in self.player_dict.keys():
            colour = self.player_colors[key]
            for piece in self.player_dict[key]:
                self.occupied[piece] = key
                x, y = self.coord_dict[piece]
                pygame.draw.polygon(self.screen, colour, list(self.hex_points(x, y)))


    def update(self):
        for key in self.coord_dict.keys():
            x, y = self.coord_dict[key]
            pygame.draw.polygon(self.screen, (255,255,255), list(self.hex_points(x,y)), 1)
        
        for event in pygame.event.get():
                if event.type == KEYDOWN:
                    self.going = False
                if event.type == QUIT:
                    self.going = False
                if event.type == MOUSEBUTTONDOWN:
                    self.handle_key_event(event)
                    
        pygame.display.update()

    def hex_round(self, hex):
        q, r =  self.cube_to_axial(self.cube_round(self.axial_to_cube(hex)))
        return (int(q), int(r))

    def cube_round(self, cube):
        rx = round(cube[0])
        ry = round(cube[1])
        rz = round(cube[2])

        x_diff = abs(rx - cube[0])
        y_diff = abs(ry - cube[1])
        z_diff = abs(rz - cube[2])

        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry-rz
        elif y_diff > z_diff:
            ry = -rx-rz
        else:
            rz = -rx-ry

        return (rx, ry, rz)

    def cube_to_axial(self, cube):
        q = cube[0]
        r = cube[2]
        return (q, r)

    def axial_to_cube(self, hex):
        x = hex[0]
        z = hex[1]
        y = -x-z
        return (x, y, z)