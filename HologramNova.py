#   H O L O G R A M   N O V A   R O U T I N E S
#   Designed by David Guidos, Dec 2017

class HologramNova:

    def sendAlert(message):
        if useNova:
            alertCommand = 'sudo hologram send "' + message + '"'
            os.system(alertCommand)
        
    def sendBeeActivity():
        if useNova:
            alertCommand = 'sudo hologram send "Bee Activity Level:' + str(currentBees) + '"'
            os.system(alertCommand)
    
    
