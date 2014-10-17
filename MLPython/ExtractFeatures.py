from ParserInfo import ParserInfo
from math import fabs
from Annotation import Annotation
import scipy
import re

class ExtractFeatures():
    """description of class"""
    _sentence = ""
    _tagInfo = [] #[(start, end, id, cat, pos)]
    _np = () #(start, end)
    _math = () #(start, end)
    _depTree = [] #[(relation, first token, second token)]
    _ann = ''
    _charPreCount = 0

    _between_start = 0
    _between_end = 0
    
    _np_wordidx = 0 #starting word
    _np_endidx = 0
    _mt_wordidx = 0 #starting word
    _mt_endidx = 0

    def __init__(self, sentence, tag, np, math, depTree, annotation, preCount=None):
        self._sentence = sentence
        self._tagInfo = tag
        self._np = self.__validNP(np, math)
        self._math = math
        self._depTree = depTree
        if annotation != None:
            self._ann = annotation
        self._charPreCount = preCount

        idx = [self._np[0], self._np[1], self._math[0], self._math[1]]
        idx.sort()
        self._between_start = idx[1]
        self._between_end = idx[2]

    def __validNP(self, np, math):
        mathtoken = self._sentence[math[0]:math[1]]
        nptoken = self._sentence[np[0]:np[1]]
        if nptoken.rstrip().endswith(mathtoken.strip()):
            originalNPEndIdx = [i for i,tag in enumerate(self._tagInfo) if tag[1] == np[1]][0]
            return (np[0], self._tagInfo[originalNPEndIdx - 1][1])
        else:
            return np

    def __mathNPValid(self):
        return not(self._math[0] >= self._np[0] and self._math[1] <= self._math[1])

    def __checkPrepPre(self, mathname, desc_idx):
        i = self._np_wordidx
        for x in range(self._np_wordidx - 1, -1, -1):
            if self._tagInfo[x][4] == 'IN' and self._sentence[self._tagInfo[x][0]:self._tagInfo[x][1]] in self._ann._mathtext[mathname][desc_idx]:
                return False
            elif self._sentence[self._tagInfo[x][0]:self._tagInfo[x][1]] not in self._ann._mathtext[mathname][desc_idx]:
                break
        return True

    def __checkPrepEnd(self, mathname, desc_idx):
        i = self._np_wordidx
        for x in range(self._np_endidx - 1, self._np_wordidx - 1, -1):
            if self._tagInfo[x][4] == 'IN' and self._sentence[self._tagInfo[x][0]:self._tagInfo[x][1]] not in self._ann._mathtext[mathname][desc_idx]:
                return False
        return True

    def isDescription(self, relv):
        lengthPreSpaces = sum([1 for c in self._sentence[:self._np[0]] if c == ' '])
        lengthsEndSpaces = sum([1 for c in self._sentence[:self._np[1]] if c == ' '])
        mathname = re.match(r'MATH_\d*', self._sentence[self._math[0]:self._math[1]])
        descriptionsOfMath = self._ann._math[mathname.group(0)]

        annStartIdx = [tok for tok,idx in self._ann._tokens.items() if idx[0] <= (self._charPreCount + self._np[0] - lengthPreSpaces) < idx[1]][0]
        annEndIdxs = [tok for tok,idx in self._ann._tokens.items() if idx[0] <= (self._charPreCount + self._np[1] - lengthsEndSpaces) <= idx[1]]
        annEndIdx = annEndIdxs[0] if len(annEndIdxs) > 0 else max(self._ann._tokens.keys())
        
        for desc_i in range(len(descriptionsOfMath)):
            desc = descriptionsOfMath[desc_i]
            if (desc[0] == annStartIdx and desc[-1] == annEndIdx) or (relv and desc[0] <= annStartIdx <= desc[-1] and self.__checkPrepPre(mathname.group(0), desc_i)) or (not relv and desc[-1] == annEndIdx and self.__checkPrepEnd(mathname.group(0), desc_i)):
                return True, annStartIdx, annEndIdx
        return False, annStartIdx, annEndIdx

    def FirstFeature(self):
        if self.__mathNPValid():
            return ':' in self._sentence[self._between_start:self._between_end], ',' in self._sentence[self._between_start:self._between_end], '__MATH_' in self._sentence[self._between_start:self._between_end]
        else:
            return False, False, False

    def SecondFeature(self):
        if self.__mathNPValid():
            if self._math[1] < self._np[0]:
                return '(' in self._sentence[self._math[1]:self._np[0]] and ')' in self._sentence[self._np[1]:]
            elif self._np[1] < self._math[0]:
                return '(' in self._sentence[:self._np[0]] and ')' in self._sentence[self._np[1]:self._math[0]]
        return False

    def ThirdFeature(self):
        self._np_wordidx = [i for i,tag in enumerate(self._tagInfo) if tag[0] == self._np[0]][0]
        self._np_endidx = [i for i,tag in enumerate(self._tagInfo) if tag[1] == self._np[1]][0]

        self._mt_wordidx = [i for i,tag in enumerate(self._tagInfo) if tag[0] == self._math[0]][0]
        self._mt_endidx = [i for i,tag in enumerate(self._tagInfo) if tag[1] == self._math[1]][0]

        return (self._mt_wordidx - self._np_endidx - 1) if self._mt_wordidx > self._np_endidx else (self._np_wordidx - self._mt_endidx - 1) 

    def FourthFeature(self):
        return self._math[0] <= self._np[0]

    def FifthFeature(self):
        verbtag = []

        if self._np_wordidx < self._mt_wordidx:
            verbs = [tag for tag in self._tagInfo[self._np_endidx+1:self._mt_wordidx] if tag[3] == 'V']
            verbtag = verbs[0] if len(verbs) > 0 else None
        else:
            verbs = [tag for tag in self._tagInfo[self._mt_endidx+1:self._np_wordidx] if tag[3] == 'V']
            verbtag = verbs[0] if len(verbs) > 0 else None
        return self._sentence[verbtag[0]:verbtag[1]] if verbtag != None else ''

    def SixthFeature(self, amount):
        presurf = []
        prepos = []
        nextsurf = []
        nextpos = []

        i = self._np_wordidx
        if self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_"):
            presurf.append("OTHERMATH")
            prepos.append("OTHERMATH")
        else:
            presurf.append(self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]])
            prepos.append(self._tagInfo[i][4])

        i -= 1
        while i >= 0:
            if i == self._mt_endidx:
                presurf.insert(0, "MATH")
                prepos.insert(0, "MATH")
            elif i != self._mt_endidx and self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_"):
                presurf.insert(0, "OTHERMATH")
                prepos.insert(0, "OTHERMATH")
            else:
                presurf.insert(0, self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]])
                prepos.insert(0, self._tagInfo[i][4])
            
            if len(presurf) == amount:
                break
            i -= 1
        
        j = self._np_endidx
        if self._sentence[self._tagInfo[j][0]:self._tagInfo[j][1]].startswith("__MATH_"):
            nextsurf.append("OTHERMATH")
            nextpos.append("OTHERMATH")
        else:
            nextsurf.append(self._sentence[self._tagInfo[j][0]:self._tagInfo[j][1]])
            nextpos.append(self._tagInfo[j][4])

        j += 1
        while j < len(self._tagInfo):
            if j == self._mt_wordidx:
                nextsurf.append("MATH")
                nextpos.append("MATH")
            elif j != self._mt_wordidx and self._sentence[self._tagInfo[j][0]:self._tagInfo[j][1]].startswith("__MATH_"):
                nextsurf.append("OTHERMATH")
                nextpos.append("OTHERMATH")
            else:
                nextsurf.append(self._sentence[self._tagInfo[j][0]:self._tagInfo[j][1]])
                nextpos.append(self._tagInfo[j][4])

            if len(nextsurf) == amount:
                break
            j += 1

        return presurf, prepos, nextsurf, nextpos

    def SeventhFeature(self, amount):
        presurf = []
        prepos = []
        nextsurf = []
        nextpos = []

        i = self._mt_wordidx - 1

        while i >= 0:
            if self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_"):
                presurf.insert(0, "OTHERMATH")
                prepos.insert(0, "OTHERMATH")
            else:
                presurf.insert(0, self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]])
                prepos.insert(0, self._tagInfo[i][4])
            
            if len(presurf) == amount:
                break
            i -= 1
        
        j = self._mt_endidx + 1

        while j < len(self._tagInfo):
            if self._sentence[self._tagInfo[j][0]:self._tagInfo[j][1]].startswith("__MATH_"):
                nextsurf.append("OTHERMATH")
                nextpos.append("OTHERMATH")
            else:
                nextsurf.append(self._sentence[self._tagInfo[j][0]:self._tagInfo[j][1]])
                nextpos.append(self._tagInfo[j][4])

            if len(nextsurf) == amount:
                break
            j += 1

        return presurf, prepos, nextsurf, nextpos

    def EighthFeature(self, ptn1, ptn2, ptn3, ptn4, ptn5, ptn6):
        temp_sent = self._sentence[:self._np[0]] + "NP" + self._sentence[self._np[1]:]
        temp_sent = temp_sent.replace(self._sentence[self._math[0]:self._math[1]], 'MATH')
        
        ans1 = ptn1.search(temp_sent) != None
        ans2 = ptn2.search(temp_sent) != None
        ans3 = ptn3.search(temp_sent) != None
        ans4 = ptn4.search(temp_sent) != None
        ans5 = ptn5.search(temp_sent) != None
        ans6 = ptn6.search(temp_sent) != None
        ans7 = False

        preIndex = self._mt_wordidx - 1
        beginDetectedIndex = 0
        endDetectedIndex = 0
        
        if preIndex > -1:
            if self._tagInfo[preIndex][3] == "N" and not self._sentence[self._tagInfo[preIndex][0]:self._tagInfo[preIndex][1]].startswith("__MATH_"):
                endDetectedIndex = preIndex

                i = preIndex
                while(i>=0):
                    if (self._tagInfo[i][3] == "N" and not self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_")) or (self._tagInfo[i][3] == "ADJ" and self._tagInfo[i+1][3] == "N" and not self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_")):
                        beginDetectedIndex = i
                    elif self._tagInfo[i][3] == "D":
                        beginDetectedIndex = i
                        break
                    else:
                        break
                    i -= 1
            else:
                searchIndex = preIndex
                while searchIndex >= 0 and (self._sentence[self._tagInfo[searchIndex][0]:self._tagInfo[searchIndex][1]].startswith("__MATH_") or self._sentence[self._tagInfo[searchIndex][0]:self._tagInfo[searchIndex][1]] == "and" or self._sentence[self._tagInfo[searchIndex][0]:self._tagInfo[searchIndex][1]] == "or" or self._sentence[self._tagInfo[searchIndex][0]:self._tagInfo[searchIndex][1]] == ","):
                    searchIndex -= 1

                i = searchIndex
                while i >= 0:
                    if (self._tagInfo[i][3] == "N" and self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_")) or (self._tagInfo[i][3] == "ADJ" and self._tagInfo[i+1][3] == "N" and not self._sentence[self._tagInfo[i][0]:self._tagInfo[i][1]].startswith("__MATH_")):
                        beginDetectedIndex = i
                        if i == searchIndex:
                            endDetectedIndex = i
                    elif self._tagInfo[i][3] == "D":
                        beginDetectedIndex = i
                        break
                    else:
                        break
                    i -= 1
        if beginDetectedIndex == self._np_wordidx and endDetectedIndex == self._np_endidx:
            ans7 = True

        return ans1, ans2, ans3, ans4, ans5, ans6, ans7

    #Feature 9 and Feature 10 need a dependency graph
    def NinthFeature(self):
        NotImplemented

    def PreTenthFeature(self):
        return self._np_wordidx, self._np_endidx, self._mt_wordidx
