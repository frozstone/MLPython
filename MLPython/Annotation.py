class Annotation:
    _math = {} #{mathname: [[], []]} --> block number
    _mathtext = {} #{mathname: [[], []]} --> text
    _tokens = {} #{wordidx: (wordstartidx, wordstart+len, text)}
    _maxtoken = 0

    def __init__(self, address_annLong, address_annShort):
        self._math = {}
        self._mathtext = {}
        self._tokens = {}
        lnsLong = open(address_annLong).readlines()
        lnsShort = open(address_annShort).readlines()
        
        charidx = 0
        #record the tokens
        for ln in lnsLong:
           if '\t' not in ln:
               continue
           cells = ln.strip().split('\t')
           token = cells[1]
           self._tokens[int(cells[0])] = (charidx, charidx + len(token), token)
           self._maxtoken = int(cells[0])
           charidx += len(token)

        #Record Long Desc
        mathname = ''
        for ln in lnsLong:
            if ln.startswith('MATH_'):
                mathname = ln.strip()
                self._math[mathname] = []
                self._mathtext[mathname] = []
            elif ln.startswith('['):
                self._math[mathname].append([])
                self._mathtext[mathname].append([])
                regions = ln.strip()[1:-1].split(',')
                for region in regions:
                    if '-' in region:
                        blocks = region.split('-')
                        self._math[mathname][-1].extend(range(int(blocks[0]), int(blocks[1]) + 1))
                        self._mathtext[mathname][-1].extend([self._tokens[i][2] for i in range(int(blocks[0]), int(blocks[1]) + 1)])
                    else:
                        self._math[mathname][-1].append(int(region))
                        self._mathtext[mathname][-1].append(self._tokens[int(region)][2])

        #Record Short Desc
        mathname = ''
        for ln in lnsShort:
            if ln.startswith('MATH_'):
                mathname = ln.strip()
            elif ln.startswith('['):
                regions = ln.strip()[1:-1].split(',')
                for region in regions:
                    if '-' in region:
                        blocks = region.split('-')
                        self._math[mathname].append(range(int(blocks[0]), int(blocks[1]) + 1))
                        self._mathtext[mathname].append([self._tokens[i][2] for i in range(int(blocks[0]), int(blocks[1]) + 1)])
                    else:
                        self._math[mathname].append([int(region)])
                        self._mathtext[mathname].append(self._tokens[int(region)][2])
