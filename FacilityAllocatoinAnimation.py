from Tkinter import *
from math import sqrt
import Tkinter as tk
import FacillityAllocationWithDemandsAndTime as FacAlloc
import time


facilityLocations = [(50, 75), (50, 255), (200, 215), (400, 300), (510, 65), (100, 450), (340, 50), (490, 350), (500, 500)]
clientLocations = [(100, 110), (120, 388), (413, 180), (500, 520)]
w = 40


class Facility(object):
    def __init__(self, canvas, i, b, **kwargs):
        self.canvas = canvas
        (x0, y0) = facilityLocations[i]
        self.x0 = x0
        self.y0 = y0
        self.color = "black" if b else "grey"
        self.id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + w, outline = self.color)
        self.text = self.canvas.create_text(x0 + w/2, y0 + w/2, text=str(i), anchor = tk.CENTER, fill = self.color)

    def updateText(self, newVal):
        self.canvas.delete(self.text)
        self.text = self.canvas.create_text(self.x0 + w/2, self.y0 + w/2, text=newVal, anchor = tk.CENTER, fill = self.color)

    # def update(self):
    #     x1, y1, x2, y2 = self.canvas.bbox(self.id)
    #     if x2 > 400: self.vx = -5
    #     if x1 < 0: self.vx = 5
    #     self.canvas.move(self.id, self.vx, self.vy)

class Client(object):
    def __init__(self, canvas, i, **kwargs):
        self.canvas = canvas
        (x0, y0) = clientLocations[i]
        self.id = self.canvas.create_oval(x0, y0, x0 + w, y0 + w)
        self.x0 = x0
        self.y0 = y0
        self.text = self.canvas.create_text(x0 + w/2, y0 + w/2, text=str(i), anchor = tk.CENTER)

    def updateText(self, newVal):
        self.canvas.delete(self.text)
        self.text = self.canvas.create_text(self.x0 + w/2, self.y0 + w/2, text=newVal, anchor = tk.CENTER)

class DemandLine(object):
    def __init__(self, canvas, i, j, demand, **kwargs):
        self.canvas = canvas
        (x0, y0) = clientLocations[i]
        (x1, y1) = clientLocations[j]
        self.i = i
        self.j = j
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        off = 0 if i < j else 8
        if (x0 < x1):
            self.id = self.canvas.create_line(x0 + w, y0 + w/2 + off, x1, y1 + w/2 + off, **kwargs)
        else:
            self.id = self.canvas.create_line(x0, y0 + w/2 + off, x1 + w, y1 + w/2 + off, **kwargs)
        x_diff = x1 - x0; y_diff = y1 - y0
        self.text = self.canvas.create_text(x0 + w/2+ x_diff/2, y0+ w/2 + y_diff/2 + off, text= "", anchor = tk.CENTER)


    def delete(self):
        self.canvas.delete(self.id)

    def updateText(self, time):
        self.canvas.delete(self.text)
        off = -5 if self.i < self.j else 5
        x_diff = self.x1 - self.x0; y_diff = self.y1 - self.y0
        val = FacAlloc.demand(self.i, self.j, time)
        self.text = self.canvas.create_text(self.x0 + w/2+ x_diff/2, self.y0+ w/2 + y_diff/2 + off, text= str(val), anchor = tk.CENTER)

class FlowLine(object):
    def __init__(self, canvas, i, k, v, o, **kwargs):
        self.canvas = canvas

        (x0, y0) = clientLocations[i]
        (x1, y1) = facilityLocations[k]
        if (o == 1): off = 1
        else: off = -1
        self.id = self.canvas.create_line(x0 + w/2, y0 + w/2 + off, x1 + w/2, y1 + w/2 + off, **kwargs)

    def delete(self):
        self.canvas.delete(self.id)

class App(object):
    def __init__(self, master, **kwargs):
        (self.xLoc, self.y, self.w) = FacAlloc.optimizeModel()

        self.master = master
        self.canvas = tk.Canvas(self.master, width = 600, height = 600)
        self.canvas.pack()
        self.time = 0
        # self.step = 20
        self.drawDemands()
        self.createFacilities()
        self.createClients()
        self.canvas.pack()
        self.master.after(0, self.animation)

    def createFacilities(self):
        self.facilities = [Facility(self.canvas, i, (1 if i in self.xLoc else 0)) for i in range(len(facilityLocations))]

    def createClients(self):
        self.clients = [Client(self.canvas, i) for i in range(len(clientLocations))]

    def drawDemands(self):
        self.currentDemands = [DemandLine(self.canvas, i, j, FacAlloc.demand(i, j, 0), arrow=tk.FIRST) for i in range(len(clientLocations)) for j in range(len(clientLocations)) if (i != j)]

    def updateDemands(self, time):
        for demand in self.currentDemands: demand.updateText(time)

    def drawYIKT(self, time):
        self.currentYIKT = []
        if (self.y.get(time) != None):
            for (i, k ,v) in self.y[time]:
                self.currentYIKT.append(FlowLine(self.canvas, i, k, v, 1, fill="blue", arrow=tk.FIRST, width = 2))

    def drawWIKT(self, time):
        self.currentWIKT = []
        if (self.w.get(time) != None):
            for (i, k , v) in self.w[time]:
                self.currentWIKT.append(FlowLine(self.canvas, i, k, v, 0, fill="red", arrow=tk.LAST, width = 2))

    def animation(self):
        currTime = self.time % 10
        # if (time % self.step == 0):
        #     self.drawSIT(currTime)
        if (currTime == 0):
             self.updateDemands(self.time/10)
        if (currTime == 3):
             self.drawYIKT(self.time/10)
        if (currTime == 6):
            self.drawWIKT(self.time/10)
        if (currTime == 9):
            for line in self.currentYIKT:
                line.delete()
            for line in self.currentWIKT:
                line.delete()
        #self.drawYIKT(time)
        #self.drawWIKT(time)
        #self.drawSIT(time)
        # for line in self.flowLines:
        #     # line.update()
        # for facility in self.facilities:
        #     # facility.update()
        # for client in self.clients:
        #     # client.update()
        self.time += 1
        self.master.after(300, self.animation)


root = tk.Tk()
app = App(root)
root.mainloop()