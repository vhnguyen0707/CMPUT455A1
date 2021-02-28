class TranspositionTable(object):
    
    def __init__(self):
        self.table = {}
        
    def store(self, code, score):
        self.table[code] = score

    def lookup(self, code):
        return self.table.get(code)
