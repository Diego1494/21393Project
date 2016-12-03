from gurobipy import *
import math

#This section is used to declare all of the model data as global variables

#Element i indicates the (x,y) location of client i
clients = [[0, 1.5],[2.5, 1.2], [4, 4]]

#Element (i, j) denotes the demand of services starting at i and ending at j.
#Note that demand need not be symmetric. 
clientToClientDemands = [[0, 1, 3],
						 [4, 0, 2],
						 [3, 6, 0]]

#Element i indicates the (x,y) location of facility i
facilities = [[0,0],[0,1],[0,1.5],
              [1,0],[1,1],[1,2],
              [2,0],[2,1],[2,2]]

#Element (i,j) indicates the cost of opening a facility of
#size j at location i
facilitySizeCosts = [[1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9],
					 [1,2,3,4,5,6,7,8,9]]

numFacilities = len(facilities)
numClients = len(clients)
numSizes = len(facilitySizeCosts)

#Data structures to hold the model variables and constants
x = {}
y = {}
d = {} # Distance matrix (not a variable)
alpha = 1

#Calculates the distance of the path c -> a -> b
def distance(a,b,c):
	dx0 = c[0] - a[0]
	dy0 = c[1] - b[1]
	dx1 = a[0] - b[0]
	dy1 = a[1] - b[1]
	return math.sqrt(dx0*dx0 + dy0*dy0) + math.sqrt(dx1*dx1 + dy1*dy1)

#START OF MODEL

# This function is responsible for adding all the variables that will be used
# by the model
def addVariables(m):
	#Variable X_(j,c) binary variable indicating wether facility j with capacity c is open or not
	for j in range(numFacilities):
		for c in range(numSizes):
			x[(j, c)] = m.addVar(vtype=GRB.BINARY, name="x%d,%d" % (j,c))

	#Variable Y_(i,j,k) continuous variable in the range [0,1] indicating portion of the capacity of
	#facility k that is allocated to take clients from location i to location j.
	#Variable d_(i,k,j) indicates the distance of the path starting at facility k, going to client i
	#and ending at client j
	for i in range(numClients):
		for j in range(numClients):
			for k in range(numFacilities):
				y[(i,j,k)] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="t%d,%d,%d" % (i,j,k))
				d[(i,j,k)] = distance(clients[i], clients[j], facilities[k])

# This function is responsible for adding all the necessary constraints to the 
# model
def addConstraints(m):

	# Add constraints

	#NOTE: this constraint may not be necessary
	#If facility k is closed, then Y_(i,j,k) must be 0. Otherwise, Y_(i,j,k) must be 1 at most.
	for k in range(numFacilities):
		for i in range(numClients):
			for j in range(numClients):
				m.addConstr(y[(i,j,k)] <= quicksum(x[(k,c)] for c in range(numSizes)))

	#The demand between any two locations must be satisfied when you add up the number of cars 
	#that each facility allocates to that particular demand.
	for i in range(numClients):
		for j in range(numClients):
			m.addConstr(quicksum(y[(i,j,k)]*quicksum(c * x[(k,c)] for c in range(numSizes)) for k in range(numFacilities)) >=
				clientToClientDemands[i][j])

	#For each facility, only one size can be open
	for i in range(numFacilities):
		m.addConstr(quicksum(x[(i,j)] for j in range(numSizes)) <= 1)

	#For each facility, it can not supply more than its capacity.
	for k in range(numFacilities):
		m.addConstr(quicksum(y[(i,j,k)] for i in range(numClients) for j in range(numClients)) <= 1)

# This function is responsible for setting up the model and defining the objective
# function of the model
def startModel(model):
	addVariables(model)
	addConstraints(model)
	model.setObjective( quicksum(facilitySizeCosts[i][j]*x[(i,j)] for i in range(numFacilities) for j in range(numSizes)) 
	    + quicksum(alpha*d[(i,j,k)]*y[(i,j,k)]*x[(k, c)]*c for c in range(numSizes) for i in range(numClients) for j in range(numClients) for k in range(numFacilities)))

def printResults(model):
	vars = model.getVars()
	for var in vars:
		if (var.x != 0):
			print(var.varName)
			print(var.x)
			print("\n")

#This function is responsible for setting up the model and invoking
#the Gurobi Optimizer on it.
def optimizeModel():
	m = Model()
	startModel(m)
	m.optimize()
	printResults(m)

optimizeModel()