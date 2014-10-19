from ParserInfo import ParserInfo

class Annotation:
    _math = {} #{mathname: [[], []]} --> block number
    _mathEnju = {} #{mathname: [(sentence number, startidx, enidx), ()}
    _mathtext = {} #{mathname: [[], []]} --> text
    _tokens = {} #{wordidx: (wordstartidx, wordstart+len, text)}
    _maxtoken = 0
    __parserinfos = []
    __allTokens = {}
    _alltokens = {}

    def __alignCharIndexes(self):
        #get sentence number
        start = 0
        end_temp = 0
        start_notspace = 0
        end_temp_notspace = 0
        newtoken = True
        idx = 0
        idx_notspace = 0
        for info in self.__parserinfos:
            tokens = []
            for c in info.sentence:
                if not c.isspace() and newtoken:
                    start = idx
                    end_temp = idx
                    start_notspace = idx_notspace
                    end_temp_notspace = idx_notspace
                    idx_notspace += 1
                    newtoken = False
                elif not c.isspace() and not newtoken:
                    end_temp = idx
                    end_temp_notspace = idx_notspace
                    idx_notspace += 1
                elif c.isspace() and not newtoken:
                    end_temp = idx
                    tokens.append((start_notspace, end_temp_notspace + 1, start, end_temp))
                    #tokens[(start_notspace, end_temp_notspace + 1)] = (start, end_temp)
                    newtoken = True
                else:
                    newtoken = True
                idx += 1
            self.__allTokens[info.lineNumber] = tokens

    def __annToEnju(self, annToken):
        '''
            annToken is a tuple = (wordstartidx, wordstart+len, text) => non space
        '''
        starttoken = tuple()
        endtoken = tuple()
        sentenceoffset = 0
        sentencenumber = 0
        for k,v in self.__allTokens.iteritems():
            if v[-1][1] > annToken[1]:
                #search the tuple that corresponds to the annToken
                foundStartToken = False
                for t in v:
                    if t[0] == annToken[0]:
                        starttoken = (t[2] - sentenceoffset, t[3] - sentenceoffset)
                        foundStartToken = True
                        sentencenumber = k
                    if t[1] == annToken[1]:
                        endtoken = (t[2] - sentenceoffset, t[3] - sentenceoffset)
                        if foundStartToken:
                            break
            sentence = self.__parserinfos[k].sentence
            sentenceoffset += len(sentence) #if 'MATH_' in sentence else 0
        return sentencenumber, list(set([starttoken, endtoken]))

    def __init__(self, address_annLong, address_annShort, parserInfos, longOrShort):
        '''
            longOrShort -> 1 for short ; 2 for long ; 3 for long and short
        '''
        self._math = {}
        self._mathtext = {}
        self._tokens = {}
        self.__parserinfos = parserInfos

        self.__alignCharIndexes()
        self._alltokens = self.__allTokens
        lnsLong = open(address_annLong).readlines()
        lnsShort = open(address_annShort).readlines()
        
        charidx = 0
        #record the tokens
        for ln in lnsLong:
           if '\t' not in ln:
               continue
           cells = ln.strip().split('\t')
           token = cells[1]
           self._tokens[int(cells[0])] = (charidx, charidx + len([c for c in token if not c.isspace()]), token)
           self._maxtoken = int(cells[0])
           charidx += len(token)

        #Record Long Desc
        mathname = ''
        for ln in lnsLong:
            if ln.startswith('MATH_'):
                mathname = ln.strip()
                self._math[mathname] = []
                self._mathEnju[mathname] = []
                self._mathtext[mathname] = []
            elif ln.startswith('[') and (longOrShort == 2 or longOrShort == 3):
                self._math[mathname].append([])
                self._mathtext[mathname].append([])
                regions = ln.strip()[1:-1].split(',')
                for region in regions:
                    if '-' in region:
                        blocks = region.split('-')
                        self._math[mathname][-1].extend(range(int(blocks[0]), int(blocks[1]) + 1))
                        
                        x,y = self.__annToEnju(self._tokens[int(blocks[0])])
                        w,z = self.__annToEnju(self._tokens[int(blocks[1])])
                        self._mathEnju[mathname].append((x, y[0][0], z[-1][1]))
                        
                        self._mathtext[mathname][-1].extend([self._tokens[i][2] for i in range(int(blocks[0]), int(blocks[1]) + 1)])
                    else:
                        self._math[mathname][-1].append(int(region))
                        x,y = self.__annToEnju(self._tokens[int(region)])
                        w,z = self.__annToEnju(self._tokens[int(region)])
                        self._mathEnju[mathname].append((x, y[0][0], z[-1][1]))

                        self._mathtext[mathname][-1].append(self._tokens[int(region)][2])
                    break

        #Record Short Desc
        mathname = ''
        for ln in lnsShort:
            if ln.startswith('MATH_'):
                mathname = ln.strip()
            elif ln.startswith('[') and (longOrShort == 1 or longOrShort == 3):
                regions = ln.strip()[1:-1].split(',')
                for region in regions:
                    if '-' in region:
                        blocks = region.split('-')
                        self._math[mathname].append(range(int(blocks[0]), int(blocks[1]) + 1))
                        x,y = self.__annToEnju(self._tokens[int(blocks[0])])
                        w,z = self.__annToEnju(self._tokens[int(blocks[1])])
                        self._mathEnju[mathname].append((x, y[0][0], z[-1][1]))

                        self._mathtext[mathname].append([self._tokens[i][2] for i in range(int(blocks[0]), int(blocks[1]) + 1)])
                    else:
                        self._math[mathname].append([int(region)])
                        x,y = self.__annToEnju(self._tokens[int(region)])
                        w,z = self.__annToEnju(self._tokens[int(region)])
                        self._mathEnju[mathname].append((x, y[0][0], z[-1][1]))
                        self._mathtext[mathname].append(self._tokens[int(region)][2])
