# Credit for this: Nicholas Swift
# as found at https://medium.com/@nicholas.w.swift/easy-a-star-pathfinding-7e6689c7f7b2

import numpy as np
import heapq
import chess
import math
import pygame
import time

def square_to_surface_coord(sq: chess.Square, surface_size=[5*12,5*8]):
    return (((sq % 8) + 2) * (surface_size[0] // 12), (sq // 8) * (surface_size[1] // 8))

class Node:
    """
    A node class for A* Pathfinding
    """

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position
    
    def __repr__(self):
      return f"{self.position} - g: {self.g} h: {self.h} f: {self.f}"

    # defining less than for purposes of heap queue
    def __lt__(self, other):
      return self.f < other.f
    
    # defining greater than for purposes of heap queue
    def __gt__(self, other):
      return self.f > other.f
    
def return_path(current_node):
    path = []
    current = current_node
    while current is not None:
        path.append(current.position)
        current = current.parent
    return path[::-1]  # Return reversed path

def is_within_bounds(target, surface_size=[5*12,5*8]):
        return 0 <= target[1] < len(surface_size[1]) and 0 <= target[0] < len(surface_size[0])

def convert_to_grid_coords(pos, surface_size, res):
    x = int((pos[0] * res) / surface_size[0])
    y = int((pos[1] * res) / surface_size[1])
    return [x, y]

def calculate_h_cost(pos1, pos2):
    """Calculate heuristic cost using octile distance"""
    dx = abs(pos1[0] - pos2[0])
    dy = abs(pos1[1] - pos2[1])
    return max(dx, dy) + (1.414 - 1) * min(dx, dy)

def astar(map, start_pos, end_pos, allow_diagonal_movement = True, surface_size=[5*12,5*8], res = 100):
    # Use sets for better performance
    closed_set = set()
    # Use dictionary to track g scores
    g_scores = {tuple(start_pos): 0}
    
    # Create start and end node
    start_node = Node(None, start_pos)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end_pos)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Heapify the open_list and Add the start node
    heapq.heapify(open_list) 
    heapq.heappush(open_list, start_node)

    # Adding a stop condition
    outer_iterations = 0
    max_iterations = 1000 #(len(maze[0]) * len(maze) // 2)

    # what squares do we search
    adjacent_squares = ((0, -1), (0, 1), (-1, 0), (1, 0),)
    if allow_diagonal_movement:
        adjacent_squares = ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1),)

    # Loop until you find the end
    while len(open_list) > 0:
        outer_iterations += 1

        if outer_iterations > max_iterations:
            # if we hit this point return the path such as it is
            # it will not contain the destination
            raise("giving up on pathfinding too many iterations")       
        
        # Get the current node
        current_node = heapq.heappop(open_list)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            return return_path(current_node)

        # Generate children
        children = []
        
        for new_position in adjacent_squares: # Adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if not (0 <= int((node_position[0]) / surface_size[0] * res) < len(map) and 0 <= int((node_position[1]) / surface_size[1] * res) < len(map[0])):
                continue

            # Make sure walkable terrain
            
            if map[int((node_position[0]) / surface_size[0] * res)][int((node_position[1]) / surface_size[1] * res)] == 1:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:
            # Child is on the closed list
            if tuple(child.position) in closed_set:
                continue

            # Add distance weights
            STRAIGHT_COST = 1.0
            DIAGONAL_COST = 1.414  # sqrt(2)
            
            # Calculate proper movement cost
            movement_cost = DIAGONAL_COST if abs(new_position[0]) + abs(new_position[1]) == 2 else STRAIGHT_COST
            child.g = current_node.g + movement_cost
            child.h = calculate_h_cost(child.position, end_node.position)
            child.f = child.g + child.h

            # Child is already in the open list
            if tuple(child.position) in g_scores and child.g > g_scores[tuple(child.position)]:
                continue

            # Add the child to the open list
            heapq.heappush(open_list, child)

            # Update g scores
            g_scores[tuple(child.position)] = child.g

            # Add to closed set
            closed_set.add(tuple(child.position))

    raise("Couldn't get a path to destination")

