from nltk.stem import PorterStemmer
from os import path

def buildDictQueries(queries_add):
    st = PorterStemmer()
    lns = open(queries_add).readlines()
    dictQueries = {}
    for ln in lns:
        cells = ln.split('\t')
        dictQueries[cells[0]] = [st.stem(tok.lower().strip()) for tok in cells[2].split(' ')]

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

def docToToken(doc_add, st):
    lns = open(doc_add).readlines()
    #print lns
    tokens = []
    for ln in lns:
        tokens.extend(st.stem(tok.lower().strip()) for tok in ln.split(' '))
    return list(set(tokens))

if __name__ == '__main__':
    rank_add = 'D:/Journal/sample_se/mir_evaluation/ft/mathcat-ftedited.tsv'
    score_add = 'D:/Journal/sample_se/mir_evaluation/ft/NTCIR_10_Math_Qrels_FT.dat'
    map_add = 'D:/Journal/sample_se/mir_evaluation/ft/idmap.tsv'
    queries_add = 'D:/Journal/sample_se/mir_evaluation/ft/queries'

    corpus_dir = 'D:/graph-accuracy/corpus/'

    minthreshold = 1.0

    st = PorterStemmer()
    dictqueries = buildDictQueries(queries_add)
    dictrank = buildDictRank(rank_add, score_add)
    precision = []
    recall = []
    accuracy = []
    for query,res in dictrank.items():
        tp = 0.0
        fp = 0.0
        tn = 0.0
        fn = 0.0
        for mts, score in res.items():
            paper = mts.split('#')[0]
            texts = docToToken(path.join(corpus_dir, paper + '.txt'), st)
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
