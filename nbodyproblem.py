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
    def __init__(self,name,position,velocity,mass,color):
        self.name = name #for code readability
        self.position = position #position is [x,y] array
        self.velocity = velocity #velocity is [x,y] array
        #there is no radius attribute, as this is calculated from the mass
        self.mass = mass #mass in solar masses
        self.color = color #RGB
        self.prevposition = position #Last known position (initialise as starting pos)
        self.nextposition = position
        self.nextvelocity = velocity
        self.alive = 1
    def addtolist(self): #add to planet list
        planetlist[self.name] = self        
    def removefromlist(self): #remove from planet list (eg: in case of collision)
        del planetlist[self.name]        
      
def makedustcloud(N,averagevel = 1, averagemass = 0.5):
    #randomly generate N planets with random properties and initial conditions
    for A in range(1,N+1):
        name = "planet"+str(A)
        randompos = np.random.uniform(low=-3.0, high=3.0, size = 2) #random position
        #here I add a slight bias for spiral movement, to make simulations more varied
        randomvel = np.random.normal(scale=averagevel,size = 2) + spiralbias(randompos) * np.random.normal(loc=0, scale=averagevel/3)
        #randomvel = np.random.normal(scale=averagevel,size = 2) #random velocity
        randomcolor = tuple(np.random.choice(range(256), size=3)) #random color
        randommass = abs(np.random.normal(loc=averagemass, scale=1))
        planetlist[name+"key"] = Planet(name, randompos, randomvel,randommass, randomcolor)
    return

def spiralbias(position):
    #creats a velocity bias perpendular to position vector
    pointer = np.array([ position[1], -1*position[0]])
    velscale = np.linalg.norm(position)
    if linalg.norm(pointer) == 0:
        pointer = np.array([0,0])
    else:
        pointer = pointer/linalg.norm(pointer)
    return velscale*pointer
    
def makesolarsystem():
    #Solarized color scheme by Ethan Schnoover
    orange = (203,75,22) #orange
    blue = (38, 139, 210) #blue
    green = (133,153,0) 
    
    #Set up Sun
    pos1 = np.array([ 0,0 ]) #initial position in centre of frame
    v1 = np.array([0,0])
    m1 = 1 #in SM units
    color1 = orange
    planetlist["Sun"] = Planet("Sun",pos1,v1,m1,color1)
    
    #Set up Earth
    pos2 = np.array([0,1])
    v2 = np.array([2*math.pi,0])
    m2 = 3.004e-6
    color2 = blue
    planetlist["Earth"] = Planet("Earth",pos2,v2,m2,color2)
    #planet2.addtolist()
    
    #Set up Jupiter
    pos3 = np.array([-4.203,0])
    v3 = np.array([-10.4*math.pi/11.86,0])
    m3 = 9.5e-4
    color3 = green
    #planetlist["Jupiter"] = Planet("Jupiter",pos3,v3,m3,color3)   
    return      
def maketestsystem():
    #Solarized color scheme by Ethan Schnoover
    orange = (203,75,22) #orange
    blue = (38, 139, 210) #blue
    green = (133,153,0) 
    
    #Set up Sun
    pos1 = np.array([ 1,0 ]) #initial position in centre of frame
    v1 = np.array([0,2])
    m1 = 2 #in SM units
    color1 = orange
    planetlist["Sun"] = Planet("Sun",pos1,v1,m1,color1)
    
    #Set up Earth
    pos2 = np.array([0,1])
    v2 = np.array([-3,0])
    m2 = 1
    color2 = blue
    planetlist["Earth"] = Planet("Earth",pos2,v2,m2,color2)
    #planet2.addtolist()
    
    #Set up Jupiter
    pos3 = np.array([0,-1])
    v3 = np.array([3,0])
    m3 = 0.8e-11
    color3 = green
    planetlist["Jupiter"] = Planet("Jupiter",pos3,v3,m3,color3)   
    return 
