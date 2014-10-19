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

def GetMathIdx(mathname, sentence, taginfos):
    for i,taginfo in enumerate(taginfos):
        if mathname in sentence[taginfo[0]:taginfo[1]]:
            return i
    return -1

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
    shortestpaths = []

    #parallelize this for loop
    for para in paras:
        if para not in feats:
            usedSentenceLength = 0
            detailInfo = []

            #para = '0905.3705_4.txt'
            print para
            parsers, ann = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')), path.join(annLongDir, para), path.join(annShortDir, para))

            for mtname, mtdescs in ann._mathEnju.iteritems():
                #print mtname, len(mtdescs)
                if len(mtdescs) == 0:
                    continue
                mtidx = GetMathIdx(mtname, parsers[mtdescs[0][0]].sentence, parsers[mtdescs[0][0]].tagInfo)
                for mtdesc in mtdescs:
                    taginfos = parsers[mtdesc[0]].tagInfo
                    starttoken = tuple()
                    startidx = 0
                    endtoken = tuple()
                    endidx = 0
                    startfound = False
                    endfound = False
                    for i,taginfo in enumerate(taginfos):
                        if taginfo[0] <= mtdesc[1] <= taginfo[1]:
                            starttoken = taginfo
                            startidx = i
                            startfound = True
                        if taginfo[0] <= mtdesc[2] <= taginfo[1] or i == len(taginfos) - 1:
                            endtoken = taginfo
                            endidx = i
                            endfound = True
                        if startfound and endfound:
                            break
                    #if not endfound and mtdesc[2] >= taginfos[-1][2]:
                    #    endtoken = taginfos[-1]
                    #    endidx = len(taginfos) - 1
                    #    endfound = True
                    if not(startfound and endfound):
                        print "cannot found proper token", mtname, startidx, endidx, mtdesc
                    else:
                        sp = ShortestPath(parsers[mtdesc[0]].depTree)
                        distance, deppath = sp.TenthFeature(startidx, endidx, mtidx)
                        shortestpaths.append((distance, deppath))
                        #print mtname, startidx, endidx, mtdesc, distance, deppath