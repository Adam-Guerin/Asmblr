"""
Bio-inspired Computing Algorithms for Asmblr
Nature-inspired optimization and computation methods
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import numpy as np
import random
import math
from abc import ABC, abstractmethod
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class BioAlgorithm(Enum):
    """Bio-inspired algorithm types"""
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM_OPTIMIZATION = "particle_swarm_optimization"
    ANT_COLONY_OPTIMIZATION = "ant_colony_optimization"
    ARTIFICIAL_BEE_COLONY = "artificial_bee_colony"
    FIREFLY_ALGORITHM = "firefly_algorithm"
    BAT_ALGORITHM = "bat_algorithm"
    CUCKOO_SEARCH = "cuckoo_search"
    GRAVITATIONAL_SEARCH = "gravitational_search"
    HARMONY_SEARCH = "harmony_search"
    NEURAL_NETWORK = "neural_network"
    CELLULAR_AUTOMATA = "cellular_automata"
    L_SYSTEM = "l_system"

class OptimizationType(Enum):
    """Optimization problem types"""
    MINIMIZATION = "minimization"
    MAXIMIZATION = "maximization"
    MULTI_OBJECTIVE = "multi_objective"
    CONSTRAINED = "constrained"
    DYNAMIC = "dynamic"

class ProblemDomain(Enum):
    """Problem domains"""
    ENGINEERING = "engineering"
    FINANCE = "finance"
    LOGISTICS = "logistics"
    SCHEDULING = "scheduling"
    DESIGN = "design"
    ROUTING = "routing"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    PREDICTION = "prediction"

@dataclass
class Individual:
    """Individual in population"""
    id: str
    genes: List[float]
    fitness: float
    age: int
    generation: int
    parent_ids: List[str]
    mutation_rate: float
    crossover_rate: float

@dataclass
class Particle:
    """Particle in swarm"""
    id: str
    position: List[float]
    velocity: List[float]
    personal_best_position: List[float]
    personal_best_fitness: float
    global_best_fitness: float
    inertia_weight: float
    cognitive_coefficient: float
    social_coefficient: float

@dataclass
class Ant:
    """Ant in colony"""
    id: str
    position: List[float]
    path: List[List[float]]
    pheromone_level: float
    distance_traveled: float
    tour_length: float

@dataclass
class Bee:
    """Bee in colony"""
    id: str
    position: List[float]
    nectar_amount: float
    waggle_dance_duration: float
    exploration_rate: float
    exploitation_rate: float

@dataclass
class Firefly:
    """Firefly in swarm"""
    id: str
    position: List[float]
    light_intensity: float
    absorption_coefficient: float
    randomization_parameter: float

@dataclass
class Harmony:
    """Harmony in memory"""
    id: str
    notes: List[float]
    fitness: float
    pitch_adjustment_rate: float
    bandwidth_adjustment_rate: float
    consideration_rate: float

@dataclass
class OptimizationProblem:
    """Optimization problem definition"""
    id: str
    name: str
    domain: ProblemDomain
    type: OptimizationType
    objective_function: str
    dimensions: int
    bounds: List[Tuple[float, float]]
    constraints: List[str]
    parameters: Dict[str, Any]
    created_at: datetime

class BioInspiredOptimizer(ABC):
    """Base class for bio-inspired optimizers"""
    
    def __init__(self, problem: OptimizationProblem):
        self.problem = problem
        self.population_size = problem.parameters.get("population_size", 50)
        self.max_generations = problem.parameters.get("max_generations", 100)
        self.convergence_threshold = problem.parameters.get("convergence_threshold", 1e-6)
        self.current_generation = 0
        self.best_solution = None
        self.fitness_history = []
        self.convergence_history = []
    
    @abstractmethod
    async def optimize(self) -> Dict[str, Any]:
        """Run optimization"""
        pass
    
    @abstractmethod
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness of solution"""
        pass
    
    def is_converged(self) -> bool:
        """Check convergence"""
        if len(self.fitness_history) < 10:
            return False
        
        recent_fitness = self.fitness_history[-10:]
        fitness_std = np.std(recent_fitness)
        
        return fitness_std < self.convergence_threshold

