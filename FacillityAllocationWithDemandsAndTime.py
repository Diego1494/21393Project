from gurobipy import *
import math
import numpy

#This section declares all model constant values

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

#Element i indicates the cost of opening a facility of
#size 1 at location i
facilityUnitCosts = [1, 2, 4, 5, 1, 2, 1.5, 2, 3]

#Usefull values
numFacilities = len(facilities)
numClients = len(clients)
facilityCapacities = 20 #The number of different sizes a facility can have

#Data structures to hold the model variables and constants
x = {}; n = {}; f = {}; y = {}; w = {}; l = {}; d = {}
alpha = 1 
totalTime = 100 #Total number of time units

#Given the index of a capacity, returns the number of cars that that a facility of that
#capacity can hold.
def capacity(c):
	return c

#Calculates the distance of the path c -> a -> b
def distance(a,b):
	dx = a[0] - b[0]
	dy = a[1] - b[1]
	return math.sqrt(dx*dx + dy*dy)

#Returns the demand of cars going from client i to client j at time t.
def demand(i, j, t):
	if (t == totalTime - 1): return 0
	else: return 5

#START MODEL

# This function is responsible for adding all the variables and constants that will be used
# by the model
def addVariables(m):
	
	#Variable X[k,c] binary variable which indicates if facility k of capacity c is open
	for k in xrange(numFacilities):
		for c in xrange(facilityCapacities):
			x[(k, c)] = m.addVar(vtype=GRB.BINARY, name="x%d,%d" % (k, c))

	for c in xrange(facilityCapacities):
		#Variable indicating the number of cars that a facility of capacity c can hold
		n[c] = capacity(c)

	for k in xrange(numFacilities):
	#Variable f[k] cost of holding 1 car at facility k.
		f[k] = facilityUnitCosts[k]

	for t in xrange(totalTime):
		for i in xrange(numClients):
			for k in xrange(numFacilities):
				#Variable Y_(i,k,t) continuous variable indicating number of cars that facility k sends to client i
				#at time t.
				y[(i,k,t)] = m.addVar(lb=0, vtype=GRB.INTEGER, name="Y%d,%d,%d" % (i,k,t))
				#Variable W_(i,k,t) continuous variable indicating number of cars that client i sends to facility k
				#at time t.
				w[(i,k,t)] = m.addVar(lb=0, vtype=GRB.INTEGER, name="W%d,%d,%d" % (i,k,t))

	for i in xrange(numClients):
		for j in xrange(numClients):
			for t in xrange(totalTime):
				#Demand of cars needing to go from i to j at time t
				l[(i, j, t)] = demand(i, k, t)

	for i in xrange(numClients):
		for k in xrange(numFacilities):
			#Variable d_(i,k,j) indicates the distance of the path starting at facility k, going to client i
			d[(i, k)] = distance(clients[i], facilities[k])


# This function is responsible for adding all the necessary constraints to the 
# model
def addConstraints(m):

	#Define two variables which will make constraints easier to understand

	#Number of cars at location i at start time ti
	def s(i, ti): return quicksum((y[(i,k,t)] - w[(i,k,t)]) for t in xrange(ti) for k in xrange(numFacilities)) + quicksum((l[(j, i, t)] - l[(i, j, t)]) for t in xrange(ti) for j in xrange(numClients))

	#Number of clients at facility i start of time ti
	def r(k, ti): return quicksum(n[c]*x[(k,c)] for c in xrange(facilityCapacities)) + quicksum((w[(i,k,t)] - y[(i,k,t)]) for t in xrange(ti) for k in xrange(numFacilities)) 

	# Add constraints

	for k in xrange(numFacilities):
		#At most one size of a facility is open per location
		m.addConstr(quicksum(x[(k,c)] for c in xrange(facilityCapacities)) <= 1)

	for t in xrange(totalTime):
		for i in xrange(numClients):
			#Excess cars at a given location go back to some facility
			m.addConstr(quicksum(w[(i, k, t)] for k in xrange(numFacilities)) == (s(i, t) + quicksum(y[(i,k,t)] for k in xrange(numFacilities)) - quicksum(l[(i,j,t)]  for j in xrange(numClients))))

			#Demand between all locations is satisfied
			m.addConstr(quicksum(l[(i, j, t)] for j in xrange(numClients)) <= quicksum(y[(i, k, t)] for k in xrange(numFacilities)) + s(i, t))

	for t in xrange(totalTime):
		for k in xrange(numFacilities):
			#A facility can not send out more cars than it has at that time
			m.addConstr(quicksum(y[(i, k, t)] for i in xrange(numClients)) <= r(k, t))
			#The number of cars at a facility must be less than its capacity
			m.addConstr(r(k, t) <= quicksum(n[c] * x[(k,c)] for c in xrange(facilityCapacities)))

	#All cars go back to some facility at the end of the day. Note that in order for this to be a viable constraint, we need to make the final unit of time
	#have a demand of 0, such that cars can go back
	m.addConstr(quicksum(y[(i, k, t)] - w[(i, k, t)] for t in xrange(totalTime) for i in xrange(numClients) for k in xrange(numFacilities)) == 0)

# This function is responsible for setting up the model and defining the objective
# function of the model
def startModel(model):
	addVariables(model)
	addConstraints(model)
	#model.setObjective( quicksum(facilitySizeCosts[i][j]*x[(i,j)] for i in range(numFacilities) for j in range(numSizes)) 
	#    + quicksum(alpha*d[(i,j,k)]*y[(i,j,k)]*x[(k, c)]*c for c in range(numSizes) for i in range(numClients) for j in range(numClients) for k in range(numFacilities)))
	model.setObjective(quicksum(n[c]*x[(k, c)]*f[k] for c in xrange(facilityCapacities) for k in xrange(numFacilities)) + quicksum(w[(i, k, t)] + y[(i, k, t)] * d[(i, k)] for i in xrange(numClients) for k in xrange(numFacilities) for t in xrange(totalTime)) )
		#NOTE: may need to multiply here by x[k, c]

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
	m.ModelSense = GRB.MINIMIZE
	m.optimize()
	printResults(m)

optimizeModel()