import os

class Similarity:
    same = 0
    containing = 1
    leftpad = 2
    rightpad = 3
    contained = 4
    leftshift = 5
    rightshift= 6
    softok = 7
    different = 8

class Match:
    strict = 0
    soft = 1

class Description:
    full = 0
    short = 1

def RepresentInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def parse_args():
    from optparse import OptionParser, OptionValueError
    p = OptionParser()
    p.add_option('-t', '--test', action='store',
                 dest='test', type='string')
    p.add_option('-f', '--full', action='store',
                 dest='full', type='string')
    p.add_option('-s', '--short', action='store',
                 dest='short', type='string')
    return p.parse_args()

def RegionToList(region):
    region = region.replace('[', '')
    region = region.replace(']', '')
    parts = region.split(',')
    retval = []
    for part in parts:
        if '-' in part:
##            #Fill the region
##            firstIndex = part.split('-')[0]
##            endIndex = part.split('-')[1]
##            retval.append(range((int)firstIndex, ((int)endIndex) + 1))
            retval.append(part)
        else:
            retval.append(part)
    return retval

def ExpandRegion(region):
    region = region.replace('[', '')
    region = region.replace(']', '')
    parts = region.split(',')
    retval = []
    for part in parts:
        if '-' in part:
            #Fill the region
            firstIndex = part.split('-')[0]
            endIndex = part.split('-')[1]
            retval.extend(range((int)(firstIndex), ((int)(endIndex)) + 1))
        else:
            retval.append(int(part))
    return retval

def PositionChecker(spanref, spantest):
    test = ExpandRegion(spantest)
    ref = ExpandRegion(spanref)
    
    if len(ref) == 0 or len(test) == 0:
        return Similarity.different
    
    if (test[0] == ref[0]) and (test[-1] == ref[-1]):
        return Similarity.same
    elif (test[0] < ref[0]) and (test[-1] > ref[-1]):
        return Similarity.containing
    elif test[-1] == ref[-1]:
        return Similarity.leftpad
    elif test[0] == ref[0]:
        return Similarity.rightpad
    elif (test[0] < ref[0]) and (test[-1] < ref[-1]) and (test[-1] > ref[0]):
        return Similarity.leftshift
    elif (test[0] > ref[0]) and (test[-1] > ref[-1]) and (test[0] < ref[-1]):
        return Similarity.rightshift
    elif (test[0] > ref[0]) and (test[-1] < ref[-1]):
        return Similarity.contained
    else:
        return Similarity.different
        
def TextChecker(ref, test):
    if ref == test:
        return Similarity.same
    elif ref.startswith(test):
        return Similarity.rightpad
    elif ref.endswtih(test):
        return Similarity.leftpad
    elif test in ref:
        return Similarity.containing
    elif ref in test:
        return Similarity.contained
    else:
        return Similarity.different

def IndexShortCompare(descRef, descTest):
    retValue = Similarity.different

    for x in descRef:
        for y in descTest:
            res = PositionChecker(x, y)            
            if res < retValue:
                retValue = res
    return retValue

def IndexFullCompare(descRef, descTest):
    diffIndex = 0
    retValue = Similarity.different

    if (len(descRef) > 1) ^ (len(descTest) > 1):
        if len(descRef) > 1:
            res = PositionChecker(descRef[0], descTest[0])
            if res == Similarity.same:
                retValue = Similarity.contained
            elif res == Similarity.leftshift:
                retValue = Similarity.leftshift
            elif res == Similarity.different:
                retValue = Similarity.different
            else:
                retValue = Similarity.contained
        else:
            res = PositionChecker(descRef[0], descTest[0])
            if res == Similarity.same:
                retValue = Similarity.containing
            elif res == Similarity.rightshift:
                retValue = Similarity.rightshift
            elif res == Similarity.different:
                retValue = Similarity.different
            else:
                retValue = Similarity.containing
    else:
        if len(descRef) > 1:
            did = PositionChecker(descRef[0], descTest[0])
            cid = Similarity.different

            if len(descRef) != len(descTest):
                cid = TextChecker(descRef[1:], descTest[1:])
            else:
                res = Similarity.same
                for x in range(1, len(descRef)):
                    temp = PositionChecker(descRef[x], descTest[x])
                    if temp > res:
                        res = temp
                cid = res

            if (did == Similarity.same) and (cid == Similarity.same):
                retValue = Similarity.same
            elif did == Similarity.same:
                retValue = Similarity.leftpad
            elif did != Similarity.different:
                retValue = Similarity.softok
            else:
                retValue = Similarity.different
        else:
            retValue = PositionChecker(descRef[0], descTest[0])
    return retValue    

