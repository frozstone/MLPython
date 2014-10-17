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

    paragraphDir = 'D:/test/sentences/math0106119'
    parseDir = 'D:/test/parsetrees/math0106119' #argv[2]
    featureDir = 'D:/test/features/math0106119' #argv[3]
    annLongDir = ''#'D:/ntcir10/bios_long/' #argv[4] #will be null for final run
    annShortDir = ''#'D:/ntcir10/bios_short/' #argv[4] #will be null for final run
    trainFormatFile = 'D:/test/format.arff' #argv[5]

    paras = listdir(paragraphDir)
    feats = []
    if path.exists(featureDir):
        feats = listdir(featureDir)
    else:
        mkdir(featureDir)

    proc = preprocess()
    csv.register_dialect("weka", WekaCSV)

    #parallelize this for loop
    for para in paras:
        if para not in feats:
            print para
            usedSentenceLength = 0
            fFormat = open(trainFormatFile)
            trainFile = fFormat.read()
            fFormat.close()
            detailInfo = []

            #Use in the case of performance measurement (PM)
            parsers, ann = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')), path.join(annLongDir, para), path.join(annShortDir, para))
            #parsers = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')))

            trainLines = cStringIO.StringIO()
            traincsv = csv.writer(trainLines, dialect='weka')

            #PM
            usedSentenceLength = 0

            for sentenceData in parsers:
                #PM
                if len(sentenceData.depTree) == 0:
                    usedSentenceLength += sum(1 for c in sentenceData.sentence if c.strip() != '')
                    continue

                sp = ShortestPath(sentenceData.depTree)
                for mt in sentenceData.maths:
                    #PM
                    if sentenceData.sentence[mt[0]:mt[1]] not in ann._math:
                        continue

                    for np in sentenceData.nps:
                        if (not(mt[0] == np[0] and mt[1] == np[1])) and ((mt[0] < np[0] and mt[1] <= np[0]) or (np[0] < mt[0] and np[1] <= mt[1])):
                            #Extracting features
                            #Put ann instead of None in 'ef' declaration for PM

                            ef = ExtractFeatures(sentenceData.sentence, sentenceData.tagInfo, np, mt, sentenceData.depTree, ann)
                            mtInNP = not (np[0] == ef._np[0] and np[1] == ef._np[1])
                            colon, comma, othermath = ef.FirstFeature()
                            insidebracket = ef.SecondFeature()
                            distance = ef.ThirdFeature()
                            mathbefore = ef.FourthFeature()
                            verb = ef.FifthFeature()
                            nppresurf, npprepos, npnextsurf, npnextpos = ef.SixthFeature(3)
                            mathpresurf, mathprepos, mathnextsurf, mathnextpos = ef.SeventhFeature(3)
                            pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7 = ef.EighthFeature(ptn1, ptn2, ptn3, ptn4, ptn5, ptn6)
                            npstart, npend, mathstart = ef.PreTenthFeature()
                            depdistance, rel_math, rel_np, math_out, np_out = sp.TenthFeature(npstart, npend, mathstart)

                            #PM
                            isDesc, annStartIdx, annEndIdx = ef.isDescription(mathbefore)

                            #PM
                            detailInfo.append(sentenceData.sentence[mt[0]:mt[1]] + '\t' + str(annStartIdx) + '\t' + str(annEndIdx) + '\n')
                            #detailInfo.append(sentenceData.sentence[mt[0]:mt[1]] + '\t' + sentenceData.sentence[ef._np[0]:ef._np[1]] + '\n')

                            featureVector = []

                            #Writing pattern features
                            featureVector.extend([str(mtInNP), str(pattern1), str(pattern2), str(pattern3), str(pattern4), str(pattern5), str(pattern6), str(pattern7)])

                            #Writing feature 1 - 4
                            featureVector.extend([str(colon), str(comma), str(othermath), str(insidebracket), str(distance), str(mathbefore)])
                            
                            #Writing feature 5
                            featureVector.append(verb if verb.strip() != '' else 'None')

                            #Writing feature 6 and 7
                            featureVector.extend(NGramTrainingLine(mathpresurf, mathprepos, "Math", "Before"))
                            featureVector.extend(NGramTrainingLine(mathnextsurf, mathnextpos, "Math", "After"))
                            featureVector.extend(NGramTrainingLine(nppresurf, npprepos, "NP", "Before"))
                            featureVector.extend(NGramTrainingLine(npnextsurf, npnextpos, "NP", "After"))

                            #Writing feature 10
                            if math_out != None:
                                featureVector.extend([str(100000 if depdistance == Inf else int(depdistance)), str(math_out), str(np_out)])
                                featureVector.extend(NGramDepRel(rel_math, "Math"))
                                featureVector.extend(NGramDepRel(rel_np, "NP"))
                            else:
                                featureVector.extend([100000, False, False])
                                featureVector.extend(['','','','','','','','','','','',''])
                            #PM
                            featureVector.append(isDesc)
                            #featureVector.append(str(True))

                            traincsv.writerow(featureVector)

                #PM
                usedSentenceLength += sum(1 for c in sentenceData.sentence if c.strip() != '')
            
            #Dump the detailFile and trainFile in a file
            f1 = open(path.join(featureDir, para), 'w')
            f1.writelines(detailInfo)
            f1.close()
            f2 = open(path.join(featureDir, para).replace('.txt', '.arff'), 'w')
            f2.write(trainFile + trainLines.getvalue())
            f2.close()
