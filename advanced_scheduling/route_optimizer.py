import pandas as pd
import numpy as np
from datetime import datetime
import logging
import random

from deap import base, creator, tools, algorithms

# Optionally try importing DB if needed, though route_optimizer heavily relies on passed df
try:
    from utils.db_utils import db
except ImportError:
    pass

# Global summary to retain GA results
_optimization_summary = {
    'generations_taken': 0,
    'fitness_score': 0.0,
    'best_assignments': None
}

def get_optimization_summary():
    """
    Returns the routing optimization execution results, including:
    - best route assignments
    - fitness score
    - generations taken
    """
    return _optimization_summary

# Setup DEAP components safely 
if not hasattr(creator, "RouteFitnessMax"):
    creator.create("RouteFitnessMax", base.Fitness, weights=(1.0,))
if not hasattr(creator, "RouteIndividual"):
    creator.create("RouteIndividual", list, fitness=creator.RouteFitnessMax)

def evaluate_route_assignment(individual, df, red_slots, blue_slots, green_slots):
    """
    Fitness function to evaluate an ordered list of train-to-route assignments.
    
    Objectives handled:
    - Maximize fleet health assigned to demanding routes.
    - Minimize deadhead runs by penalizing assignment to a mismatching home depot.
    """
    score = 0
    
    def calc_deadhead_penalty(train_idx, expected_depot):
        depot = df.iloc[train_idx].get('home_depot', 'System')
        if pd.isna(depot) or depot == 'System': 
            return -5 # Generic penalty
        return 0 if expected_depot in str(depot) else -15

    # Evaluate Red Line (High demand highest weight)
    ptr = 0
    for _ in range(red_slots):
        idx = individual[ptr]
        health = df.iloc[idx].get('health_score', 85)
        score += health * 1.5 
        score += calc_deadhead_penalty(idx, 'Miyapur')
        ptr += 1
        
    # Evaluate Blue Line (Medium demand)
    for _ in range(blue_slots):
        idx = individual[ptr]
        health = df.iloc[idx].get('health_score', 85)
        score += health * 1.2 
        score += calc_deadhead_penalty(idx, 'Uppal')
        ptr += 1
        
    # Evaluate Green Line (Lower demand)
    for _ in range(green_slots):
        idx = individual[ptr]
        health = df.iloc[idx].get('health_score', 85)
        score += health * 1.0 
        score += calc_deadhead_penalty(idx, 'Secunderabad')
        ptr += 1
        
    # Penalize hoarding good trains in Standby
    while ptr < len(individual):
        idx = individual[ptr]
        health = df.iloc[idx].get('health_score', 85)
        score += health * 0.1
        ptr += 1

    return (score,)

def run_route_optimizer_ga(df, N, red_slots, blue_slots, green_slots):
    """
    Executes the GA using Tournament Selection, Ordered Crossover (OX), and Swap Mutation.
    """
    toolbox = base.Toolbox()
    
    # Gene generator: random permutation of indices
    toolbox.register("indices", random.sample, range(N), N)
    
    # Chromosome setup
    toolbox.register("individual", tools.initIterate, creator.RouteIndividual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Evaluate function 
    toolbox.register("evaluate", evaluate_route_assignment, df=df, red_slots=red_slots, blue_slots=blue_slots, green_slots=green_slots)
    
    # GA Operators (OX and tournament selection as requested)
    toolbox.register("mate", tools.cxOrdered)
    
    # Swap mutation for sequences
    def mutSwap(individual, indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                swap_idx = random.randint(0, len(individual) - 1)
                individual[i], individual[swap_idx] = individual[swap_idx], individual[i]
        return individual,
        
    toolbox.register("mutate", mutSwap, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)
    
    pop = toolbox.population(n=40)
    hof = tools.HallOfFame(1)
    
    # Termination conditions: 150 gens or plateau
    max_gens = 150
    patience = 20
    best_fitness = -float('inf')
    plateau_count = 0
    gens_run = 0
    
    # Init pop eval
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        
    for gen in range(max_gens):
        gens_run += 1
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))
        
        # Apply OX Crossover
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
                
        # Apply Swap Mutation
        for mutant in offspring:
            if random.random() < 0.2:
                toolbox.mutate(mutant)
                del mutant.fitness.values
                
        # Re-evaluate logic
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            
        pop[:] = offspring
        hof.update(pop)
        
        # Check plateau for early termination
        current_best = hof[0].fitness.values[0]
        if current_best > best_fitness:
            best_fitness = current_best
            plateau_count = 0
        else:
            plateau_count += 1
            
        if plateau_count >= patience:
            break
            
    return hof[0], best_fitness, gens_run

