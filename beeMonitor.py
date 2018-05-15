#!/usr/bin/env python
# -*- coding: utf-8 -*-

# beeMonitor.py
# Bee Monitor - Detects Bees Using a Microphone to Listen for a Characteristic Buzzing Frequency
#               Bees buzz at 190 Hz ... 250 Hz. Allowance made for doppler effects of moving bees.
# Designed by David Guidos, 2017

import sys  
import numpy
import time
import json
import pyaudio
import pygame
import argparse
import os
from subprocess import check_call
from FLIRLepton import FLIRLepton
import HologramNova
  
# get command line arguments
#parser = argparse.ArgumentParser(description='Arguments for BeeDetector.')
#parser.add_argument('usePyGame', metavar='N', type=bool, nargs=1,
#                    help='Display grahical data?')
#args = parser.parse_args()

# functional set up
# TODO: set up as command line parameters
usePyGame = True
useNova = False
useThermal = True
samplesPerPublish = 20  # audio samples before publishing to Hologram Nova

# audio set up
mic = None
FS=44100       # sampling frequency; standard CD rate
SAMPLES=1024   # approx 20 sample packets / sec. if not overlapped using a callback, processing lowers to approx. 20 / sec
MIC_DEVICE = 1 # TODO: enumerate to find mic device?

# bee detection variables
beeMinFFTIndex = 30
beeMaxFFTIndex = 37

#   P Y G A M E
#
# set canvas parameters
size = width, height = 1100, 700
speed = [100, 100]

redColor = pygame.Color(255, 0, 0)
blueColor = pygame.Color(0, 0, 255)
greenColor = pygame.Color(0, 255, 0)
blackColor = pygame.Color(0, 0, 0)
whiteColor = pygame.Color(255, 255, 255)
grayColor = pygame.Color(150, 150, 150)



#   A U D I O
#
def get_audioSample():
    global mic
    sampleData = []
    if mic is None:
        pa = pyaudio.PyAudio()
        mic = pa.open(format=pyaudio.paInt16, channels=1, rate=FS,
                      input_device_index = MIC_DEVICE, input=True,
                      frames_per_buffer=SAMPLES)
        #mic = pa.open(format=pyaudio.paInt16, channels=1, rate=FS,
        #              input=True, frames_per_buffer=SAMPLES * 64)
    try:
        mic.start_stream()
        sampleString = mic.read(SAMPLES)
        sampleData = numpy.fromstring(mic.read(SAMPLES), dtype=numpy.short)
        mic.stop_stream()
    except IOError as ex:
        raise
    return sampleData
    #return numpy.fromstring(mic.read(SAMPLES), dtype=numpy.short)

def get_powerSpectrum(amplitudes):
    return abs(numpy.fft.fft(amplitudes / 32768.0))[:int(SAMPLES/2)]

def plot_sound(amplitudes):
    # show title
    screen.blit(soundLabel, (10, 10))
    # determine canvas positions
    yUsable = (height / 2) - 60
    yRange = yUsable / 2
    yBase = 10
    x = -1
    maxAmplitude = max(max(amplitudes), -min(amplitudes))
    previousY = 0
    for amplitude in amplitudes:
        x += 1
        #y = (-float(amplitude) / float(maxAmplitude)) * yRange   # for automatic scaling
        y = (-float(amplitude) / 4096.0) * yRange   # fixed scaling
        # plot this amplitude
        #lineRect = pygame.draw.line(screen, blueColor, (x + 10, yRange + y + 10), (x + 10, yRange - y + 10), 1)
        lineRect = pygame.draw.line(screen, blueColor, (x + 10, yBase + yRange + previousY), (x + 10, yBase + yRange + y), 1)
        previousY = y
    #print max(amplitudes)

def plot_powerSpectrum(powerArray):  
    # show title
    screen.blit(spectrumLabel, (10, 330))
    screen.blit(spectrumFrequencies, (10, height - 25))
    # determine canvas positions
    yUsable = (height / 2) - 60
    yBase = height - 40
    x = -1
    freqIndex = powerArray.argmax(axis=0)   # primary frequency
    maximumPower = max(powerArray)
    print ("Freq Index: " + str(freqIndex))
    for powerValue in powerArray:
        x += 1
        y = powerValue / maximumPower * yUsable
        if (x == freqIndex):
            # show power level for primary sample frequency in red
            lineColor = redColor
        else:
            # normal power levels in black
            lineColor = blackColor
        # plot the power level for this sample value
        lineRect = pygame.draw.line(screen, lineColor, (x + 10, yBase), (x + 10, yBase - y), 1)

def plot_detectionLevels(levels):
    yUsable = (height / 3) - 60
    yBase = height - 40
    xBase = width - 500
    x = -1
    maximumLevel = 50 # max(levels)
    lineColor = blueColor
    previousY = -1
    for level in levels:
        x += 1
        y = float(level) / float(maximumLevel) * float(yUsable)
        if previousY == -1:
            previousY = y
        # plot the detection level for this sample value 
        lineRect = pygame.draw.line(screen, lineColor, (xBase + (x - 1) * 2, yBase - previousY), (xBase + x * 2, yBase - y), 1)       
        previousY = y
    