def draw(window,planetX,trailsurface,centerpos,scale,solarsystem):
    #draws a single planet (and its trail)
    #scale radius to mass (non-linearly) with minimum size of 0.02AU
    R = max(0.2*math.log(0.5* planetX.mass+1.1), 0.02)
    integerR = int(scale*R)
    integerpos = np.array([int((scale*planetX.nextposition+centerpos)[0]) , int((scale*planetX.nextposition+centerpos)[1])]) #add centerpos offset and round
    #draw trail (only if solarsystem == True)
    if solarsystem:
        #make R bigger for artistic license
         #PUT ALTERNATE R-EQUATION HERE
        #draw trails
        integerprevpos = np.array([int((scale*planetX.prevposition+centerpos)[0]) , int((scale*planetX.prevposition+centerpos)[1])])
        pygame.draw.line(trailsurface, planetX.color, integerprevpos, integerpos)
    pygame.draw.circle(window,planetX.color,integerpos,integerR)
    return

def grav(MovingPlanet, StationaryPlanet, G):
    #finds acceleration on body 1 due to another body
    #vector from 1 to 2:
    vector = MovingPlanet.position - StationaryPlanet.position
    pointer = vector/linalg.norm(vector) #unit vector pointing to 2 from 1
    distance = math.hypot(vector[0],vector[1]) #distance between the two
    accel = -G*StationaryPlanet.mass /(distance**2)
    accelvector = accel*pointer
    return accelvector

def EulerSimulate(MovingPlanet, StationaryPlanet,G,dt):
    if np.all(MovingPlanet.position == StationaryPlanet.position): #this should never happen, but just in case
        accel = 0
    else:
        accel = grav(MovingPlanet,StationaryPlanet,G)
    #quick but simple Euler algorithm for complex systems (EG: dustcloud)
    #note that we dont update the velocity/position immediately - this is so the
    #simulation occurs simultaneously for all planets, not sequentially
    MovingPlanet.nextvelocity = MovingPlanet.nextvelocity + accel*dt
    MovingPlanet.nextposition = MovingPlanet.nextposition + MovingPlanet.velocity*dt
    return (MovingPlanet)

def VerletSimulate(MovingPlanet, StationaryPlanet,G,dt):
    if np.all(MovingPlanet.position == StationaryPlanet.position): #this should never happen, but just in case
        accel = 0
    else:
        accel = grav(MovingPlanet,StationaryPlanet,G)
        x0 = MovingPlanet.position
        v0 = MovingPlanet.nextvelocity
        a0 = grav(MovingPlanet,StationaryPlanet,G)   # ay at beginning of interval
        MovingPlanet.position = x0 + v0*0.5*dt         # y at middle of interval
        vmid = v0 + a0*0.5*dt       # vy at middle of interval
        amid = grav(MovingPlanet,StationaryPlanet,G)                   # ay at middle of interval
        MovingPlanet.nextposition = MovingPlanet.nextposition + vmid * dt
        vf = amid * dt
        

        
    #quick but simple Euler algorithm for complex systems (EG: dustcloud)
    #note that we dont update the velocity/position immediately - this is so the
    #simulation occurs simultaneously for all planets, not sequentially
    MovingPlanet.nextvelocity = MovingPlanet.nextvelocity + amid*dt
    MovingPlanet.nextposition = MovingPlanet.nextposition + vf*dt
    MovingPlanet.position = x0 #reset position
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
    planetA.nextvelocity = totalmomentum/totalmass 
    planetA.nextposition = (planetA.mass*planetA.prevposition + planetB.mass*planetB.prevposition)/totalmass
    planetA.mass = totalmass     #this MUST come after planetA.nextposition
    planetA.color = mixcolor(planetA,planetB)     #mix colors together
    return planetA

def checkcollision(planetA,planetB):
    distance = np.linalg.norm(planetA.nextposition - planetB.nextposition)
    RA = max(0.2*math.log(0.5* planetA.mass+1.1), 0.02)
    RB = max(0.2*math.log(0.5* planetB.mass+1.1), 0.02)
    return distance < max((RA+RB)/2 , abs(RA-RB))

def main():
    (Nx, Ny) = (700,700) #initial window size
    scale = int( min( (Nx,Ny)) / 10) #scale to fit window
    centerpos = np.array([int(Nx/2), int(Ny/2)]) #origin of coordinate system
    
    G = 39.443 #gravitational constant using AU, years, Solar Mass
    dt = 0.1/365 #1 day/tick (we will later set the framerate to 0.1 years/second)   