def assign_trains_to_routes(available_trains_df, date):
    """
    Assigns trains to HMRL routes using a GA-based Route Optimizer.
    Balances load and ensures optimal fleet health per demand dynamically.
    """
    logging.info("Starting GA-based HMRL route assignment engine")
    
    df = available_trains_df.copy()
    if df.empty:
        return pd.DataFrame()
        
    # Safeguard standard column presence for GA operations
    if 'health_score' not in df.columns:
        df['health_score'] = df.get('Priority_Score', 85)
    if 'year_of_manufacture' not in df.columns:
        df['year_of_manufacture'] = 2018
        
    req_red = 25
    req_blue = 23
    req_green = 12
    total_req = req_red + req_blue + req_green
    
    df.reset_index(drop=True, inplace=True)
    N = len(df)
    
    # Calculate balanced load. Hard boundaries preventing overloading of 1 single line
    if N < total_req:
        red_slots = int((req_red / total_req) * N)
        blue_slots = int((req_blue / total_req) * N)
        green_slots = N - red_slots - blue_slots
    else:
        red_slots = req_red
        blue_slots = req_blue
        green_slots = req_green
        
    best_ind, best_fit, gens_taken = run_route_optimizer_ga(df, N, red_slots, blue_slots, green_slots)
    
    assigned_data = []
    ptr = 0
    
    # Unpack best individual into explicit assignments
    for _ in range(red_slots):
        row = df.iloc[best_ind[ptr]]
        assigned_data.append({
            'train_id': row.get('train_id', row.get('Train_ID', 'UNKNOWN')),
            'assigned_route': 'Red Line',
            'home_depot': 'Miyapur',
            'route_priority': 1,
            'assignment_reason': 'High demand route assignment (GA selected)',
            'backup_route': 'Blue Line',
            'estimated_daily_km': 29.87 * 10
        })
        ptr += 1
        
    for _ in range(blue_slots):
        row = df.iloc[best_ind[ptr]]
        assigned_data.append({
            'train_id': row.get('train_id', row.get('Train_ID', 'UNKNOWN')),
            'assigned_route': 'Blue Line',
            'home_depot': 'Uppal',
            'route_priority': 2,
            'assignment_reason': 'Punctuality focused assignment (GA selected)',
            'backup_route': 'Green Line',
            'estimated_daily_km': 28.0 * 10
        })
        ptr += 1
        
    for _ in range(green_slots):
        row = df.iloc[best_ind[ptr]]
        assigned_data.append({
            'train_id': row.get('train_id', row.get('Train_ID', 'UNKNOWN')),
            'assigned_route': 'Green Line',
            'home_depot': 'Secunderabad',
            'route_priority': 3,
            'assignment_reason': 'Secondary density assignment (GA selected)',
            'backup_route': 'Red Line',
            'estimated_daily_km': 9.6 * 14
        })
        ptr += 1
        
    # Unpack remaining as Standby
    while ptr < N:
        row = df.iloc[best_ind[ptr]]
        assigned_data.append({
            'train_id': row.get('train_id', row.get('Train_ID', 'UNKNOWN')),
            'assigned_route': 'Standby',
            'home_depot': 'Ameerpet (Interchange)',
            'route_priority': 0,
            'assignment_reason': 'Available for crisis management',
            'backup_route': 'Any',
            'estimated_daily_km': 0
        })
        ptr += 1

    # Keep historical states properly encapsulated by fetching global directly
    global _optimization_summary
    result_df = pd.DataFrame(assigned_data)
    _optimization_summary['generations_taken'] = gens_taken
    _optimization_summary['fitness_score'] = best_fit
    _optimization_summary['best_assignments'] = result_df
        
    return result_df

def optimize_route_distribution(schedule_df):
    """Rebalances route allocations to meet minimum operational density"""
    route_counts = schedule_df['assigned_route'].value_counts().to_dict()
    
    ideal = {'Red Line': 25, 'Blue Line': 23, 'Green Line': 12}
    recommendations = []
    
    for route, required in ideal.items():
        current = route_counts.get(route, 0)
        if current < required:
            recommendations.append(f"DEFICIT on {route}: Need {required-current} more trains. Pull from Standby if available.")
        elif current > required:
            recommendations.append(f"SURPLUS on {route}: {current-required} trains can be rested.")
            
    if not recommendations:
        recommendations.append("Fleet perfectly balanced across all 3 routes.")
        
    return schedule_df, recommendations

def calculate_route_capacity(route_name, available_trains):
    """Determine dynamic route capacity and shortfall/surplus parameters."""
    specs = {
        'Red Line': {'len': 29.87, 'avg_speed': 35, 'headway': 3, 'req': 25},
        'Blue Line': {'len': 28.0, 'avg_speed': 35, 'headway': 3, 'req': 23},
        'Green Line': {'len': 9.6, 'avg_speed': 35, 'headway': 5, 'req': 12}
    }
    spec = specs.get(route_name)
    if not spec:
        return 0, 0
    
    capacity_pct = min(100.0, (available_trains / spec['req']) * 100)
    deficit = available_trains - spec['req']
    return round(capacity_pct, 1), deficit
