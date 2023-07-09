from math import e
from datetime import datetime

class Leaderboard:
    def __init__(self):
        self.players = {}

    def loadData(self, players):
        self.players = players
    
    def dumpData(self):
        return self.players
        
    def addPlayer(self, name):
        if name in self.players:
            return False
        else:
            self.players[name] = {
                "elo": 1500,
                "matches": {}
            }
            return True
    
    def delPlayer(self, name):
        if name not in self.players:
            return False
        else:
            self.players.pop(name)
            return True

    def setElo(self, name, elo):
        try:
            print(f"{self.players[name]['elo']} --> {elo}")
            self.players[name]['elo'] = elo
            return True
        except:
            print("That person doesn't exist")
            return False

    def getPlayers(self):
        string = ""
        for name in self.players.keys():
            string += f"{name} elo: {self.players[name]['elo']:.2f}\n"
        return string
    
    def getLeaderboard(self):
        board = []
        for key in self.players.keys():
            board.append((self.players[key]['elo'], key))
        return sorted(board, reverse=True)
    
    def get2pUpsetMult(self, t1p1Elo, t1p2Elo, t2p1Elo, t2p2Elo, t1Score, t2Score, upsetConstant = 1):
        if t1Score >= t2Score:
            winningElo = (t1p1Elo + t1p2Elo) / 2
            losingElo = (t2p1Elo + t2p2Elo) / 2
        else: 
            winningElo = (t2p1Elo + t2p2Elo) / 2
            losingElo = (t1p1Elo + t1p2Elo) / 2

        return upsetConstant * losingElo / winningElo
    
    def get1pUpsetMult(self, p1Elo, p2Elo, s1, s2, upsetConstant = 1):
        if s1 > s2:
            winningElo = p1Elo
            losingElo = p2Elo
        else:
            winningElo = p2Elo
            losingElo = p1Elo
        
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

    def add2pGame(self, t1p1, t1p2, t2p1, t2p2, t1Score, t2Score, winElo = 100, lossElo = -100):

        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        t1p1Elo = self.players[t1p1]['elo']
        t1p2Elo = self.players[t1p2]['elo']
        t2p1Elo = self.players[t2p1]['elo']
        t2p2Elo = self.players[t2p2]['elo']
        
        upsetMult = self.get2pUpsetMult(t1p1Elo, t1p2Elo, t2p1Elo, t2p2Elo, t1Score, t2Score)
        scoreDeltaMult = self.getScoreDeltaMult(t1Score, t2Score)
        lobbyElo = sum([t1p1Elo, t1p2Elo, t2p1Elo, t2p2Elo]) / 4
        
        if t1Score > t2Score: # t1 beat t2
            t1p1Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p1Elo, True) * scoreDeltaMult
            t1p2Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p2Elo, True) * scoreDeltaMult
            t2p1Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p1Elo, False) * scoreDeltaMult
            t2p2Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p2Elo, False) * scoreDeltaMult
            
        else: # t2 beat t1
            t1p1Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p1Elo, False) * scoreDeltaMult
            t1p2Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, t1p2Elo, False) * scoreDeltaMult
            t2p1Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p1Elo, True) * scoreDeltaMult
            t2p2Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, t2p2Elo, True) * scoreDeltaMult
            

        self.players[t1p1]['elo'] += t1p1Change
        self.players[t1p2]['elo'] += t1p2Change
        self.players[t2p1]['elo'] += t2p1Change
        self.players[t2p2]['elo'] += t2p2Change

        # add match report to profile
        self.players[t1p1]['matches'][timestamp] = {
            'type': 'doubles',
            'teammate': t1p2,
            'opponent1': t2p1,
            'opponent2': t2p2,
            'self_elo_prior': t1p1Elo,
            'self_elo_delta': t1p1Change,
            'self_elo_after': t1p1Elo + t1p1Change,
            'opponent1_elo': t2p1Elo,
            'opponent2_elo': t2p2Elo,
            'teammate_elo': t1p2Elo,
            'win': t1Score > t2Score,
            'self_score': t1Score,
            'opponent_score': t2Score
        }

        self.players[t1p2]['matches'][timestamp] = {
            'type': 'doubles',
            'teammate': t1p1,
            'opponent1': t2p1,
            'opponent2': t2p2,
            'self_elo_prior': t1p2Elo,
            'self_elo_delta': t1p2Change,
            'self_elo_after': t1p2Elo + t1p2Change,
            'opponent1_elo': t2p1Elo,
            'opponent2_elo': t2p2Elo,
            'teammate_elo': t1p1Elo,
            'win': t1Score > t2Score,
            'self_score': t1Score,
            'opponent_score': t2Score
        }

        self.players[t2p1]['matches'][timestamp] = {
            'type': 'doubles',
            'teammate': t2p2,
            'opponent1': t1p1,
            'opponent2': t1p2,
            'self_elo_prior': t2p1Elo,
            'self_elo_delta': t2p1Change,
            'self_elo_after': t2p1Elo + t2p1Change,
            'opponent1_elo': t1p1Elo,
            'opponent2_elo': t1p2Elo,
            'teammate_elo': t2p2Elo,
            'win': t1Score < t2Score,
            'self_score': t2Score,
            'opponent_score': t1Score
        }

        self.players[t2p2]['matches'][timestamp] = {
            'type': 'doubles',
            'teammate': t2p1,
            'opponent1': t1p1,
            'opponent2': t1p2,
            'self_elo_prior': t2p2Elo,
            'self_elo_delta': t2p2Change,
            'self_elo_after': t2p2Elo + t2p2Change,
            'opponent1_elo': t1p1Elo,
            'opponent2_elo': t1p2Elo,
            'teammate_elo': t2p1Elo,
            'win': t1Score < t2Score,
            'self_score': t2Score,
            'opponent_score': t1Score
        }

        telemetry = {}
        telemetry["score"] = [t1Score, t2Score]
        telemetry["avgElo"] = f"{lobbyElo:.2f}"
        telemetry["names"] = [t1p1, t1p2, t2p1, t2p2]
        telemetry["oldElo"] = [f"{t1p1Elo:.2f}", 
                               f"{t1p2Elo:.2f}", 
                               f"{t2p1Elo:.2f}", 
                               f"{t2p2Elo:.2f}"
            ]
        telemetry["newElo"] = [
            f"{self.players[t1p1]['elo']:.2f}", 
            f"{self.players[t1p2]['elo']:.2f}", 
            f"{self.players[t2p1]['elo']:.2f}", 
            f"{self.players[t2p2]['elo']:.2f}"
            ]
        telemetry["eloDelta"] = [
            f"{'+' if t1p1Change > 0 else ''}{t1p1Change:.2f}", 
            f"{'+' if t1p2Change > 0 else ''}{t1p2Change:.2f}", 
            f"{'+' if t2p1Change > 0 else ''}{t2p1Change:.2f}", 
            f"{'+' if t2p2Change > 0 else ''}{t2p2Change:.2f}"
            ]
        telemetry["upsetMult"] = f"{upsetMult:.3f}"
        telemetry["scoreDeltaMult"] = f"{scoreDeltaMult:.3f}"
        return telemetry
    
    def add1pGame(self, p1, p2, s1, s2, winElo = 100, lossElo = -100):
        
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        p1Elo = self.players[p1]['elo']
        p2Elo = self.players[p2]['elo']
        upsetMult = self.get1pUpsetMult(p1Elo, p2Elo, s1, s2)
        scoreDeltaMult = self.getScoreDeltaMult(s1, s2)
        lobbyElo = sum([p1Elo, p2Elo]) / 2

        if s1 > s2: # player 1 beat player 2
            p1Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, p1Elo, True) * scoreDeltaMult
            p2Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, p2Elo, False) * scoreDeltaMult
        else:
            p1Change = lossElo * upsetMult * self.getLobbyEloMult(lobbyElo, p1Elo, False) * scoreDeltaMult
            p2Change = winElo * upsetMult * self.getLobbyEloMult(lobbyElo, p2Elo, True) * scoreDeltaMult

        self.players[p1]['elo'] += p1Change
        self.players[p2]['elo'] += p2Change

        # add match report to profile
        self.players[p1]['matches'][timestamp] = {
            'type': 'singles',
            'opponent': p2,
            'self_elo_prior': p1Elo,
            'self_elo_delta': p1Change, 
            'self_elo_after': p1Elo + p1Change,
            'opponent_elo': p2Elo,
            'win': s1 > s2,
            'self_score': s1,
            'opponent_score': s2
        }

        self.players[p2]['matches'][timestamp] = {
            'type': 'singles',
            'opponent': p1,
            'self_elo_prior': p2Elo,
            'self_elo_delta': p2Change, 
            'self_elo_after': p2Elo + p2Change,
            'opponent_elo': p1Elo,
            'win': s1 < s2,
            'self_score': s2,
            'opponent_score': s1
        }

        telemetry = {}
        telemetry["score"] = [s1, s2]
        telemetry["avgElo"] = f"{lobbyElo:.2f}"
        telemetry["names"] = [p1, p2]
        telemetry["oldElo"] = [f"{p1Elo:.2f}", 
                               f"{p2Elo:.2f}"
            ]
        telemetry["newElo"] = [
            f"{self.players[p1]['elo']:.2f}", 
            f"{self.players[p2]['elo']:.2f}"
            ]
        telemetry["eloDelta"] = [
            f"{'+' if p1Change > 0 else ''}{p1Change:.2f}", 
            f"{'+' if p2Change > 0 else ''}{p2Change:.2f}"
            ]
        telemetry["upsetMult"] = f"{upsetMult:.3f}"
        telemetry["scoreDeltaMult"] = f"{scoreDeltaMult:.3f}"
        return telemetry

    