class GeneticAlgorithm(BioInspiredOptimizer):
    """Genetic Algorithm optimizer"""
    
    def __init__(self, problem: OptimizationProblem):
        super().__init__(problem)
        self.mutation_rate = problem.parameters.get("mutation_rate", 0.1)
        self.crossover_rate = problem.parameters.get("crossover_rate", 0.8)
        self.elitism_rate = problem.parameters.get("elitism_rate", 0.1)
        self.tournament_size = problem.parameters.get("tournament_size", 3)
        
        self.population = []
        self.offspring = []
    
    async def optimize(self) -> Dict[str, Any]:
        """Run genetic algorithm optimization"""
        try:
            # Initialize population
            self._initialize_population()
            
            # Evolution loop
            for generation in range(self.max_generations):
                self.current_generation = generation
                
                # Evaluate fitness
                for individual in self.population:
                    individual.fitness = self.evaluate_fitness(individual.genes)
                
                # Sort by fitness
                self.population.sort(key=lambda x: x.fitness, reverse=True)
                
                # Record best fitness
                best_fitness = self.population[0].fitness
                self.fitness_history.append(best_fitness)
                
                # Check convergence
                if self.is_converged():
                    logger.info(f"GA converged at generation {generation}")
                    break
                
                # Selection
                selected = self._selection()
                
                # Crossover
                self.offspring = self._crossover(selected)
                
                # Mutation
                self._mutation(self.offspring)
                
                # Evaluate offspring
                for individual in self.offspring:
                    individual.fitness = self.evaluate_fitness(individual.genes)
                
                # Replacement
                self._replacement()
                
                # Update generation
                for individual in self.population:
                    individual.age += 1
                    individual.generation = generation
            
            # Get best solution
            self.best_solution = self.population[0]
            
            return {
                "algorithm": "Genetic Algorithm",
                "best_solution": {
                    "genes": self.best_solution.genes,
                    "fitness": self.best_solution.fitness,
                    "generation": self.best_solution.generation
                },
                "generations": self.current_generation + 1,
                "fitness_history": self.fitness_history,
                "converged": self.is_converged()
            }
            
        except Exception as e:
            logger.error(f"Error in genetic algorithm: {e}")
            raise
    
    def _initialize_population(self):
        """Initialize random population"""
        self.population = []
        
        for i in range(self.population_size):
            genes = []
            for j, (lower, upper) in enumerate(self.problem.bounds):
                genes.append(random.uniform(lower, upper))
            
            individual = Individual(
                id=str(uuid.uuid4()),
                genes=genes,
                fitness=0.0,
                age=0,
                generation=0,
                parent_ids=[],
                mutation_rate=self.mutation_rate,
                crossover_rate=self.crossover_rate
            )
            
            self.population.append(individual)
    
    def _selection(self) -> List[Individual]:
        """Tournament selection"""
        selected = []
        
        # Elitism - keep best individuals
        elite_count = int(self.population_size * self.elitism_rate)
        selected.extend(self.population[:elite_count])
        
        # Tournament selection for remaining
        while len(selected) < self.population_size:
            tournament = random.sample(self.population, self.tournament_size)
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected
    
    def _crossover(self, parents: List[Individual]) -> List[Individual]:
        """Crossover operation"""
        offspring = []
        
        for i in range(0, len(parents) - 1, 2):
            parent1, parent2 = parents[i], parents[i + 1]
            
            if random.random() < self.crossover_rate:
                # Uniform crossover
                child1_genes, child2_genes = self._uniform_crossover(
                    parent1.genes, parent2.genes
                )
            else:
                # Copy parents
                child1_genes = parent1.genes.copy()
                child2_genes = parent2.genes.copy()
            
            child1 = Individual(
                id=str(uuid.uuid4()),
                genes=child1_genes,
                fitness=0.0,
                age=0,
                generation=self.current_generation + 1,
                parent_ids=[parent1.id, parent2.id],
                mutation_rate=self.mutation_rate,
                crossover_rate=self.crossover_rate
            )
            
            child2 = Individual(
                id=str(uuid.uuid4()),
                genes=child2_genes,
                fitness=0.0,
                age=0,
                generation=self.current_generation + 1,
                parent_ids=[parent1.id, parent2.id],
                mutation_rate=self.mutation_rate,
                crossover_rate=self.crossover_rate
            )
            
            offspring.extend([child1, child2])
        
        return offspring
    
    def _uniform_crossover(self, parent1_genes: List[float], 
                           parent2_genes: List[float]) -> Tuple[List[float], List[float]]:
        """Uniform crossover"""
        child1_genes = []
        child2_genes = []
        
        for i in range(len(parent1_genes)):
            if random.random() < 0.5:
                child1_genes.append(parent1_genes[i])
                child2_genes.append(parent2_genes[i])
            else:
                child1_genes.append(parent2_genes[i])
                child2_genes.append(parent1_genes[i])
        
        return child1_genes, child2_genes
    
    def _mutation(self, individuals: List[Individual]):
        """Mutation operation"""
        for individual in individuals:
            for i in range(len(individual.genes)):
                if random.random() < individual.mutation_rate:
                    # Gaussian mutation
                    lower, upper = self.problem.bounds[i]
                    mutation = random.gauss(0, 0.1) * (upper - lower)
                    individual.genes[i] += mutation
                    
                    # Ensure within bounds
                    individual.genes[i] = max(lower, min(upper, individual.genes[i]))
    
    def _replacement(self):
        """Replace old population with offspring"""
        # Sort combined population by fitness
        combined = self.population + self.offspring
        combined.sort(key=lambda x: x.fitness, reverse=True)
        
        # Keep best individuals
        self.population = combined[:self.population_size]
        self.offspring = []
    
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness (to be implemented based on problem)"""
        # Placeholder - would be problem-specific
        return sum(x**2 for x in solution)  # Sphere function

class ParticleSwarmOptimization(BioInspiredOptimizer):
    """Particle Swarm Optimization"""
    
    def __init__(self, problem: OptimizationProblem):
        super().__init__(problem)
        self.inertia_weight = problem.parameters.get("inertia_weight", 0.729)
        self.cognitive_coefficient = problem.parameters.get("cognitive_coefficient", 1.49445)
        self.social_coefficient = problem.parameters.get("social_coefficient", 1.49445)
        self.velocity_clamp = problem.parameters.get("velocity_clamp", 1.0)
        
        self.particles = []
        self.global_best_position = None
        self.global_best_fitness = float('-inf')
    
    async def optimize(self) -> Dict[str, Any]:
        """Run PSO optimization"""
        try:
            # Initialize swarm
            self._initialize_swarm()
            
            # Optimization loop
            for iteration in range(self.max_generations):
                # Evaluate fitness
                for particle in self.particles:
                    fitness = self.evaluate_fitness(particle.position)
                    
                    # Update personal best
                    if fitness > particle.personal_best_fitness:
                        particle.personal_best_fitness = fitness
                        particle.personal_best_position = particle.position.copy()
                    
                    # Update global best
                    if fitness > self.global_best_fitness:
                        self.global_best_fitness = fitness
                        self.global_best_position = particle.position.copy()
                
                # Update velocities and positions
                for particle in self.particles:
                    self._update_velocity(particle)
                    self._update_position(particle)
                
                # Record best fitness
                self.fitness_history.append(self.global_best_fitness)
                
                # Check convergence
                if self.is_converged():
                    logger.info(f"PSO converged at iteration {iteration}")
                    break
            
            return {
                "algorithm": "Particle Swarm Optimization",
                "best_solution": {
                    "position": self.global_best_position,
                    "fitness": self.global_best_fitness
                },
                "iterations": self.current_generation + 1,
                "fitness_history": self.fitness_history,
                "converged": self.is_converged()
            }
            
        except Exception as e:
            logger.error(f"Error in PSO: {e}")
            raise
    
    def _initialize_swarm(self):
        """Initialize particle swarm"""
        self.particles = []
        
        for i in range(self.population_size):
            position = []
            velocity = []
            
            for j, (lower, upper) in enumerate(self.problem.bounds):
                position.append(random.uniform(lower, upper))
                velocity.append(random.uniform(-(upper - lower), (upper - lower)))
            
            particle = Particle(
                id=str(uuid.uuid4()),
                position=position,
                velocity=velocity,
                personal_best_position=position.copy(),
                personal_best_fitness=float('-inf'),
                global_best_fitness=float('-inf'),
                inertia_weight=self.inertia_weight,
                cognitive_coefficient=self.cognitive_coefficient,
                social_coefficient=self.social_coefficient
            )
            
            self.particles.append(particle)
        
        # Initialize global best
        first_fitness = self.evaluate_fitness(self.particles[0].position)
        self.global_best_fitness = first_fitness
        self.global_best_position = self.particles[0].position.copy()
        
        for particle in self.particles:
            particle.personal_best_fitness = first_fitness
            particle.personal_best_position = particle.position.copy()
    
    def _update_velocity(self, particle: Particle):
        """Update particle velocity"""
        for i in range(len(particle.velocity)):
            r1 = random.random()
            r2 = random.random()
            
            cognitive = self.cognitive_coefficient * r1 * (
                particle.personal_best_position[i] - particle.position[i]
            )
            social = self.social_coefficient * r2 * (
                self.global_best_position[i] - particle.position[i]
            )
            
            particle.velocity[i] = (
                particle.inertia_weight * particle.velocity[i] +
                cognitive + social
            )
            
            # Velocity clamping
            max_velocity = abs(self.problem.bounds[i][1] - self.problem.bounds[i][0]) * self.velocity_clamp
            if abs(particle.velocity[i]) > max_velocity:
                particle.velocity[i] = max_velocity * np.sign(particle.velocity[i])
    
    def _update_position(self, particle: Particle):
        """Update particle position"""
        for i in range(len(particle.position)):
            particle.position[i] += particle.velocity[i]
            
            # Boundary handling
            lower, upper = self.problem.bounds[i]
            if particle.position[i] < lower:
                particle.position[i] = lower
                particle.velocity[i] *= -0.5
            elif particle.position[i] > upper:
                particle.position[i] = upper
                particle.velocity[i] *= -0.5
    
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness"""
        return -sum(x**2 for x in solution)  # Negative for maximization

