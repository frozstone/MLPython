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

    exitFlag = False
    spsample = ''
    #parallelize this for loop
    for para in paras:
        if para not in feats:
            print para
            usedSentenceLength = 0
            detailInfo = []

            parsers, ann = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')), path.join(annLongDir, para), path.join(annShortDir, para))

            for mtname, mtdescs in ann._mathEnju.iteritems():
                for mtdesc in mtdescs:
                    taginfos = parsers[mtdesc[0]].tagInfo
                    starttoken = tuple()
                    endtoken = tuple()
                    startfound = False
                    endfound = False
                    for taginfo in taginfos:
                        if mtdesc[1] == taginfo[0]:
                            starttoken = taginfo
                            startfound = True
                        if mtdesc[2] == taginfo[1]:
                            endtoken = taginfo
                            endfound = True
                        if startfound and endfound:
                            break
                    if not(startfound and endfound):
                        print "cannot found proper token"
                    else:
                        sp = ShortestPath(parsers[mtdesc[0]].depTree)
                        sp.TenthFeature()