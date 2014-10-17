from Preprocess import *
from ExtractFeatures import *
from ShortestPath import ShortestPath
from WekaCSV import WekaCSV
import time
import cStringIO
import csv
from numpy import Inf
from os import listdir, mkdir, path
from sys import argv
import re

def DictionaryToWekaFormat(ngrams, position, type='token'):
    if position == 'Before':
        retVector = []
        for idx in [-3,-2,-1,(-3,-2), (-2,-1), (-3,-2,-1)]:
            if idx in ngrams:
                retVector.extend([ngrams[idx][0], ngrams[idx][1]])
            else:
                retVector.extend(['',''])
        return retVector
    elif position == "After":
        retVector = []
        for idx in [1,2,3,(1,2), (2,3), (1,2,3)]:
            if idx in ngrams:
                if type == 'token':
                    retVector.extend([ngrams[idx][0], ngrams[idx][1]])
                elif type == 'dep':
                    retVector.append(ngrams[idx])
            else:
                if type == 'token':
                    retVector.extend(['',''])
                elif type == 'dep':
                    retVector.append('')
        return retVector

def NGramTrainingLine(surface, pos, type, position):
    surfacename = ''
    posname = ''

    if type == 'NP':
        surfacename = 'surnp'
        posname = 'posnp'
    elif type == 'Math':
        surfacename = 'surmath'
        posname = 'posmath'

    ngram = {}

    if position == 'Before':
        for i in range(len(surface)):
            ngram[(-(len(surface) - 1))] = [surface[i].strip(), pos[i].strip()]

            if i < len(surface) - 1:
                ngram[(-(len(surface)-i), -(len(surface)-i-1))] = [surface[i].strip() + '|' + surface[i+1].strip(), pos[i].strip() + '|' + pos[i+1].strip()]

            if len(surface) == 3 and i == 0:
                ngram[(-(len(surface)-i), -(len(surface)-i-1), -(len(surface)-i-2))] = [surface[i].strip() +  '|' + surface[i+1].strip() + '|' + surface[i+2].strip(), pos[i].strip() + '|' + pos[i+1].strip() + '|' + pos[i+2].strip()]
    elif position == 'After':
        for i in range(len(surface)):
            ngram[(i+1)] = [surface[i].strip(), pos[i].strip()]

            if len(surface) > 1 and len(surface) - i > 1:
                ngram[(i+1, i+2)] = [surface[i].strip() + '|' + surface[i+1].strip(), pos[i].strip() + '|' + pos[i+1].strip()]

            if len(surface) == 3 and i == 0:
                ngram[(i+1, i+2, i+3)] = [surface[i].strip() +  '|' + surface[i+1].strip() + '|' + surface[i+2].strip(), pos[i].strip() + '|' + pos[i+1].strip() + '|' + pos[i+2].strip()]

    return DictionaryToWekaFormat(ngram, position)

def NGramDepRel(relations, type):
    relname = ''
    if type == 'NP':
        relname = 'relnp'
    elif type == 'Math':
        relname = 'relmath'
    
    ngram = {}

    for i in range(len(relations)):
        ngram[(i+1)] = relations[i].strip()

        if len(relations) > 1 and len(relations) - i > 1:
            ngram[(i+1,i+2)] = relations[i].strip() + '|' + relations[i+1].strip()

        if len(relations) == 3 and i == 0:
            ngram[(i+1,i+2,i+3)] = relations[i].strip() + '|' + relations[i+1].strip() + '|' + relations[i+2].strip()
    
    return DictionaryToWekaFormat(ngram, 'After', 'dep')

if __name__ == "__main__":
    ptn1 = re.compile(r"(D|d)enote(d)? (as|by)\sMATH\sNP\.?")
    ptn2 = re.compile(r"((L|l)et|(S|s)et) MATH (denote|denotes|be) NP\.?")
    ptn3 = re.compile(r"NP (is|are)? (denoted|defined|given) (as|by) MATH\.?")
    ptn4 = re.compile(r"MATH (denotes|denote|(stand|stands)\sfor|mean|means) NP\.?")
    ptn5 = re.compile(r"MATH (is|are) NP\.?")
    ptn6 = re.compile(r"NP (is|are) MATH\.?")

    paragraphDir = 'D:/ntcir10/sentences/'
    parseDir = 'D:/ntcir10/parsetrees/' #argv[2]
    featureDir = 'D:/ntcir10/features/' #argv[3]
    annLongDir = 'D:/ntcir10/bios_long/' #argv[4] #will be null for final run
    annShortDir = 'D:/ntcir10/bios_short/' #argv[4] #will be null for final run
    trainFormatFile = 'D:/test/format.arff' #argv[5]

    paras = listdir(paragraphDir)
    feats = []
    if path.exists(featureDir):
        feats = listdir(featureDir)
    else:
        mkdir(featureDir)

    proc = preprocess()
    csv.register_dialect("weka", WekaCSV)

    exitFlag = False
    spsample = ''
    #parallelize this for loop
    for para in paras:
        if para not in feats:
            print para
            usedSentenceLength = 0
            detailInfo = []

            #Use in the case of performance measurement (PM)
            parsers, ann = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')), path.join(annLongDir, para), path.join(annShortDir, para))
            #parsers = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')))

            #PM
            usedSentenceLength = 0

            for sentenceData in parsers:
                #PM
                if len(sentenceData.depTree) == 0:
                    usedSentenceLength += sum(1 for c in sentenceData.sentence if c.strip() != '')
                    continue

                sp = ShortestPath(sentenceData.depTree)
                spsample = sp
                for mt in sentenceData.maths:

                    #PM
                    if sentenceData.sentence[mt[0]:mt[1]] not in ann._math:
                        continue

                    for np in sentenceData.nps:
                        if (not(mt[0] == np[0] and mt[1] == np[1])) and ((mt[0] < np[0] and mt[1] <= np[0]) or (np[0] < mt[0] and np[1] <= mt[1])):
                            #Extracting features
                            print np
                            print sentenceData.sentence[np[0]:np[1]]

                            #Put ann instead of None in 'ef' declaration for PM

                            ef = ExtractFeatures(sentenceData.sentence, sentenceData.tagInfo, np, mt, sentenceData.depTree, ann)
                            
                            mathbefore = ef.FourthFeature()
                            #PM
                            isDesc, annStartIdx, annEndIdx = ef.isDescription(mathbefore)

                            if isDesc:
                                mtInNP = not (np[0] == ef._np[0] and np[1] == ef._np[1])
                                verb = ef.FifthFeature()
                                npstart, npend, mathstart = ef.PreTenthFeature()
                                depdistance, deppath = sp.TenthFeature(npstart, npend, mathstart)
                                print(sentenceData.sentence[mt[0]:mt[1]] + ' ' + sentenceData.sentence[np[0]:np[1]] + str(deppath))

                #PM
                usedSentenceLength += sum(1 for c in sentenceData.sentence if c.strip() != '')
                if para == '0801.0652_2.txt' and 'MATH_5' in sentenceData.sentence:
                    break
        if para == '0801.0652_2.txt' and 'MATH_5' in sentenceData.sentence:
                    break
