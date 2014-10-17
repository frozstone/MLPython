class ParserInfo(object):
    """description of class"""
    lineNumber = 0
    sentence = ""
    tagInfo = [] #[(start, end, id, cat, pos)]
    nps = [] #[(start, end)]
    maths = [] #[(start, end)]
    depTree = [] #[(relation, first token, second token)]

    def __init__(self, number, sentence, block_def, block_so):
        self.lineNumber = number
        self.sentence = sentence

        if block_def != None:
            self.AddPOSTag(block_so)
            self.AddNPs(block_so)
            self.AddDepTree(block_def)
            self.AddMaths()
            #print self.tagInfo

    def AddMaths(self):
        self.maths = []
        for token in self.tagInfo:
            word = self.sentence[token[0]:token[1]]
            if word.startswith('MATH_'):# and word.endswith('__'): #uncomment the 'and' part for PM
                self.maths.append((token[0], token[1]))

    def AddPOSTag(self, block_so):
        self.tagInfo = []
        lines = block_so.split('\n')
        startindex = int(lines[0].split('\t')[0])
        for line in lines:
            if line.strip() != '':
                cells = line.split('\t')
                if cells[2].startswith('tok'):
                    inner_cells = cells[2].split(' ')
                    self.tagInfo.append((int(cells[0]) - startindex, int(cells[1]) - startindex, int(inner_cells[1][5:-1]), inner_cells[2][5:-1], inner_cells[3][5:-1]))

    def AddNPs(self, block_so):
        self.nps = []
        lines = block_so.split('\n')
        startindex = int(lines[0].split('\t')[0])
        colls = set()
        for line in lines:
            if line.strip() != '':
                cells = line.split('\t')
                inner_cells = cells[2].split(' ')
                if inner_cells[2] in ['cat="NP"', 'cat="NX"']: #noun phrases = NX, NP, N
                    if (int(cells[0]) - startindex, int(cells[1]) - startindex) not in colls:
                        self.nps.append((int(cells[0]) - startindex, int(cells[1]) - startindex)) 
                    colls.add((int(cells[0]) - startindex, int(cells[1]) - startindex))

    def AddDepTree(self, block_def):
        self.depTree = []
        for line in block_def.split('\n'):
            if line.strip() != '':# and not line.startswith('ROOT\t'):
                cells = line.split('\t')
                self.depTree.append((cells[5] , int(cells[4]), int(cells[11])))
                