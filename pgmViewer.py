# pgmViewer.py
# Display PGM File and Convert to JPEG
# Designed by David Guidos, Jan 2018

import sys  
import numpy
import time
import os
import pygame

#   P Y G A M E
#
# set canvas parameters
size = width, height = 300, 300
speed = [100, 100]

redColor = pygame.Color(255, 0, 0)
blueColor = pygame.Color(0, 0, 255)
greenColor = pygame.Color(0, 255, 0)
blackColor = pygame.Color(0, 0, 0)
whiteColor = pygame.Color(255, 255, 255)
grayColor = pygame.Color(150, 150, 150)

#   P G M   F I L E
#
# get pgm file to a string
def pgmString(pgmFileName):
    pgm_string = ""
    with open(pgmFileName, "r") as pgmFile:
        pgm_string = pgmFile.read()
    return pgm_string   

# get image data (width, height and max value)
def pgmSpecs(pgmImageString):
    if pgmString != "":
        pgmList = pgmImageString.split()
        xSize =int(pgmList[1])
        ySize =int(pgmList[2])
        maxValue = int(pgmList[3])
    else:
        xSize = 0
        ySize = 0
        maxValue = 0        
    return (xSize, ySize, maxValue)       

# draw the pgm image on a pygame surface 
# (doubles the size in both directions to make it larger)
def drawPGM(xy, pgmImageString, thermalLabel, screen):
    (x0, y0) = xy
    if pgmImageString != "":
        pgmList = pgmImageString.split()
        hdrP2 = pgmList[0]
        (xSize, ySize, maxValue) = pgmSpecs(pgmImageString)
        # double size in both x and y directions
        for n in range(4, len(pgmList)):
            x = (n - 4) % xSize
            y = int((n - 4) / xSize)
            x = x * 2
            y = y * 2
            grayLevel = int(pgmList[n])
            graylevel = int(grayLevel * 255 / maxValue)
            if grayLevel > 255:
                grayLevel = 255
            if grayLevel < 0:
                grayLevel = 0
            c = (grayLevel, grayLevel, grayLevel)
            screen.set_at((x0 + x, y0 + y), c)
            screen.set_at((x0 + x + 1, y0 + y), c)
            screen.set_at((x0 + x, y0 + y + 1), c)
            screen.set_at((x0 + x + 1, y0 + y + 1), c)
        screen.blit(thermalLabel, (x0, y0 + ySize * 2 + 10))

def saveImageToFile(xy, wh, imageFileName, screen):
    # save the image as a JPEG
    imageRect = pygame.Rect(xy, wh)
    imageSubscreen = screen.subsurface(imageRect)
    pygame.image.save(imageSubscreen, imageFileName + '.jpg')    


#   M A I N
# get the parameters
imageFileName = 'IMG_0001'
if len(sys.argv) > 1:
    imageFileName = sys.argv[1]

# initialize the game engine
pygame.init( )

# display title on canvas and clear the display
pygame.display.set_caption("PGM Viewer")
screen = pygame.display.set_mode(size)
screen.fill(whiteColor)

gameFont = pygame.font.SysFont("monospace", 15)
gameFont2 = pygame.font.SysFont("monospace", 30)

# create text
pgmLabel = gameFont.render("PGM Image", 1, blackColor)

# render the surface
pygame.display.flip()
  
#start = time.time()
abort = False
while not abort:
    try:
        # clear the canvas
        screen.fill(whiteColor)

        # display the image
        imageString = pgmString(imageFileName + '.pgm')
        xy = (50, 50)
        drawPGM(xy, imageString, pgmLabel, screen)

        # update the display
        pygame.display.flip()
        pygame.display.update()
        
        # save the image as a jpeg
        (xSize, ySize, maxValue) = pgmSpecs(imageString)
        saveImageToFile(xy, (xSize * 2, ySize * 2), imageFileName, screen)

        abort = True
    except (KeyboardInterrupt):
        abort = True

