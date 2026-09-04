class RiskScorer:
    ORDER={"GREEN":0,"YELLOW":1,"RED":2}
    def score(self,level):return self.ORDER[level]
