# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 18:40:24 2019
Better 3-body problem
@author: Antiochian

This project was intended as a simpler task before attempting to write the 
superior "betterorbits" program. This program has several flaws and limitations.

    1. A simple and inaccurate Euler algorithm is used
    2. Planets are EulerSimulated sequentially, not simultaneously
    3. There is no collision/coalescence functionality for when 2 planets collide
    4. There is no GUI.
    5. There is no easy way to add or remove planets
    6. Object classes are not used
    
"""

import math
import numpy as np
from numpy import linalg
import itertools
import pygame
import sys

 #create dictionary of all current planets for each mode
planetlist = {}
class Planet: #PLANET OBJECT
    def __init__(self,name,position,velocity,mass,color,manualradius=0):
        self.name = name #for code readability
        self.position = position #position is [x,y] array
        self.velocity = velocity #velocity is [x,y] array
        self.vmid = np.array([0,0]) #start this at zero
        self.manualradius = manualradius #this is only used in the solar system model, as if radii were to scale the planets would be too small to see
        self.mass = mass #mass in solar masses
        self.color = color #RGB
        self.prevposition = position #Last known position (initialise as starting pos)
        self.nextposition = position
        self.alive = 1
    def addtolist(self): #add to planet list
        planetlist[self.name] = self        
    def removefromlist(self): #remove from planet list (eg: in case of collision)
        del planetlist[self.name]        
      
def makedustcloud(N,averagevel = 4, averagemass = 0.5):
    #randomly generate N planets with random properties and initial conditions
    for A in range(1,N+1):
        name = "planet"+str(A)
        randompos = np.random.uniform(low=-3.0, high=3.0, size = 2) #random position
        #here I add a slight bias for spiral movement, to make simulations more varied
        randomvel = np.random.normal(scale=averagevel,size = 2) + spiralbias(randompos) * np.random.normal(loc=0, scale=averagevel/3)
        randomcolor = tuple(np.random.choice(range(256), size=3)) #random color
        randommass = abs(np.random.normal(loc=averagemass, scale=1))
        planetlist[name+"key"] = Planet(name, randompos, randomvel,randommass, randomcolor)
    return

def spiralbias(position):
    #creats a velocity bias perpendular to position vector
    pointer = np.array([ position[1], -1*position[0]])
    velscale = np.linalg.norm(position)*3
    if linalg.norm(pointer) == 0:
        pointer = np.array([0,0])
    else:
        pointer = pointer/linalg.norm(pointer)
    return velscale*pointer
    
def makesolarsystem():
    #Solarized color scheme by Ethan Schnoover
    yellow = (181,137,0)
    beige = (238,232,213)
    orange = (203,75,22) #orange
    blue = (38, 139, 210) #blue
    red =  (220,50,47)
    green = (133,153,0) 
    grey = (88,	110, 117)
    #Set up Sun
    pos1 = np.array([ 0,0 ]) #initial position in centre of frame
    v1 = np.array([0,0])
    m1 = 1 #in SM units
    color1 = orange
    manualradius1=0.15
    planetlist["Sun"] = Planet("Sun",pos1,v1,m1,color1,manualradius1)
    
    #Set up Halleys Comet
    posH = 0.586*np.array([-1,0])
    vH = 11.38*np.array([0,-1])
    mH = 1.1e-16
    colorH = grey
    planetlist["Halleys_Comet"] = Planet("Halleys_Comet",posH,vH,mH,colorH)
    
    #Set up Mercury
    pos1 = np.array([0.3953,0])
    v1 = np.array([0,-9.989])
    m1 = 1.66e-7
    color1 = beige
    manualradius1= 0.03
    planetlist["Mercury"] = Planet("Mercury",pos1,v1,m1,color1,manualradius1)
    
    #Set up Venus
    pos2 = np.array([0.723,0])
    v2 = np.array([0,-7.38])
    m2 = 2.448e-6
    color2 = green
    manualradius2 = 0.07
    planetlist["Venus"] = Planet("Venus",pos2,v2,m2,color2,manualradius2)
    
    #Set up Earth
    pos3 = np.array([1,0])
    v3 = np.array([0,-2*math.pi])
    m3 = 3.004e-6
    color3 = blue
    manualradius3 = 0.08
    planetlist["Earth"] = Planet("Earth",pos3,v3,m3,color3,manualradius3)
    
    #Set up Mars
    pos4 = np.array([1.5323,0])
    v4 = np.array([0,-5.08])
    m4 = 3.227e-7
    color4 = red
    manualradius4 = 0.04
    planetlist["Mars"] = Planet("Mars",pos4,v4,m4,color4,manualradius4)    
    
    #Set up Jupiter
    pos5 = np.array([5.209,0])
    v5 = np.array([0,-2.75])
    m5 = 9.55e-4
    color5 = yellow
    manualradius5 = 0.1
    planetlist["Jupiter"] = Planet("Jupiter",pos5,v5,m5,color5,manualradius5)   
    return      

def draw(window,planetX,trailsurface,centerpos,scale,solarsystem):
    #draws a single planet (and its trail)
    #scale radius to mass (non-linearly) with minimum size of 0.02AU
    if solarsystem ==1:
        R = planetX.manualradius
    else: #for dustcloud, use less exaggerated scale (so collisions happen more often)
        R = max(0.2*math.log(0.5* planetX.mass+1.1), 0.02)
    integerR = int(scale*R)
    integerpos = np.array([int((scale*planetX.nextposition+centerpos)[0]) , int((scale*planetX.nextposition+centerpos)[1])]) #add centerpos offset and round
    if solarsystem: #add trails if Solarsystem model is being used
        integerprevpos = np.array([int((scale*planetX.prevposition+centerpos)[0]) , int((scale*planetX.prevposition+centerpos)[1])])
        pygame.draw.line(trailsurface, planetX.color, integerprevpos, integerpos)
    pygame.draw.circle(window,planetX.color,integerpos,integerR)
    return

def grav(position, StationaryPlanet, G):
    #finds acceleration on body 1 due to another body
    #vector from 1 to 2:
    vector = position - StationaryPlanet.position
    #vector2 = vector / max(min(abs(vector)),1e5)
    pointer = vector/linalg.norm(vector) #unit vector pointing to 2 from 1
    distance = math.hypot(vector[0],vector[1]) #distance between the two
    accel = -G*StationaryPlanet.mass /(distance**2)
    accelvector = accel*pointer
    return accelvector

def VerletSimulate(MovingPlanet, StationaryPlanet,G,dt):
    if np.all(MovingPlanet.position == StationaryPlanet.position): #this should never happen, but just in case
        MovingPlanet.nextposition = MovingPlanet.nextposition + MovingPlanet.velocity*dt       
    elif StationaryPlanet.mass > 1e-12: #arbritary value below which planets are treated as having 0 mass
        xmid = MovingPlanet.position + MovingPlanet.velocity*0.5*dt
        vmid = MovingPlanet.velocity + grav(MovingPlanet.position,StationaryPlanet,G)*0.5*dt
        amid = grav(xmid,StationaryPlanet,G)                   
        #print(MovingPlanet.name," being pulled by ", StationaryPlanet.name,"\n     Delta-V = ",amid*dt,"\n     Delta-Pos = ",vmid*dt)
        MovingPlanet.velocity = MovingPlanet.velocity + amid*dt
        MovingPlanet.vmid = vmid 
    return (MovingPlanet)

def mixcolor(planetA,planetB):
    #mixes colors, the more massive the planet, the more weight its color has
    colorC = [0,0,0]
    for i in range(3):
        colorC[i] = int((planetA.mass*planetA.color[i]+planetB.mass*planetB.color[i])/(planetA.mass+planetB.mass))   
    return tuple(colorC)

def mergeplanets(planetA, planetB):
    #planetA survives, planetB dies
    totalmass = planetA.mass + planetB.mass
    #conserve x and y momentum
    totalmomentum = planetA.mass*planetA.velocity + planetB.mass*planetB.velocity
    planetA.velocity = totalmomentum/totalmass 
    planetA.nextposition = (planetA.mass*planetA.prevposition + planetB.mass*planetB.prevposition)/totalmass
    planetA.mass = totalmass     #this MUST come after planetA.nextposition
    planetA.color = mixcolor(planetA,planetB)     #mix colors together
    return planetA

def checkcollision(planetA,planetB):
    distance = np.linalg.norm(planetA.position - planetB.position)
    RA = max(0.2*math.log(0.5* planetA.mass+1.1), 0.02)
    RB = max(0.2*math.log(0.5* planetB.mass+1.1), 0.02)
    return distance < max((RA+RB)/2 , abs(RA-RB))

def main():
    (Nx, Ny) = (700,700) #initial window size
    centerpos = np.array([int(Nx/2), int(Ny/2)]) #origin of coordinate system
    
    G = 39.443 #gravitational constant using AU, years, Solar Mass
    dt = 0.05/365 #1 day/tick (we will later set the framerate to 0.1 years/second)   
##################### SET UP PLANETS #####################

    solarsystem = 1
    N=30
    if solarsystem == 1:
        makesolarsystem()
        scale = int( min( (Nx,Ny)) / 12)
    else:
        makedustcloud(N,2)
        scale = int( min( (Nx,Ny)) / 10) #scale to fit window
    bgcolor = (0, 43, 54) #base03
    
    pygame.init()
    window = pygame.display.set_mode((Nx, Ny), pygame.RESIZABLE)
    pygame.display.set_caption('Press X to exit')
    window.fill(bgcolor)
    pygame.display.update()
    
    trailsurface = pygame.Surface([Nx, Ny], pygame.SRCALPHA|pygame.RESIZABLE)
    trailsurface.fill((255,255,255,0))   
    window.blit(trailsurface, (0, 0))
    
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30) #only used for FPS clock
    
    maxFPS = 200
    ######## MAIN SIMULATION LOOP #########
    while True: #main simulation loop
        clock.tick(maxFPS) #set framerate to 1 year every 10 seconds (36.5 days/second)
        pygame.draw.circle(window,(255,255,255),(200,200),50)          
        for event in pygame.event.get(): #detect events
            if event.type == pygame.QUIT: #detect attempted exit
                pygame.quit()
                sys.exit()      #these 2 optional lines fix a hangup bug in IDLE  
            
            elif event.type == pygame.VIDEORESIZE: #detect resize
                (Nx, Ny) = event.size
                window = pygame.display.set_mode((Nx, Ny), pygame.RESIZABLE)
                trailsurface = pygame.Surface([Nx, Ny], pygame.SRCALPHA|pygame.RESIZABLE) #make transparent overlayer
                trailsurface.fill((255,255,255,0))     
                window.blit(trailsurface, (0, 0))   
                scale = int( min( (Nx,Ny)) / 10)
                centerpos = np.array([int(Nx/2), int(Ny/2)])
        
        #the up and down arrow keys increase and decrease dt respectively
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[273] and solarsystem == 0:
            scale *= 1.05
        if pressed_keys[274] and solarsystem == 0:
            scale *= 0.95
        if pressed_keys[114]: #R keypress
            #SWITCH TO DUSTCLOUD SIMULATION
            maxFPS=20
            dt = 0.5/365
            planetlist.clear()
            trailsurface.fill((255,255,255,0))
            window.blit(trailsurface, (0,0))
            makedustcloud(N)
            scale = int( min( (Nx,Ny)) / 10) #scale to fit window
            solarsystem = 0
        window.fill((bgcolor)) #blank screen
        if pressed_keys[115]: #S keypress
            #SWITCH TO SOLARSYSTEM
            maxFPS=180
            dt = 0.05/365
            planetlist.clear()
            trailsurface.fill((255,255,255,0))
            window.blit(trailsurface, (0,0))
            makesolarsystem()
            scale = int( min( (Nx,Ny)) / 12) #scale to fit window
            solarsystem = 1      
      #####################SIMULATION STEP######################
        for planet in planetlist: #updates prevpositions
            planetlist[planet].prevposition = planetlist[planet].position 
            planetlist[planet].nextposition = planetlist[planet].position
            if len(planetlist) == 1: #this edge case puts the last planet on a straight line trajectory
                planetlist[planet].nextposition = planetlist[planet].nextposition + planetlist[planet].velocity*dt 
        
        #iterates through all combinations of 2-planet pairs  
        for activeplanet in list(planetlist.keys()):
            for otherplanet in planetlist:
                if activeplanet != otherplanet and not checkcollision(planetlist[activeplanet],planetlist[otherplanet]):
                    planetlist[activeplanet] = VerletSimulate(planetlist[activeplanet],planetlist[otherplanet],G,dt)
        
        for couple in itertools.combinations(planetlist,2): #Check for collisions
            planet1 = couple[0]
            planet2 = couple[1]
            if checkcollision(planetlist[planet1],planetlist[planet2]) and solarsystem ==0:
                #print("Merging ", planetlist[planet1].name , "with",planetlist[planet2].name )
                planetlist[planet1] = mergeplanets(planetlist[planet1],planetlist[planet2])                     
                planetlist[planet1].name += planetlist[planet2].name
                planetlist[planet2].alive = 0 
        #delete all mass = 0 planets
        for planet in list(planetlist.keys()):
            if planetlist[planet].alive == 0:
                del planetlist[planet] 
                
        for planet in planetlist: #update positions and draw to surface
            planetlist[planet].position = planetlist[planet].nextposition = planetlist[planet].nextposition+planetlist[planet].vmid*dt     
            draw(window,planetlist[planet],trailsurface,centerpos,scale,solarsystem) 

#OPTIONAL FPS CLOCK:
        fps = font.render("FPS: "+str(int(clock.get_fps())), True, pygame.Color('white'))
        window.blit(fps,(50, 50))
        window.blit(trailsurface, (0, 0)) #paste trails onto window
        pygame.display.update() #update screen
        

#run function as script
if __name__ == '__main__':
    main()