def SoftMatching(position):
    if position != Similarity.different:
        return True
    else:
        return False

def StrictMatching(position):
    if position <= Similarity.same:
        return True
    else:
        return False

#precision with data = test ; recall with data = ref
def Calculate(data):
    allData = 0
    trueData = 0
    falseData = 0
    for k, v in data.iteritems():
        for desc in v:
            allData = allData + 1
            if True in desc:
                trueData = trueData + 1
            else:
                falseData = falseData + 1
    return allData, trueData, falseData

def DoMatching(dicRef, dicTest, matchType, descriptionType):
    allPre = 0
    truePre = 0
    allRec = 0
    trueRec = 0

    matched_id = []

    #Search for the precision (place the "True" or "False" in the last position of test)
    for k, v in dicTest.iteritems():
        refVal = dicRef[k]
        for desctest in v:
            comparisonresult = Similarity.different
            
            for descref in refVal:
                compres = Similarity.different

                if descriptionType == Description.full:
                    compres = IndexFullCompare(descref, desctest)
                elif descriptionType == Description.short:
                    compres = IndexShortCompare(descref, desctest)

                if comparisonresult > compres:
                    comparisonresult = compres
            
            condition = False

            if matchType == Match.strict:
                condition = StrictMatching(comparisonresult)
            else:
                condition = SoftMatching(comparisonresult)           

            if condition is True:
                matched_id.append(k)
                #print k
                
                    
            allPre = allPre + 1
            if condition is True:
                truePre = truePre + 1
                #if matchType == Match.soft:
                #    print str(k) + ' ' + str(comparisonresult) + ' ' + str(desctest) + ' ' + str(refVal)

            comparisonresult = Similarity.different

    #Search for the recall (place the "True" or "False" in the last position of ref)
    for k, v in dicRef.iteritems():
        testval = dicTest[k]
        for descref in v:
            comparisonresult = Similarity.different
            
            for desctest in testval:
                compres = Similarity.different

                if descriptionType == Description.full:
                    compres = IndexFullCompare(desctest, descref)
                elif descriptionType == Description.short:
                    compres = IndexShortCompare(desctest, descref)
                    
                if comparisonresult > compres:
                    comparisonresult = compres

            condition = False

            if matchType == Match.strict:
                condition = StrictMatching(comparisonresult)
            else:
                condition = SoftMatching(comparisonresult)
                
            #descref.append(condition)
            allRec = allRec + 1
            if condition is True:
                trueRec = trueRec + 1

            comparisonresult = Similarity.different

    #Uncomment to show performance per file
    #try:
    #    print "Precision: " + str(truePre)+ '/' + str(allPre)+ ' = ' + str((float)(truePre)/(float)(allPre))
    #    print "Recall: " + str(trueRec) + '/' + str(allRec) + ' = ' + str((float)(trueRec)/(float)(allRec))
    #except ZeroDivisionError:
    #    print "Pembagian dengan 0"
        
    return truePre, allPre, trueRec, allRec, matched_id