##################### SET UP PLANETS #####################

    solarsystem = 0
    if solarsystem == 1:
        makesolarsystem()
        #scale = int( min( (Nx,Ny)) / 20)
    else:
        N=50
        makedustcloud(N,2)

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
    while True: #main simulation loop
        clock.tick(36.5) #set framerate to 1 year every 10 seconds (36.5 days/second)
        pygame.draw.circle(window,(255,255,255),(200,200),50)          
        for event in pygame.event.get(): #detect events
            if event.type == pygame.QUIT: #detect attempted exit
                pygame.quit()
                sys.exit()      #these 2 optional lines fix a hangup bug in IDLE  
            
            elif event.type == pygame.VIDEORESIZE: #detect resize
                (Nx, Ny) = event.size
                window = pygame.display.set_mode((Nx, Ny), pygame.RESIZABLE)
#                trail_layer = pygame.Surface([Nx, Ny], pygame.SRCALPHA|pygame.RESIZABLE) #make transparent overlayer
                pygame.transform.scale(trailsurface, (Nx,Ny))   
                window.blit(trailsurface, (0, 0))
                
                scale = int( min( (Nx,Ny)) / 10)
                centerpos = np.array([int(Nx/2), int(Ny/2)])
        
        #the up and down arrow keys increase and decrease dt respectively
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[273]:
            dt *= 1.05
        if pressed_keys[274]:
            #dt /= 1.05
            for planet in planetlist:
                planetlist[planet].removefromlist()
        if pressed_keys[114]:
            #restart dustcloud
            
            trailsurface.fill((255,255,255,0))
            window.blit(trailsurface, (0,0))
            makedustcloud(N)
            solarsystem = 0
        window.fill((bgcolor)) #blank screen
               
      #####################SIMULATION STEP######################
        for planet in planetlist: #updates prevpositions
            planetlist[planet].prevposition = planetlist[planet].position 
            if len(planetlist) == 1: #this edge case puts the last planet on a straight line trajectory
                planetlist[planet].nextposition = planetlist[planet].nextposition + planetlist[planet].velocity*dt 
        
        #iterates through all combinations of 2-planet pairs  
        for activeplanet in list(planetlist.keys()):
            for otherplanet in planetlist:
                if activeplanet != otherplanet and not checkcollision(planetlist[activeplanet],planetlist[otherplanet]):
                    if solarsystem == 1:
                        planetlist[activeplanet] = VerletSimulate(planetlist[activeplanet],planetlist[otherplanet],G,dt)
                    else:
                        planetlist[activeplanet] = EulerSimulate(planetlist[activeplanet],planetlist[otherplanet],G,dt)
                    
    
        #very clumsy/messy way to handle merging - come back and improve?
        for couple in itertools.combinations(planetlist,2):
            planet1 = couple[0]
            planet2 = couple[1]
            if checkcollision(planetlist[planet1],planetlist[planet2]):
                #print("Merging ", planetlist[planet1].name , "with",planetlist[planet2].name )
                planetlist[planet1] = mergeplanets(planetlist[planet1],planetlist[planet2])                     
                planetlist[planet1].name += planetlist[planet2].name
                planetlist[planet2].alive = 0 
        
        #delete all mass = 0 planets
        for planet in list(planetlist.keys()):
            if planetlist[planet].alive == 0:
                del planetlist[planet] 
                
        for planet in planetlist:
            #apply changes simultaneously, and draw final result
            planetlist[planet].velocity = planetlist[planet].nextvelocity
            planetlist[planet].position = planetlist[planet].nextposition
            draw(window,planetlist[planet],trailsurface,centerpos,scale,solarsystem) 

#OPTIONAL FPS CLOCK:
        if solarsystem == 1:
            fps = font.render("FPS: "+str(int(clock.get_fps())), True, pygame.Color('white'))
            window.blit(fps,(50, 50))
        window.blit(trailsurface, (0, 0)) #paste trails onto window
        pygame.display.update() #update screen
        

#run function as script
if __name__ == '__main__':
    main()