def map_generator(size_x=5*12, size_y=5*8, obstacle_radius=1.0, res=100, obstacles=[]):
    # Create a map with the specified resolution
    map = [[0 for x in range(res)] for y in range(res)]
    
    for obstacle in obstacles:
        # Convert real-world coordinates to map indices
        x_ind = int((obstacle[0]) / size_x * res)
        y_ind = int((obstacle[1]) / size_y * res)
        
        # Calculate the obstacle radius in map indices
        ob_radius_x = obstacle_radius / size_x * res
        ob_radius_y = obstacle_radius / size_y * res
        
        # Mark the area around the obstacle as occupied
        for j in range(-int(ob_radius_x), int(ob_radius_x) + 1):
            for k in range(-int(ob_radius_y), int(ob_radius_y) + 1):
                # Check if the index is within bounds and within the ellipse
                if (0 <= x_ind + j < res) and (0 <= y_ind + k < res):
                    if (j**2 / ob_radius_x**2 + k**2 / ob_radius_y**2) <= 1:
                        map[x_ind + j][y_ind + k] = 1  # Use y, x indexing
    return map

def path_converter_(path=list, size_x=5*12, size_y=5*8, res=100):
    converted_path = []
    grid_scale_x = size_x/res  # Amount of distance in real world per array element
    grid_scale_y = size_y/res  # Amount of distance in real world per array element
    
    for index in path:
        # Fix: Properly create tuple with parentheses around the entire expression
        converted_path.append(
            ((index[0] - int(res/2)) * -grid_scale_x, 
             (index[1] - int(res/2)) * -grid_scale_y)
        )
    
    return converted_path

def path_converter(path = list, size_x=5*12, size_y=5*8, res = 100):
    converted_path = []
    i = 0
    grid_scale_x = size_x/res  # Amount of distance in real world per array element
    grid_scale_y = size_y/res  # Amount of distance in real world per array element
    for index in path:
       converted_path.append( [(index[0] - int(res/2)) * grid_scale_x, (index[1] - int(res/2)) * grid_scale_y] )
       i = i + 1
    return converted_path

# Helper function to calculate the perpendicular distance of a point to a line segment
def perpendicular_distance(point, line_start, line_end):
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Line segment length
    segment_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    if segment_length == 0:
        return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    # Projection of point onto the line segment
    return abs((y2 - y1)*x0 - (x2 - x1)*y0 + x2*y1 - y2*x1) / segment_length

# Ramer-Douglas-Peucker line simplification algorithm
def simplify_path(points, epsilon=1.0):
    """
    Simplifies a given path by removing intermediate points in straight segments.
    
    Parameters:
    - points (list of tuples): List of (x, y) coordinates representing the path.
    - epsilon (float): Sensitivity threshold to control the simplification. Lower values mean stricter straightness requirement.
    
    Returns:
    - list of tuples: Simplified list of (x, y) points.
    """
    # If path has less than 3 points, no simplification can be done
    if (points == None):
       return None
    else:
        if len(points) < 3:
            return points
   
    
    
    # Find the point with the maximum distance from the line formed by the first and last points
    start, end = points[0], points[-1]
    max_distance = 0
    index = -1
    
    for i in range(1, len(points) - 1):
        dist = perpendicular_distance(points[i], start, end)
        if dist > max_distance:
            max_distance = dist
            index = i
    
    # If the maximum distance is greater than epsilon, recursively simplify
    if max_distance > epsilon:
        # Recursively simplify the two halves
        left_simplified = simplify_path(points[:index+1], epsilon)
        right_simplified = simplify_path(points[index:], epsilon)
        
        # Merge results, excluding the duplicate point at the junction
        return left_simplified[:-1] + right_simplified
    else:
        # If no point is far enough, return the segment with just start and end points
        return [start, end]

    
def astar_activate(pose = [], goal = [], radius = float,  obstacle_list = list ,print_map= False):
    
    
    map = map_generator(size_x = 5*12, size_y = 5*8,obstacle_radius = radius, res=100, obstacles = obstacle_list)
    if print_map:
        for row in map:
            for i in row:
                if i==0: print(' ',end= '') 
                else: print('X',end= '')
            print("", end= '\n')
    start = pose
    end = goal
    #print("pose =", start[0],",", start[1])
    #print("goal =", end[0],",", end[1])
    
    path = astar(map, start, end)
    path = simplify_path(path, 0.5)
    return path