def detectBees(frequencyIndex, previousFrequencyIndex):
    if (frequencyIndex >= beeMinFFTIndex) and (frequencyIndex <= beeMaxFFTIndex) and (previousFrequencyIndex >= beeMinFFTIndex) and (previousFrequencyIndex <= beeMaxFFTIndex):
        beesDetected = 1
    else:
        beesDetected = 0
    return beesDetected


    
#   M A I N

# init the game engine
if usePyGame:
    pygame.init( )

    # display title on canvas and clear the display
    pygame.display.set_caption("Bee Monitor")
    screen = pygame.display.set_mode(size)
    screen.fill(whiteColor)

    gameFont = pygame.font.SysFont("monospace", 15)
    gameFont2 = pygame.font.SysFont("monospace", 30)

    # create text
    soundLabel = gameFont.render("Sound data", 1, blackColor)
    spectrumLabel = gameFont.render("Power spectrum", 1, blackColor)
    spectrumFrequencies = gameFont.render("0Hz  5kHz 10kHz 15kHz 20kHz 25kHz 30kHz 35kHz 40kHz 45kHz", 1, blueColor)
    thermalLabel = gameFont.render("Thermal Images", 1, blackColor)

    # create bee image
    beeImage = pygame.image.load("bee.png")

    # render the surface
    pygame.display.flip()

if useThermal:
    flir = FLIRLepton()
  
#start = time.time()
abort = False
currentBees = 0
detectionLevels = []
previousFrequencyIndex = 0
sampleCount = 0
beesDetectedCount = 0
while not abort:
    try:
        amplitudes = get_audioSample()
        print("Amplitudes: ", amplitudes)
        if len(amplitudes) != 0:
            power = get_powerSpectrum(amplitudes)
            primaryFrequencyIndex = power.argmax(axis=0)
            # detect bees
            beesDetected = detectBees(primaryFrequencyIndex, previousFrequencyIndex)
            beesDetectedCount += beesDetected
            previousFrequencyIndex = primaryFrequencyIndex
            sampleCount += 1
            # update bee detection level
            if beesDetected == 1:
                currentBees += 2
            else:
                currentBees -= 1
                if currentBees < 0:
                    currentBees = 0
            print ("Bee Detection Index: " + str(currentBees))
            
            # put current bee detection level into the detection levels array
            # limits the size to 200 elements
            detectionLevels.append(currentBees)
            if len(detectionLevels) > 200:
                detectionLevels.pop(0)
            
            # display bee level
            if usePyGame:
                beesDetectedLabel = gameFont.render("Bee Detection Index: ", 1, blackColor)
                beesDetectedValue = gameFont2.render(str(currentBees), 1, redColor)

                # clear the canvas
                screen.fill(whiteColor)
                            
                # show bees detected
                screen.blit(beesDetectedLabel, (600, 330))
                screen.blit(beesDetectedValue, (800, 320))

                # show bee image
                beeImageScaled = pygame.transform.scale(beeImage, (5 * currentBees + 25, 5 * currentBees + 25))
                screen.blit(beeImageScaled, (600, 360))
            
                # display the sound data
                plot_sound(amplitudes)
            
                # display the sound spectrum
                plot_powerSpectrum(power)

                # display the detection level history
                plot_detectionLevels(detectionLevels)
                
                # display the thermal images
                if useThermal:
                    flir.captureThermalImage('IMG_0000.pgm')
                    flir.drawPGM((900, 350), flir.previousThermalImageString, screen)
                    flir.drawPGM((900, 500), flir.currentThermalImageString, screen)
                    screen.blit(thermalLabel, (900, 630))

                    if flir.thermalImageAnomalyDetected() and useNova:
                        # send alert using Holgram Nova
                        HologramNova.sendAlert("Thermal anomaly detected!")
                    
                # send bee activity level
                if currentBees > 50 and useNova:
                    HologramNova.sendBeeActivity()
            
                # update the display
                pygame.display.flip()

            # check whether to publish the sample data
            if sampleCount >= samplesPerPublish:
                
                # send data to Hologram Nova
                if useNova:
                    print ("Bee Detection Level: ", beesDetectedCount)
                    with open("/var/www/html/beeDetectionLevel.txt", "w") as text_file:
                        text_file.write(str(beesDetectedCount))
                    with open("/var/www/html/beeDetectionLevel.json", "w") as text_file:
                        text_file.write(json.dumps(message))

                # clear data for next publishing period
                sampleCount = 0
                beesDetectedCount = 0

    #except (IOError):
    #    print("IOError: " + str(IOError))
    #    abort = True
    #    continue
    except (KeyboardInterrupt):
        abort = True

