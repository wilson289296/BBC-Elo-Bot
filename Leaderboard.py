from math import e
import random

class Leaderboard:
    def __init__(self):
        self.players = {}
        
    def addPlayer(self, name):
        self.players[name] = 1500

    def setElo(self, name, elo):
        try:
            print(f"{self.players[name]} --> {elo}")
            self.players[name] = elo
            return True
        except:
            print("That person doesn't exist")
            return False

    def getPlayers(self):
        string = ""
        for name in self.players.keys():
            string += f"{name} elo: {self.players[name]:.2f}\n"
        return string
    
    def getUpsetMult(self, t1p1Elo, t1p2Elo, t2p1Elo, t2p2Elo, t1Score, t2Score, upsetConstant = 1):
        if t1Score >= t2Score:
            winningElo = (t1p1Elo + t1p2Elo) / 2
            losingElo = (t2p1Elo + t2p2Elo) / 2
        else: 
            winningElo = (t2p1Elo + t2p2Elo) / 2
            losingElo = (t1p1Elo + t1p2Elo) / 2

        return upsetConstant * losingElo / winningElo

    def legacy_LobbyEloMult(self, lobbyElo, playerElo, upset, constant = 0.00005): # legacy version using normal distribution
        # e^-constant(delta^2)
        delta = abs(lobbyElo - playerElo)
        exponent = constant * (delta ** 2)
        if upset:
            return 1- (0.9 * e ** -exponent)
        else:
            return 0.9 * e ** -exponent
    
    def getLobbyEloMult(self, lobbyElo, playerElo, win, constant = 0.002): # new version using sigmoid function
        # 1 / (1 - e^-x)
        if win:
            return 2 / (1 + e ** (constant * (playerElo - lobbyElo)))
        else:
            return 2 / (1 + e ** (-constant * (playerElo - lobbyElo)))
            
    def getScoreDeltaMult(self, t1Score, t2Score, scoreDeltaConstant = 1):
        delta = abs(t1Score - t2Score)
        return scoreDeltaConstant * delta / 21

    def add2pGame(self, t1p1, t1p2, t2p1, t2p2, t1Score, t2Score, winElo = 100, lossElo = -100, report = False):
        t1p1Elo = self.players[t1p1]
        t1p2Elo = self.players[t1p2]
        t2p1Elo = self.players[t2p1]
        t2p2Elo = self.players[t2p2]
        
        upsetMult = self.getUpsetMult(t1p1Elo, t1p2Elo, t2p1Elo, t2p2Elo, t1Score, t2Score)
        scoreDeltaMult = self.getScoreDeltaMult(t1Score, t2Score)
        # print(f"upsetMult = {upsetMult} \nscoreDeltaMult={scoreDeltaMult}")
        lobbyElo = sum([t1p1Elo, t1p2Elo, t2p1Elo, t2p2Elo]) / 4
        
        if t1Score > t2Score: # t1 beat t2
            t1p1Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p1Elo, True) * scoreDeltaMult
            self.players[t1p1] += t1p1Change

            t1p2Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p2Elo, True) * scoreDeltaMult
            self.players[t1p2] += t1p2Change

            t2p1Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p1Elo, False) * scoreDeltaMult
            self.players[t2p1] += t2p1Change

            t2p2Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p2Elo, False) * scoreDeltaMult
            self.players[t2p2] += t2p2Change
            
        else: # t2 beat t1
            t1p1Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p1Elo, False) * scoreDeltaMult
            self.players[t1p1] += t1p1Change

            t1p2Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p2Elo, False) * scoreDeltaMult
            self.players[t1p2] += t1p2Change

            t2p1Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p1Elo, True) * scoreDeltaMult
            self.players[t2p1] += t2p1Change

            t2p2Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p2Elo, True) * scoreDeltaMult
            self.players[t2p2] += t2p2Change

        if report:
            string = ""
            string += "\n"
            string += f"{t1p1} and {t1p2}  vs. {t2p1} and {t2p2}\n"
            string += f"{((t1p1Elo + t1p2Elo) / 2):.2f} vs. {((t2p1Elo + t2p2Elo) / 2):.2f}\n"
            string += f"Average lobby Elo: {lobbyElo:.2f}\n"
            string += f"Score: {t1Score} - {t2Score}\n"
            string += f"{t1p1}: \n{t1p1Elo:.2f} --> {self.players[t1p1]:.2f} ({'+' if t1p1Change > 0 else ''}{t1p1Change:.2f}) (LobbyEloMult = {self.getLobbyEloMult(lobbyElo, t1p1Elo, t1Score > t2Score):.2f})\n"
            string += f"{t1p2}: \n{t1p2Elo:.2f} --> {self.players[t1p2]:.2f} ({'+' if t1p2Change > 0 else ''}{t1p2Change:.2f}) (LobbyEloMult = {self.getLobbyEloMult(lobbyElo, t1p2Elo, t1Score > t2Score):.2f})\n"
            string += f"{t2p1}: \n{t2p1Elo:.2f} --> {self.players[t2p1]:.2f} ({'+' if t2p1Change > 0 else ''}{t2p1Change:.2f}) (LobbyEloMult = {self.getLobbyEloMult(lobbyElo, t2p1Elo, t1Score < t2Score):.2f})\n"
            string += f"{t2p2}: \n{t2p2Elo:.2f} --> {self.players[t2p2]:.2f} ({'+' if t2p2Change > 0 else ''}{t2p2Change:.2f}) (LobbyEloMult = {self.getLobbyEloMult(lobbyElo, t2p2Elo, t1Score < t2Score):.2f})\n"
            string += f"Upset Multiplier: {upsetMult:.2f}\n"
            string += f"Score delta multiplier: {scoreDeltaMult:.2f}\n"
            return string