def SingleFileComparison(ffile, sfile, mfile):
    ftLine = 0
    ffLine = 0
    fsLine = 0
    
    dicTest = {}
    dicFull = {}
    dicShort = {}

    #Building the dictionary from the test    
    if mfile is not None:
        ftest = open(mfile, 'r')
        ftestLines = ftest.readlines()
        for line in ftestLines:
            if line.startswith("MATH") or not RepresentInt(line[0]):
                #stop since it means the end of content section
                break
            else:
                ftLine = ftLine + 1
        mathtestTemp = ""
        for line in ftestLines[ftLine:]:
            if line.startswith("MATH"):
                dicTest[line.split('\t')[0].strip()] = []
                mathtestTemp = line.split('\t')[0].strip()
            elif line.startswith("[") and mathtestTemp !=  "":
                dicTest[mathtestTemp].append(RegionToList(line[:line.index(']') + 1].strip()))
            else:
                continue
    else:
        print "Please input the test file"
        exit

    #Build the dictionaries for the full
    if ffile is not None:
        ffull = open(ffile, 'r')
        ffullLines = ffull.readlines()
        for line in ffullLines:
            if line.startswith("MATH") or not RepresentInt(line[0]):
                #stop since it means the end of content section
                break
            else:
                ffLine = ffLine + 1        
        mathfullTemp = ""
        for line in ffullLines[ffLine:]:
            if line.startswith("MATH"):
                dicFull[line.split('\t')[0].strip()] = []
                mathfullTemp = line.split('\t')[0].strip()
            elif line.startswith("[") and mathfullTemp !=  "":
                #dicFull[mathfullTemp].append(RegionToList(line[:line.index(']') + 1].strip()))
                desc_seq = RegionToList(line[:line.index(']') + 1].strip())
                if desc_seq not in dicFull[mathfullTemp]:
                    dicFull[mathfullTemp].append(desc_seq)
            else:
                continue

    #Build the dictionaries for the short
    if sfile is not None:
        fshort = open(sfile, 'r')
        fshortLines = fshort.readlines()
        for line in fshortLines:
            if line.startswith("MATH") or not RepresentInt(line[0]):
                #stop since it means the end of content section
                break
            else:
                fsLine = fsLine + 1        
        mathshortTemp = ""
        for line in fshortLines[fsLine:]:
            if line.startswith("MATH"):
                dicShort[line.split('\t')[0].strip()] = []
                mathshortTemp = line.split('\t')[0].strip()
            elif line.startswith("[") and mathshortTemp !=  "":
                desc_seq = RegionToList(line[:line.index(']') + 1].strip())
                if desc_seq not in dicShort[mathshortTemp]:
                    dicShort[mathshortTemp].append(desc_seq)
            else:
                continue

    sttrueRec = 0
    stallRec = 0
    sttruePre = 0
    stallPre = 0

    sotrueRec = 0
    soallRec = 0
    sotruePre = 0
    soallPre = 0

    matched_id_strc = []
    matched_id_soft = []
          
    #DO the matching
    if (ffile is not None) ^ (sfile is not None):
        if ffile is not None:
            if ffLine == ftLine:
                #print "Strict Full"
                sttruePre, stallPre, sttrueRec, stallRec, matched_id_strc = DoMatching(dicFull, dicTest, Match.strict, Description.full)
                #print "\nSoft Full"
                sotruePre, soallPre, sotrueRec, soallRec, matched_id_soft = DoMatching(dicFull, dicTest, Match.soft, Description.full)
            else:
                print "Full and Test files are different"
        elif sfile is not None:
            if fsLine == ftLine:
                #print "\nStrict Short"
                sttruePre, stallPre, sttrueRec, stallRec, matched_id_strc = DoMatching(dicShort, dicTest, Match.strict, Description.short)
    
                #print "\nSoft Short"
                sotruePre, soallPre, sotrueRec, soallRec, matched_id_soft = DoMatching(dicShort, dicTest, Match.soft, Description.short)                
            else:
                #print sfile
                #print mfile
                print "Short and Test files are different"

    return sttruePre, stallPre, sttrueRec, stallRec, sotruePre, soallPre, sotrueRec, soallRec, matched_id_strc, matched_id_soft

