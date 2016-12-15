from gurobipy import *
import math
import numpy
from random import randint

#This section declares all model constant values

#Element i indicates the (x,y) location of client i
clients = [(100, 110), (120, 388), (413, 180), (500, 520)]

#Element i indicates the (x,y) location of facility i
facilities = [(50, 75), (50, 255), (200, 215), (400, 300), (510, 65), (100, 450), (340, 50), (490, 350), (500, 500)]

#Element i indicates the cost of opening a facility of size 1 at location i
facilityUnitCosts = [1, 2, 4, 5, 1, 2, 1.5, 2, 3]    #CHANGE HERE

#Usefull values
numFacilities = len(facilities)    #CHANGE HERE
numClients = len(clients)          #CHANGE HERE

#Data structures to hold the model variables and constants
x = {}; n = {}; f = {}; y = {}; w = {}; l = {}; d = {}
#Number of possible different capacities for a facility
facilityCapacities = 30
# When multiplied by facility-capacity value, returns the number of cars that the facility can hold. i.e 
# if the capacity is 7, then the number of cars the facility can hold is 7*capacityMultiplier
capacityMultiplier = 10
#Total number of time units the model will run for
totalTime = 24
#Ratio of distance to facility cost in objective function
alpha = 0.5

#Given the index of a capacity, returns the number of cars that that a facility of that
#capacity can hold.
def capacity(c):
	return capacityMultiplier * c

#Calculates the distance of the path a -> b    #CHANGE HERE
def distance((x0, y0), (x1, y1)):
	dx = x0 - x1
	dy = y0 - y1
	return math.sqrt(dx*dx + dy*dy)

#Returns the demand of cars going from client i to client j at time t.
def demand(i, j, t):
	if (t >= totalTime - 1): return 0
	else: return randint(0, 100)

#START MODEL

# This function is responsible for adding all the variables and constants that will be used
# by the model
def addVariables(m):
	
	#Variable X[k,c] binary variable which indicates if facility k of capacity c is open
	for k in xrange(numFacilities):
		for c in xrange(facilityCapacities):
			x[(k, c)] = m.addVar(vtype=GRB.BINARY, name="X_%d,%d" % (k, c))

	for c in xrange(facilityCapacities):
		#Variable indicating the number of cars that a facility of capacity c can hold
		n[c] = capacity(c)

	for k in xrange(numFacilities):
	#Variable f[k] cost of holding 1 car at facility k.
		f[k] = facilityUnitCosts[k]

	for t in xrange(totalTime):
		for i in xrange(numClients):
			for k in xrange(numFacilities):
				#Variable Y_(i,k,t) variable indicating number of cars that facility k sends to client i
				#at time t.
				y[(i,k,t)] = m.addVar(lb=0, vtype=GRB.INTEGER, name="Y_%d,%d,%d" % (i,k,t))
				#Variable W_(i,k,t) variable indicating number of cars that client i sends to facility k
				#at time t.
				w[(i,k,t)] = m.addVar(lb=0, vtype=GRB.INTEGER, name="W_%d,%d,%d" % (i,k,t))

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
	def r(k, ti): return quicksum(n[c]*x[(k,c)] for c in xrange(facilityCapacities)) + quicksum((w[(i,k,t)] - y[(i,k,t)]) for t in xrange(ti) for i in xrange(numClients)) 

	# Add constraints

	for k in xrange(numFacilities):
		#At most one size of a facility is open per location
		m.addConstr(quicksum(x[(k,c)] for c in xrange(facilityCapacities)) <= 1)

		for i in xrange(numClients):
			#At final time, cars can only return to open facilities
			m.addConstr(w[(i,k,totalTime - 1)] <= quicksum(n[c] * x[(k,c)] for c in xrange(facilityCapacities)))

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
	model.setObjective(quicksum(n[c]*x[(k, c)]*f[k] for c in xrange(facilityCapacities) for k in xrange(numFacilities)) + alpha * quicksum(w[(i, k, t)] + y[(i, k, t)] * d[(i, k)] for i in xrange(numClients) for k in xrange(numFacilities) for t in xrange(totalTime)) )
		#NOTE: may need to multiply here by x[k, c]

def printResults(model):
	vars = model.getVars()
	for var in vars:
		if(var.x != 0): print(var.varName + " = %.1f" % var.x)

def createTimeDict(d, md):
	for (i, j, t) in md.keys():
		var = md.get((i, j, t))
		if (var != None and var.x != 0):
			v = d.get(t)
			if (v != None):
				v.append((i, j, var.x))
			else:
				d[t] = [(i, j, var.x)]

def processResults():
	facToLoc = {}; locToFac = {}
	createTimeDict(facToLoc, y)
	createTimeDict(locToFac, w)
	return (facToLoc, locToFac)

#This function is responsible for setting up the model and invoking
#the Gurobi Optimizer on it.
# It returns tuple a, b, c, where:
# a : list of (k, c) where k is index of location and c is capactity, it only includes non-zero locations.
# b : dictionary (k, v) where k is the time unit and v is a list of tuples (x, y, z) which denote Y_(x, y, v)  = z.
# c : dictionary (k, v) where k is the time unit and v is a list of tuples (x, y, z) which denote W_(x, y, v)  = z.
def optimizeModel():
	m = Model()
	startModel(m)
	m.ModelSense = GRB.MINIMIZE
	m.optimize()
	#printResults(m)
	(b, c) = processResults() 
	a = [k for (k,l) in x if (x.get((k,l)).x != 0)]
	return (a, b, c)

(a, b, c) = optimizeModel()
