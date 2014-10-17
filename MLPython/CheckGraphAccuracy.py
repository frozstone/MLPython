import os
import nltk
import numpy
from xml.dom import minidom
from nltk.stem import PorterStemmer
from apgl.graph import SparseGraph
from pickle import load, dump
from sys import argv

def convertmt(k, mp):
  if k in mp:
    return mp[k]
  else:
    return k

def flattenListOfText(texts):
    st = PorterStemmer()
    tokens = []
    for text in texts:
        tokens.extend(st.stem(tok.lower()) for tok in text.split(' '))
    return list(set(tokens))

def buildCtxDict(xfile):
    doc = minidom.parse(xfile)
    mts = doc.getElementsByTagName('expression')
    ctxInfo = {}
    for mt in mts:
        mtID = mt.firstChild.firstChild.getAttribute('id')
        ctxs = mt.getElementsByTagName('context')
        ctxInfo[mtID] = []
        for ctx in ctxs:
            if ctx.firstChild.nodeValue != None:
                ctxInfo[mtID].append(ctx.firstChild.nodeValue)
    return ctxInfo

def buildDscDict(xfile):
    doc = minidom.parse(xfile)
    mts = doc.getElementsByTagName('expression')
    dscInfo = {}
    for mt in mts:
        mtID = mt.firstChild.firstChild.getAttribute('id')
        dscs = mt.getElementsByTagName('description')
        dscInfo[mtID] = []
        for dsc in dscs:
            if dsc.firstChild.nodeValue != None:
                dscInfo[mtID].append(dsc.firstChild.nodeValue)
    return dscInfo

def processDictFile(dfile):
    f = open(dfile, 'rb')
    dict = load(f)
    f.close()
    dictnew = {}

    dictuniq = {}
    dictcoll = {}

    for k,v in dict.items():
        new_v = v.replace('<mrow>', '').replace('</mrow>', '')
        dictnew[k] = new_v
        if new_v not in dictuniq:
            qnum = len(dictuniq)
            dictuniq[new_v] = qnum
            dictcoll[qnum] = [k]
        else:
            qnum = dictuniq[new_v]
            dictcoll[qnum].append(k)
    return dictuniq, dictcoll

def createGraph(dictuniq):
    g = SparseGraph(len(dictuniq), False, dtype = numpy.int32)
    mts = dictuniq.keys()
    for mt in mts:
        if mt.strip() != '':
            relmts = [k for k in mts if k.strip() != '' and k in mt and k != mt]
            relmts.sort(key=len, reverse=True)
            currentGrandchildren = set([])
            for relmt in relmts:
                if relmt not in currentGrandchildren:
                    g.addEdge(dictuniq[mt], dictuniq[relmt])
                    currentGrandchildren = currentGrandchildren.union([k for k in mts if k.strip() != '' and k in relmt])
    return g

def getRelatedNodes(g, root=0, isleaf=True, hop=0, isall=False):
    if isleaf and not isall:
        #Obtain leaves
        outseq = numpy.array(g.adjacencyMatrix().sum(1), dtype=numpy.int32).ravel()
        connectedNodes = g.breadthFirstSearch(root)
        leaves = []
        for nd, outdeg in enumerate(outseq):
            if nd in connectedNodes and outdeg == 0:
                leaves.append(nd)
        return [root] + leaves
    elif not isall:
        #Obtain node from a certain number of hops
        dists = g.dijkstrasAlgorithm(root)
        relnds = []
        for nd, dist in enumerate(dists):
            if dist <= hop:
                relnds.append(nd)
        return relnds
    elif isall:
        return g.breadthFirstSearch(root)

def getTextFromVertices(vertices, dictcoll, dictctx=None, dictdesc=None):
    desc = []
    for vertex in vertices:
        for mt in dictcoll[vertex]:
            if dictctx != None:
                desc.extend(dictctx[mt])
            if dictdesc != None:
                desc.extend(dictdesc[mt])
    return flattenListOfText(desc)

def buildDictQueries(queries_add):
    st = PorterStemmer()
    lns = open(queries_add).readlines()
    dictQueries = {}
    for ln in lns:
        cells = ln.split('\t')
        dictQueries[cells[0]] = [st.stem(tok.lower()) for tok in cells[2].split(' ')]

    return dictQueries

def buildDictRank(rank_add, score_add):
    ranklns = open(rank_add).readlines()
    scorelns = open(score_add).readlines()

    dictscore = {}
    for ln in scorelns:
        cells = ln.split('\t')
        if cells[0] not in dictscore:
            dictscore[cells[0]] = {}
        dictscore[cells[0]][cells[1]] = int(cells[2])

    dictrank = {}
    for ln in ranklns:
        if ln.startswith('NTCIR10-FT-2') or ln.startswith('NTCIR10-FT-3'):
            continue
        cells = ln.split('\t')
        if cells[0] not in dictrank:
            dictrank[cells[0]] = {}
        if cells[2] in dictscore[cells[0]]:
            dictrank[cells[0]][cells[2]] = dictscore[cells[0]][cells[2]]
        else:
            dictrank[cells[0]][cells[2]] = 0
    return dictrank

