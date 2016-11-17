from gurobipy import *
import math

#This section is used to declare all of the model data as global variables

#Element i indicates the (x,y) location of client i
clients = [[0, 1.5],[2.5, 1.2]]

#Element i indicates the (x,y) location of facility i
facilities = [[0,0],[0,1],[0,1],
              [1,0],[1,1],[1,2],
              [2,0],[2,1],[2,2]]

#Element (i,j) indicates the cost of opening a facility of
#size j at facility i
facilitySizeCosts = [[3,2,3,1,3,3,4,3,2],
					 [2,2,3,1,3,3,4,3,2],
					 [3,2,3,1,3,3,4,3,2],
					 [1,2,3,1,3,3,4,3,2],
					 [3,2,3,1,3,3,4,3,2],
					 [3,2,3,1,3,3,4,3,2],
					 [4,2,3,1,3,3,4,3,2],
					 [3,2,3,1,3,3,4,3,2],
					 [2,2,3,1,3,3,4,3,2],]

numFacilities = len(facilities)
numClients = len(clients)
numSizes = len(facilitySizeCosts)

#Data structures to hold the model variables and constants
x = {}
y = {}
d = {} # Distance matrix (not a variable)
alpha = 1


def distance(a,b):
	dx = a[0] - b[0]
	dy = a[1] - b[1]
	return math.sqrt(dx*dx + dy*dy)

# This function is responsible for adding all the variables that will be used
# by the model
def addVariables(m):
	for j in range(numFacilities):
		for c in range(numSizes):
			x[(j, c)] = m.addVar(vtype=GRB.BINARY, name="x%d,%d" % (j,c))

	for i in range(numClients):
		for j in range(numFacilities):
			y[(i,j)] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="t%d,%d" % (i,j))
			d[(i,j)] = distance(clients[i], facilities[j])

# This function is responsible for adding all the necessary constraints to the 
# model
def addConstraints(m):

	# Add constraints
	for i in range(numClients):
		for j in range(numFacilities):
			m.addConstr(y[(i,j)] <= quicksum(x[(j,c)] for c in range(numSizes)))

	for i in range(numClients):
		m.addConstr(quicksum(y[(i,j)] for j in range(numFacilities)) == 1)

	for i in range(numFacilities):
		m.addConstr(quicksum(x[(i,j)] for j in range(numSizes)) == 1)

# This function is responsible for setting up the model and defining the objective
# function of the model
def startModel(model):
	addVariables(model)
	addConstraints(model)
	model.setObjective( quicksum(quicksum(facilitySizeCosts[i][j]*x[(i,j)] for i in range(numFacilities) for j in range(numSizes)) 
		+ quicksum(alpha*d[(i,j)]*y[(i,j)] for i in range(numClients)) for j in range(numFacilities)) )

#This function is responsible for setting up the model and invoking
#the Gurobi Optimizer on it.
def optimizeModel():
	m = Model()
	startModel(m)
	m.optimize()

optimizeModel()
