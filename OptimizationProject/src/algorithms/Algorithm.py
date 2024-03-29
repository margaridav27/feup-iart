from abc import abstractmethod, ABC
from random import randint, choice
from copy import deepcopy
from time import perf_counter
import json

class Algorithm(ABC):
    def __init__(self, initial_solution, max_iterations=10000, max_iterations_no_imp=1000):
        self.max_iterations_no_imp = 1000
        self.max_iterations = 10000
        self.initial_solution = initial_solution

    @abstractmethod
    def execute(self):
        pass

    def stop(self, iteration, iteration_no_imp):
        return iteration >= self.max_iterations or iteration_no_imp >= self.max_iterations_no_imp
    
    def change_pool(self, solution):
        """
        Generates a neighbour solution by changing the pool of a randomly selected server from the original solution
        """

        if solution.pools <= 1: 
            return solution

        new_solution = deepcopy(solution)
        servers, pools = new_solution.servers, new_solution.pools

        allocated = [server for server in servers if server.pool != -1]
        if len(allocated) == 0: return solution

        server = allocated[randint(0, len(allocated) - 1)]

        possibilities = [ p for p in range(0, pools) if p != server.pool ]
        server.pool = choice(possibilities)

        new_solution.evaluate()
        return new_solution

    def change_row(self, solution):
        """
        Generates a neighbour solution by changing the row of a randomly selected server from the original solution
        """

        new_solution = deepcopy(solution)
        servers, rows = new_solution.servers, new_solution.rows

        allocated = [server for server in servers if server.pool != -1]
        if len(allocated) == 0: return solution

        server = allocated[randint(0, len(allocated) - 1)]
        
        new_row_idx = randint(0, len(rows) - 1)
        new_row = rows[new_row_idx]
        
        if (new_slot:=new_row.allocate_server(server)) == -1: return solution

        rows[server.row].unset_server(server)
        server.set_position(new_slot, new_row_idx)
        
        new_solution.evaluate()
        return new_solution
       
    def allocate_server(self, solution):
        """
        Generates a neighbour solution by allocating a randomly selected non-allocated server 
        """
        
        new_solution = deepcopy(solution)
        servers, rows, pools = new_solution.servers, new_solution.rows, new_solution.pools

        deallocated = [server for server in servers if server.pool == -1]
        if len(deallocated) == 0: return solution
        
        server = deallocated[randint(0, len(deallocated) - 1)]

        new_row_idx = randint(0, len(rows) - 1)
        new_row = rows[new_row_idx]
        
        if (slot:=new_row.allocate_server(server)) == -1: return solution
        
        server.set_position(slot, new_row_idx)
        server.pool = randint(0, pools - 1)

        new_solution.evaluate()
        return new_solution
        
    def swap_allocation(self, solution):       
        """
        Generates a neighbour solution by deallocating an allocated server and allocating a non-allocated server, both randomly selected
        """
                
        new_solution = deepcopy(solution)
        servers, rows = new_solution.servers, new_solution.rows

        allocated = []
        deallocated = []

        for server in servers:
            if server.pool != -1:
                allocated.append(server)
            else:
                deallocated.append(server)

        if (len(deallocated) == 0) or (len(allocated) == 0): return solution

        to_deallocate = allocated[randint(0, len(allocated) - 1)]
        to_allocate = deallocated[randint(0, len(deallocated) - 1)]


        row = rows[to_deallocate.row]
        row.unset_server(to_deallocate)

        if row.allocate_server_to_slot(to_allocate, to_deallocate.slot): 
            to_allocate.set_position(to_deallocate.slot, to_deallocate.row)
            to_allocate.pool = to_deallocate.pool
            to_deallocate.unset()
            new_solution.evaluate()
            return new_solution

        return solution
    
    def swap_allocated_servers(self, solution):       
        """
        Generates a neighbour solution by swapping two randomly selected allocated servers 
        """
                
        new_solution = deepcopy(solution)
        servers, rows = new_solution.servers, new_solution.rows

        allocated = [server for server in servers if server.pool != -1]
        if len(allocated) < 2: return solution
        
        server1 = allocated[randint(0, len(allocated) - 1)]
        allocated.remove(server1)
        server2 = allocated[randint(0, len(allocated) - 1)]
        
        row1, row2 = rows[server1.row], rows[server2.row]
        row1.unset_server(server1)
        row2.unset_server(server2)

        if not (row1.allocate_server_to_slot(server2, server1.slot) and \
                row2.allocate_server_to_slot(server1, server2.slot)): 
                return solution
                        
        server1_old_row, server1_old_slot = server1.row, server1.slot
        server1.set_position(server2.slot, server2.row)   
        server2.set_position(server1_old_slot, server1_old_row)
             
        new_solution.evaluate()
        return new_solution

    def neighbour_solution(self, solution):
        """
        Obtains neighbour solution by applying one of the available strategies
        """
        operators = [self.change_pool, 
                     self.change_row, 
                     self.allocate_server,
                     self.swap_allocation, 
                     self.swap_allocated_servers]

        selected_operator = randint(0, len(operators) - 1)
        new_solution = operators[selected_operator](solution)
        new_solution.evaluate()
        return new_solution
    
    def neighbour_solutions(self, solution):
        """
        Obtains neighbour solution by applying one of the available strategies
        """

        operators = [self.change_pool, 
                     self.change_row, 
                     self.allocate_server, 
                     self.swap_allocation, 
                     self.swap_allocated_servers]
        
        solutions = []
        for operator in operators:
            new_solution = operator(solution)
            new_solution.evaluate()
            solutions.append(new_solution)
        
        return solutions

    def get_best_solution(self, solution):
        return max(solution, key= lambda sol: sol.evaluation)

    def open_file(self, file):
        with open(file, 'w') as outfile:
            outfile.write('{"data": [\n')

    def write_to_file(self, file,solution, iteration):
        data = {'evaluation': solution.evaluation,
                'time': solution.time,
                'iteration': iteration}

        with open(file, 'a') as outfile:
            outfile.write(json.dumps(data)+',\n')
            outfile.close()

    def close_file(self, file):
        with open(file, 'a') as outfile:
            outfile.write(']}')

    def set_initial_solution(self, initial_solution):
        self.initial_solution = initial_solution