def getVertexFromMID(dictcoll, mid):
    for k,v in dictcoll.items():
        if mid in v:
            return k

def buildBigDicts(mathDictDir):
    DICTuniq = {}
    DICTcoll = {}
    DICTgraph = {}
    fls = os.listdir(mathDictDir)
    for fl in fls:
        name = fl.replace('.math', '')
        dictuniq, dictcoll = processDictFile(os.path.join(mathDictDir, fl))
        graph = createGraph(dictuniq)
        DICTuniq[name] = dictuniq
        DICTcoll[name] = dictcoll
        DICTgraph[name] = graph
    return DICTuniq, DICTcoll, DICTgraph

if __name__ == '__main__':
    rank_add = 'D:/Journal/sample_se/mir_evaluation/ft/mathcat-ftedited.tsv'
    score_add = 'D:/Journal/sample_se/mir_evaluation/ft/NTCIR_10_Math_Qrels_FT.dat'
    map_add = 'D:/Journal/sample_se/mir_evaluation/ft/idmap.tsv'
    queries_add = 'D:/Journal/sample_se/mir_evaluation/ft/queries'

    xml_dir = 'D:/Journal/sample_se/mir_evaluation/ft/ft_edited_agg/'
    adj_dir = 'D:/Journal/sample_se/mir_evaluation/ft/math_adj/'
    dic_dir = 'D:/Journal/sample_se/mir_evaluation/ft/math_dict/'

    minthreshold = 1.0

    dictqueries = buildDictQueries(queries_add)
    dictrank = buildDictRank(rank_add, score_add)
    DICTuniq, DICTcoll, DICTgraph = buildBigDicts(dic_dir)
    if len(argv) > 3 and argv[3] == 'dump':
        f1 = open('duniq', 'wb')
        dump(DICTuniq, f1, -1)
        f1.close()
        f2 = open('dcoll', 'wb')
        dump(DICTcoll, f2, -1)
        f2.close()
        f3 = open('dgraph', 'wb')
        dump(DICTgraph, f3, -1)
        f3.close()

    precision = []
    recall = []
    accuracy = []

    for query, ans in dictrank.items():
        print query
        tp = 0.0
        tn = 0.0
        fp = 0.0
        fn = 0.0
        for mt, score in ans.items():
            xmlpath = os.path.join(xml_dir, mt.split('#')[0] + '.xml')
            ctxDict = buildCtxDict(xmlpath)
            dscDict = buildDscDict(xmlpath)
            #dictuniq, dictcoll = processDictFile(os.path.join(dic_dir, mt.split('#')[0]) + '.math')
            #graph = createGraph(dictuniq)
            dictuniq = DICTuniq[mt.split('#')[0]]
            dictcoll = DICTcoll[mt.split('#')[0]]
            graph = DICTgraph[mt.split('#')[0]]

            vertex_id = getVertexFromMID(dictcoll, mt.split('#')[1])

            rel_nodes = []
            if argv[2] == 'leaf':
                rel_nodes = getRelatedNodes(graph, vertex_id, True)
            elif argv[2] == 'all':
                rel_nodes = getRelatedNodes(graph, vertex_id, False, isall=True)
            elif int(argv[2]) == 1:
                rel_nodes = getRelatedNodes(graph, vertex_id, False, 1)
            elif int(argv[2]) == 2:
                rel_nodes = getRelatedNodes(graph, vertex_id, False, 2)

            texts = []
            if argv[1] == 'ctx':
                texts = getTextFromVertices(rel_nodes, dictcoll, ctxDict)
            elif argv[1] == 'desc':
                texts = getTextFromVertices(rel_nodes, dictcoll, None, dscDict)
            elif argv[1] == 'ctxdesc':
                texts = getTextFromVertices(rel_nodes, dictcoll, ctxDict, dscDict)

            matchbool = False
            for qtok in dictqueries[query]:
                if qtok in texts:
                    matchbool = True
                    break
            if matchbool and score >= minthreshold:
                tp += 1
            elif matchbool and score < minthreshold:
                fp += 1
            elif not matchbool and score >= minthreshold:
                fn += 1
            else:
                tn += 1
        precision.append(tp / (tp + fp) if (tp + fp) > 0 else 0)
        recall.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
        accuracy.append((tp+tn)/(tp + fp + fn + tn))

    print 'Precision:   ' + str(sum(precision)/len(precision))
    print recall
    print 'Recall:      ' + str(sum(recall)/len(recall))
    print 'Accuracy:    ' + str(sum(accuracy)/len(accuracy))