class AntColonyOptimization(BioInspiredOptimizer):
    """Ant Colony Optimization for TSP-like problems"""
    
    def __init__(self, problem: OptimizationProblem):
        super().__init__(problem)
        self.num_ants = problem.parameters.get("num_ants", 20)
        self.num_iterations = problem.parameters.get("num_iterations", 100)
        self.evaporation_rate = problem.parameters.get("evaporation_rate", 0.1)
        self.alpha = problem.parameters.get("alpha", 1.0)  # Pheromone importance
        self.beta = problem.parameters.get("beta", 2.0)      # Heuristic importance
        self.q0 = problem.parameters.get("q0", 0.9)        # Probability of random choice
        
        self.ants = []
        self.pheromone_matrix = None
        self.distance_matrix = None
        self.best_tour = None
        self.best_tour_length = float('inf')
    
    async def optimize(self) -> Dict[str, Any]:
        """Run ACO optimization"""
        try:
            # Initialize distance matrix (simplified for continuous optimization)
            self._initialize_distance_matrix()
            
            # Initialize pheromone matrix
            self._initialize_pheromone_matrix()
            
            # Optimization loop
            for iteration in range(self.num_iterations):
                # Construct solutions
                for ant in self.ants:
                    self._construct_solution(ant)
                
                # Calculate tour lengths
                for ant in self.ants:
                    ant.tour_length = self._calculate_tour_length(ant.path)
                
                # Update best solution
                best_ant = min(self.ants, key=lambda x: x.tour_length)
                if best_ant.tour_length < self.best_tour_length:
                    self.best_tour = best_ant.path.copy()
                    self.best_tour_length = best_ant.tour_length
                
                # Update pheromones
                self._update_pheromones()
                
                # Record fitness (inverse of tour length)
                fitness = 1.0 / (self.best_tour_length + 1e-10)
                self.fitness_history.append(fitness)
                
                # Check convergence
                if self.is_converged():
                    logger.info(f"ACO converged at iteration {iteration}")
                    break
            
            return {
                "algorithm": "Ant Colony Optimization",
                "best_solution": {
                    "path": self.best_tour,
                    "tour_length": self.best_tour_length,
                    "fitness": 1.0 / (self.best_tour_length + 1e-10)
                },
                "iterations": self.current_generation + 1,
                "fitness_history": self.fitness_history,
                "converged": self.is_converged()
            }
            
        except Exception as e:
            logger.error(f"Error in ACO: {e}")
            raise
    
    def _initialize_distance_matrix(self):
        """Initialize distance matrix"""
        n = self.problem.dimensions
        self.distance_matrix = np.random.rand(n, n)
        
        # Make symmetric and diagonal zero
        for i in range(n):
            for j in range(i + 1, n):
                self.distance_matrix[j, i] = self.distance_matrix[i, j]
    
    def _initialize_pheromone_matrix(self):
        """Initialize pheromone matrix"""
        n = self.problem.dimensions
        self.pheromone_matrix = np.ones((n, n)) * 0.1
    
    def _construct_solution(self, ant: Ant):
        """Construct solution for ant"""
        n = self.problem.dimensions
        visited = [random.randint(0, n - 1)]
        ant.path = [self._position_from_index(visited[0])]
        
        while len(visited) < n:
            current = visited[-1]
            
            # Choose next node
            if random.random() < self.q0:
                # Random choice
                next_node = random.choice([i for i in range(n) if i not in visited])
            else:
                # Probabilistic choice
                probabilities = []
                for i in range(n):
                    if i not in visited:
                        pheromone = self.pheromone_matrix[current, i] ** self.alpha
                        heuristic = 1.0 / (self.distance_matrix[current, i] + 1e-10) ** self.beta
                        probabilities.append(pheromone * heuristic)
                    else:
                        probabilities.append(0)
                
                if sum(probabilities) > 0:
                    probabilities = np.array(probabilities) / sum(probabilities)
                    next_node = np.random.choice(n, p=probabilities)
                else:
                    next_node = random.choice([i for i in range(n) if i not in visited])
            
            visited.append(next_node)
            ant.path.append(self._position_from_index(next_node))
        
        ant.tour_length = self._calculate_tour_length(ant.path)
    
    def _position_from_index(self, index: int) -> List[float]:
        """Convert index to position vector"""
        position = []
        for i, (lower, upper) in enumerate(self.problem.bounds):
            if i == index:
                position.append(random.uniform(lower, upper))
            else:
                position.append((lower + upper) / 2)
        
        return position
    
    def _calculate_tour_length(self, path: List[List[float]]) -> float:
        """Calculate tour length"""
        total_length = 0.0
        
        for i in range(len(path) - 1):
            distance = 0.0
            for j in range(len(path[i])):
                distance += (path[i][j] - path[i + 1][j]) ** 2
            total_length += np.sqrt(distance)
        
        return total_length
    
    def _update_pheromones(self):
        """Update pheromone matrix"""
        # Evaporation
        self.pheromone_matrix *= (1 - self.evaporation_rate)
        
        # Deposit pheromones
        for ant in self.ants:
            pheromone_deposit = 1.0 / (ant.tour_length + 1e-10)
            
            for i in range(len(ant.path) - 1):
                current_idx = self._index_from_position(ant.path[i])
                next_idx = self._index_from_position(ant.path[i + 1])
                
                self.pheromone_matrix[current_idx, next_idx] += pheromone_deposit
                self.pheromone_matrix[next_idx, current_idx] += pheromone_deposit
    
    def _index_from_position(self, position: List[float]) -> int:
        """Convert position to index (simplified)"""
        # Find closest index
        min_distance = float('inf')
        best_idx = 0
        
        for i in range(self.problem.dimensions):
            distance = 0.0
            for j, (lower, upper) in enumerate(self.problem.bounds):
                center = (lower + upper) / 2
                distance += (position[j] - center) ** 2
            
            if distance < min_distance:
                min_distance = distance
                best_idx = i
        
        return best_idx
    
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness"""
        return -sum(x**2 for x in solution)

class ArtificialBeeColony(BioInspiredOptimizer):
    """Artificial Bee Colony optimization"""
    
    def __init__(self, problem: OptimizationProblem):
        super().__init__(problem)
        self.colony_size = problem.parameters.get("colony_size", 50)
        self.num_food_sources = problem.parameters.get("num_food_sources", 5)
        self.limit = problem.parameters.get("limit", 100)
        self.abandonment_limit = problem.parameters.get("abandonment_limit", 10)
        
        self.employed_bees = []
        self.onlooker_bees = []
        self.scout_bees = []
        self.food_sources = []
    
    async def optimize(self) -> Dict[str, Any]:
        """Run ABC optimization"""
        try:
            # Initialize colony
            self._initialize_colony()
            
            # Optimization loop
            for iteration in range(self.max_generations):
                # Employed bees phase
                self._employed_bees_phase()
                
                # Onlooker bees phase
                self._onlooker_bees_phase()
                
                # Scout bees phase
                self._scout_bees_phase()
                
                # Update best solution
                best_bee = max(self.employed_bees + self.onlooker_bees, 
                              key=lambda x: x.nectar_amount)
                
                if best_bee.nectar_amount > (self.best_solution.fitness if self.best_solution else 0):
                    self.best_solution = Individual(
                        id=best_bee.id,
                        genes=best_bee.position,
                        fitness=best_bee.nectar_amount,
                        age=0,
                        generation=iteration,
                        parent_ids=[],
                        mutation_rate=0.1,
                        crossover_rate=0.8
                    )
                
                # Record fitness
                self.fitness_history.append(self.best_solution.fitness)
                
                # Check convergence
                if self.is_converged():
                    logger.info(f"ABC converged at iteration {iteration}")
                    break
            
            return {
                "algorithm": "Artificial Bee Colony",
                "best_solution": {
                    "genes": self.best_solution.genes,
                    "fitness": self.best_solution.fitness,
                    "generation": self.best_solution.generation
                },
                "iterations": self.current_generation + 1,
                "fitness_history": self.fitness_history,
                "converged": self.is_converged()
            }
            
        except Exception as e:
            logger.error(f"Error in ABC: {e}")
            raise
    
    def _initialize_colony(self):
        """Initialize bee colony"""
        # Initialize employed bees
        for i in range(self.colony_size // 2):
            position = []
            for j, (lower, upper) in enumerate(self.problem.bounds):
                position.append(random.uniform(lower, upper))
            
            bee = Bee(
                id=str(uuid.uuid4()),
                position=position,
                nectar_amount=self.evaluate_fitness(position),
                waggle_dance_duration=0.0,
                exploration_rate=0.1,
                exploitation_rate=0.9
            )
            
            self.employed_bees.append(bee)
        
        # Initialize onlooker bees
        for i in range(self.colony_size // 2):
            bee = Bee(
                id=str(uuid.uuid4()),
                position=[],
                nectar_amount=0.0,
                waggle_dance_duration=0.0,
                exploration_rate=0.1,
                exploitation_rate=0.9
            )
            
            self.onlooker_bees.append(bee)
        
        # Initialize scout bees
        for i in range(5):
            bee = Bee(
                id=str(uuid.uuid4()),
                position=[],
                nectar_amount=0.0,
                waggle_dance_duration=0.0,
                exploration_rate=1.0,
                exploitation_rate=0.0
            )
            
            self.scout_bees.append(bee)
    
    def _employed_bees_phase(self):
        """Employed bees exploration phase"""
        for bee in self.employed_bees:
            # Generate new position near current position
            new_position = []
            for i, (lower, upper) in enumerate(self.problem.bounds):
                current_pos = bee.position[i]
                neighborhood_size = (upper - lower) * 0.1
                
                new_pos = current_pos + random.uniform(-neighborhood_size, neighborhood_size)
                new_pos = max(lower, min(upper, new_pos))
                new_position.append(new_pos)
            
            # Evaluate new position
            new_nectar = self.evaluate_fitness(new_position)
            
            # Update if better
            if new_nectar > bee.nectar_amount:
                bee.position = new_position
                bee.nectar_amount = new_nectar
                bee.waggle_dance_duration = 5.0  # Longer dance for better source
            else:
                bee.waggle_dance_duration = 0.0
                bee.abandonment_count += 1
                
                # Abandon if limit reached
                if bee.abandonment_count > self.abandonment_limit:
                    bee.position = []
                    bee.nectar_amount = 0.0
    
    def _onlooker_bees_phase(self):
        """Onlooker bees exploitation phase"""
        for bee in self.onlooker_bees:
            # Choose food source based on waggle dances
            if self.employed_bees:
                # Calculate selection probabilities
                total_dance = sum(b.waggle_dance_duration for b in self.employed_bees)
                
                if total_dance > 0:
                    probabilities = [b.waggle_dance_duration / total_dance for b in self.employed_bees]
                    
                    # Choose food source
                    chosen_bee = np.random.choice(self.employed_bees, p=probabilities)
                    
                    # Exploit near chosen bee
                    new_position = []
                    for i, (lower, upper) in enumerate(self.problem.bounds):
                        current_pos = chosen_bee.position[i]
                        neighborhood_size = (upper - lower) * 0.05
                        
                        new_pos = current_pos + random.uniform(-neighborhood_size, neighborhood_size)
                        new_pos = max(lower, min(upper, new_pos))
                        new_position.append(new_pos)
                    
                    # Evaluate
                    new_nectar = self.evaluate_fitness(new_position)
                    
                    if new_nectar > bee.nectar_amount:
                        bee.position = new_position
                        bee.nectar_amount = new_nectar
    
    def _scout_bees_phase(self):
        """Scout bees exploration phase"""
        for bee in self.scout_bees:
            # Random exploration
            position = []
            for j, (lower, upper) in enumerate(self.problem.bounds):
                position.append(random.uniform(lower, upper))
            
            bee.position = position
            bee.nectar_amount = self.evaluate_fitness(position)
    
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness"""
        return sum(x**2 for x in solution)

