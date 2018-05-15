#   F L I R   T H E R M A L   I M A G E   R O U T I N E S
#   Designed by David Guidos, Dec 2017
#   imageFileName = 'IMG_0000.pgm'

import os
from subprocess import check_call
import pygame

class FLIRLepton(object):

    def __init__(self):
        self.currentThermalImageString = ""
        self.previousThermalImageString = ""

    def captureThermalImage(self, pgmFileName):
        check_call('./raspberrypi_capture')
        pgm_string = self.pgmString(pgmFileName)
        if pgm_string != "":
            self.previousThermalImageString = self.currentThermalImageString
            self.currentThermalImageString = pgm_string
        os.remove(pgmFileName)
        
    def pgmString(self, pgmFileName):
        pgm_string = ""
        with open(pgmFileName, "r") as pgmFile:
            pgm_string = pgmFile.read()
        return pgm_string          

    def drawPGM(self, xy, pgmImageString, screen):
        (x0, y0) = xy
        if pgmImageString != "":
            pgmList = pgmImageString.split()
            hdrP2 = pgmList[0]
            xSize =int(pgmList[1])
            ySize =int(pgmList[2])
            maxValue = int(pgmList[3])
            # double size in both x and y directions
            for n in range(4, len(pgmList)):
                x = (n - 4) % xSize
                y = int((n -4) / xSize)
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

    def thermalImageAnomalyDetected(self):
        # check for significant thermal activity
        variationCount = 0
        if self.currentThermalImageString != "" and self.previousThermalImageString != "":
            currentList = self.currentThermalImageString.split()
            previousList = self.previousThermalImageString.split()
            for n in range(4, len(currentList)):
                if abs(int(currentList[n]) - int(previousList[n])) > 8:
                    variationCount += 1
        return (variationCount > 128)