def utama(golddata, mldata, address_math):
    sttrueRec = 0
    stallRec = 0
    sttruePre = 0
    stallPre = 0

    sotrueRec = 0
    soallRec = 0
    sotruePre = 0
    soallPre = 0
    
    matched_id_strict = []
    matched_id_soft = []

    for fl in os.listdir(golddata):
        pname = fl[:9]
        goldfile = golddata + fl
        mlfile = mldata + fl
        a, b, c, d, e, f, g, h, i, j = SingleFileComparison(goldfile, None, mlfile)
        #a, b, c, d, e, f, g, h, i, j = SingleFileComparison(None, goldfile, mlfile)

        sttrueRec += c
        stallRec += d
        sttruePre += a
        stallPre += b

        sotrueRec += g
        soallRec += h
        sotruePre += e
        soallPre += f
        
        #matched_id_strict.extend(i)
        #matched_id_soft.extend(j)
        matched_id_strict.extend([isi.replace('_', '_' + pname + '_') for isi in i])
        matched_id_soft.extend([isi.replace('_', '_' + pname + '_') for isi in j])

    print ""
    print "FINAL:"
    print "hasil strict"
    precision = (float)(sttruePre)/(float)(stallPre)
    recall = (float)(sttrueRec)/(float)(stallRec)
    
    print "Precision: " + str(sttruePre)+ '/' + str(stallPre)+ ' = ' + str(precision)
    print "Recall: " + str(sttrueRec) + '/' + str(stallRec) + ' = ' + str(recall)
    print "F1: " + str(2 * precision * recall / (precision+recall))

    print "hasil soft"
    precision = (float)(sotruePre)/(float)(soallPre)
    recall = (float)(sotrueRec)/(float)(soallRec)
    print "Precision: " + str(sotruePre)+ '/' + str(soallPre)+ ' = ' + str(precision)
    print "Recall: " + str(sotrueRec) + '/' + str(soallRec) + ' = ' + str(recall)
    print "F1: " + str(2 * precision * recall / (precision+recall))

    #matched_id_strict.sort()
    #matched_id_soft.sort()
    
    if address_math != None:
        with open(address_math + "strict", "w") as f:
            f.write('\n'.join(matched_id_strict))
        with open(address_math + "soft", "w") as f:
            f.write('\n'.join(matched_id_soft))
 
if __name__ == "__main__":
    options, remainder = parse_args()
    #For NTCIR-11 data
    #golddata = "D:/ntcir10/bios_long/"
    #mldata = "D:/ntcir10/result_np/"

    #For current mathcat (use dependency tree instead of predicate-argument graph)

    #For calculating the analysis result (using ACL and consider recall only)
    #golddata = "D:/Journal/dataset/test/long-acl/test_gold_annotation/"
    #mldata = "D:/Journal/dataset/test/long-acl/result_all/"
    #utama(golddata, mldata, '')

    #For calculating the P, R, F1 for all models
    golddata = "D:/Journal/dataset/test/long-new/bios_long/"
    mldatas = ["D:/Journal/dataset/test/app/result/", "D:/Journal/dataset/test/context/result/", "D:/Journal/dataset/test/long-new/analysis/", "D:/Journal/dataset/test/long-new-minnp/analysis/"]
    tgtdatas = ["D:/applong", 'D:/regexlong', 'D:/basiclong', 'D:/basicptnlong', 'D:/alllong', 'D:/basicdeplong', 'D:/minlong']

    #mldatas = ["D:/Journal/dataset/test/long-short-app/result/", "D:/Journal/dataset/test/long-short-regex/result/", "D:/Journal/dataset/test/short-new/basic/", "D:/Journal/dataset/test/short-new/basic_ptn/", "D:/Journal/dataset/test/short-new/basic_ptn_dep/", "D:/Journal/dataset/test/short-new/basic_dep/", "D:/Journal/dataset/test/short-new-minnp/basic_ptn_dep/"]
    #tgtdatas = ["D:/appshort", 'D:/regexshort', 'D:/basicshort', 'D:/basicptnshort', 'D:/allshort', 'D:/basicdepshort', 'D:/minshort']

    for i,mldata in enumerate(mldatas):
        #mldata = "D:/Journal/dataset/test/long-short-regex/result/"
        utama(golddata, mldata, '')

    #For calculating learning rate
    #for i in range(1, 11):
    #    print str(i);
    #    golddata = "D:/Journal/dataset/rate/short-new/tags/bios_short/"
    #    mldata = "D:/Journal/dataset/rate/short-new/tags/" + str(i) + "/"
    #    address_math = "D:/Journal/dataset/rate/short-new/tags/all_" + str(i)
    #    utama(golddata, mldata, address_math)