class FireflyAlgorithm(BioInspiredOptimizer):
    """Firefly Algorithm optimization"""
    
    def __init__(self, problem: OptimizationProblem):
        super().__init__(problem)
        self.population_size = problem.parameters.get("population_size", 50)
        self.absorption_coefficient = problem.parameters.get("absorption_coefficient", 0.5)
        self.randomization_parameter = problem.parameters.get("randomization_parameter", 0.5)
        self.gamma = problem.parameters.get("gamma", 1.0)
        
        self.fireflies = []
        self.global_best_position = None
        self.global_best_intensity = float('-inf')
    
    async def optimize(self) -> Dict[str, Any]:
        """Run Firefly Algorithm"""
        try:
            # Initialize fireflies
            self._initialize_fireflies()
            
            # Optimization loop
            for iteration in range(self.max_generations):
                # Update light intensities
                for firefly in self.fireflies:
                    firefly.light_intensity = self.evaluate_fitness(firefly.position)
                    
                    # Update global best
                    if firefly.light_intensity > self.global_best_intensity:
                        self.global_best_intensity = firefly.light_intensity
                        self.global_best_position = firefly.position.copy()
                
                # Move fireflies
                for i, firefly_i in enumerate(self.fireflies):
                    for j, firefly_j in enumerate(self.fireflies):
                        if i != j:
                            self._move_firefly(firefly_i, firefly_j)
                
                # Record best fitness
                self.fitness_history.append(self.global_best_intensity)
                
                # Check convergence
                if self.is_converged():
                    logger.info(f"Firefly Algorithm converged at iteration {iteration}")
                    break
            
            return {
                "algorithm": "Firefly Algorithm",
                "best_solution": {
                    "position": self.global_best_position,
                    "fitness": self.global_best_intensity
                },
                "iterations": self.current_generation + 1,
                "fitness_history": self.fitness_history,
                "converged": self.is_converged()
            }
            
        except Exception as e:
            logger.error(f"Error in Firefly Algorithm: {e}")
            raise
    
    def _initialize_fireflies(self):
        """Initialize firefly population"""
        self.fireflies = []
        
        for i in range(self.population_size):
            position = []
            for j, (lower, upper) in enumerate(self.problem.bounds):
                position.append(random.uniform(lower, upper))
            
            firefly = Firefly(
                id=str(uuid.uuid4()),
                position=position,
                light_intensity=0.0,
                absorption_coefficient=self.absorption_coefficient,
                randomization_parameter=self.randomization_parameter
            )
            
            self.fireflies.append(firefly)
        
        # Initialize global best
        first_intensity = self.evaluate_fitness(self.fireflies[0].position)
        self.global_best_intensity = first_intensity
        self.global_best_position = self.fireflies[0].position.copy()
    
    def _move_firefly(self, firefly_i: Firefly, firefly_j: Firefly):
        """Move firefly i towards firefly j"""
        distance = self._calculate_distance(firefly_i.position, firefly_j.position)
        
        if firefly_j.light_intensity > firefly_i.light_intensity:
            # Move towards brighter firefly
            beta = 1.0
            for k in range(len(firefly_i.position)):
                firefly_i.position[k] += beta * (
                    firefly_j.position[k] - firefly_i.position[k]
                ) * np.exp(-self.gamma * distance**2)
        else:
            # Random movement
            alpha = self.randomization_parameter
            for k in range(len(firefly_i.position)):
                firefly_i.position[k] += alpha * (random.random() - 0.5) * (
                    self.problem.bounds[k][1] - self.problem.bounds[k][0]
                )
        
        # Keep within bounds
        for k in range(len(firefly_i.position)):
            lower, upper = self.problem.bounds[k]
            firefly_i.position[k] = max(lower, min(upper, firefly_i.position[k]))
    
    def _calculate_distance(self, pos1: List[float], pos2: List[float]) -> float:
        """Calculate distance between positions"""
        return np.sqrt(sum((x - y)**2 for x, y in zip(pos1, pos2)))
    
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness (light intensity)"""
        return sum(x**2 for x in solution)

class NeuralNetworkOptimizer(BioInspiredOptimizer):
    """Neural Network-based optimizer"""
    
    def __init__(self, problem: OptimizationProblem):
        super().__init__(problem)
        self.network_size = problem.parameters.get("network_size", [10, 5])
        self.learning_rate = problem.parameters.get("learning_rate", 0.01)
        self.epochs = problem.parameters.get("epochs", 100)
        
        self.network = None
        self._initialize_network()
    
    def _initialize_network(self):
        """Initialize neural network"""
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        class SimpleNN(nn.Module):
            def __init__(self, input_size, hidden_size, output_size):
                super().__init__()
                self.fc1 = nn.Linear(input_size, hidden_size)
                self.fc2 = nn.Linear(hidden_size, hidden_size)
                self.fc3 = nn.Linear(hidden_size, output_size)
                self.relu = nn.ReLU()
            
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.relu(self.fc2(x))
                x = self.fc3(x)
                return x
        
        input_size = self.problem.dimensions
        hidden_size = self.network_size[0]
        output_size = 1  # Single output for optimization
        
        self.network = SimpleNN(input_size, hidden_size, output_size)
        self.optimizer = optim.Adam(self.network.parameters(), lr=self.learning_rate)
    
    async def optimize(self) -> Dict[str, Any]:
        """Run neural network optimization"""
        try:
            import torch
            
            # Training loop
            for epoch in range(self.epochs):
                # Generate training data
                inputs, targets = self._generate_training_data()
                
                # Forward pass
                outputs = self.network(inputs)
                loss = torch.mean((outputs - targets)**2)
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                # Record fitness
                fitness = -loss.item()
                self.fitness_history.append(fitness)
                
                # Check convergence
                if self.is_converged():
                    logger.info(f"Neural Network converged at epoch {epoch}")
                    break
            
            # Get best solution
            best_position = self._get_network_parameters()
            best_fitness = self.evaluate_fitness(best_position)
            
            return {
                "algorithm": "Neural Network",
                "best_solution": {
                    "position": best_position,
                    "fitness": best_fitness
                },
                "epochs": self.current_generation + 1,
                "fitness_history": self.fitness_history,
                "converged": self.is_converged()
            }
            
        except Exception as e:
            logger.error(f"Error in Neural Network optimization: {e}")
            raise
    
    def _generate_training_data(self):
        """Generate training data"""
        import torch
        
        # Generate random training data
        batch_size = 100
        inputs = torch.randn(batch_size, self.problem.dimensions)
        
        # Simple target function
        targets = torch.sum(inputs**2, dim=1, keepdim=True)
        
        return inputs, targets
    
    def _get_network_parameters(self) -> List[float]:
        """Get network parameters as list"""
        import torch
        
        params = []
        for param in self.network.parameters():
            params.extend(param.detach().numpy().flatten())
        
        return params
    
    def evaluate_fitness(self, solution: List[float]) -> float:
        """Evaluate fitness"""
        return -sum(x**2 for x in solution)

class BioInspiredManager:
    """Manager for bio-inspired optimization algorithms"""
    
    def __init__(self):
        self.algorithms = {
            BioAlgorithm.GENETIC_ALGORITHM: GeneticAlgorithm,
            BioAlgorithm.PARTICLE_SWARM_OPTIMIZATION: ParticleSwarmOptimization,
            BioAlgorithm.ANT_COLONY_OPTIMIZATION: AntColonyOptimization,
            BioAlgorithm.ARTIFICIAL_BEE_COLONY: ArtificialBeeColony,
            BioAlgorithm.FIREFLY_ALGORITHM: FireflyAlgorithm,
            BioAlgorithm.NEURAL_NETWORK: NeuralNetworkOptimizer
        }
        
        self.optimization_history = []
    
    async def optimize(self, problem: OptimizationProblem, 
                        algorithm: BioAlgorithm = BioAlgorithm.GENETIC_ALGORITHM) -> Dict[str, Any]:
        """Run optimization with specified algorithm"""
        try:
            if algorithm not in self.algorithms:
                raise ValueError(f"Algorithm {algorithm} not supported")
            
            optimizer_class = self.algorithms[algorithm]
            optimizer = optimizer_class(problem)
            
            result = await optimizer.optimize()
            
            self.optimization_history.append({
                "algorithm": algorithm.value,
                "problem": problem.name,
                "result": result,
                "timestamp": datetime.now()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in optimization: {e}")
            raise
    
    def get_algorithm_comparison(self, problem: OptimizationProblem) -> Dict[str, Any]:
        """Compare all algorithms on the same problem"""
        try:
            results = {}
            
            for algorithm in BioAlgorithm:
                try:
                    result = await self.optimize(problem, algorithm)
                    results[algorithm.value] = result
                except Exception as e:
                    logger.error(f"Error in {algorithm.value}: {e}")
                    results[algorithm.value] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error in algorithm comparison: {e}")
            return {}

# Global bio-inspired manager
bio_manager = BioInspiredManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/bio_inspired", tags=["bio_inspired_computing"])

class ProblemDefinition(BaseModel):
    name: str
    domain: str
    type: str
    dimensions: int
    bounds: List[List[float]]
    parameters: Dict[str, Any] = {}

class OptimizationRequest(BaseModel):
    problem_id: str
    algorithm: str = "genetic_algorithm"

@router.post("/problems/create")
async def create_problem(request: ProblemDefinition):
    """Create optimization problem"""
    try:
        problem = OptimizationProblem(
            id=str(uuid.uuid4()),
            name=request.name,
            domain=ProblemDomain(request.domain),
            type=OptimizationType(request.type),
            dimensions=request.dimensions,
            bounds=request.bounds,
            constraints=[],
            parameters=request.parameters,
            created_at=datetime.now()
        )
        
        return asdict(problem)
    except Exception as e:
        logger.error(f"Error creating problem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def run_optimization(request: OptimizationRequest):
    """Run bio-inspired optimization"""
    try:
        # Create dummy problem (in real implementation, would get from storage)
        problem = OptimizationProblem(
            id=request.problem_id,
            name="Test Problem",
            domain=ProblemDomain.ENGINEERING,
            type=OptimizationType.MINIMIZATION,
            dimensions=10,
            bounds=[[-5.0, 5.0]] * 10,
            constraints=[],
            parameters={},
            created_at=datetime.now()
        )
        
        algorithm = BioAlgorithm(request.algorithm)
        result = await bio_manager.optimize(problem, algorithm)
        
        return result
    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/algorithms")
async def list_algorithms():
    """List available bio-inspired algorithms"""
    try:
        algorithms = [algo.value for algo in BioAlgorithm]
        return {"algorithms": algorithms}
    except Exception as e:
        logger.error(f"Error listing algorithms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains")
async def list_domains():
    """List problem domains"""
    try:
        domains = [domain.value for domain in ProblemDomain]
        return {"domains": domains}
    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_bio_inspired_status():
    """Get bio-inspired computing status"""
    try:
        return {
            "available_algorithms": len(bio_manager.algorithms),
            "optimization_history": len(bio_manager.optimization_history),
            "supported_domains": len(ProblemDomain),
            "supported_types": len(OptimizationType)
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
