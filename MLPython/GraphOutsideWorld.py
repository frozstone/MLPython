from pickle import load
from os import path
import operator as op
from xml.dom import minidom
from apgl.graph import SparseGraph
import igraph as ig
import os

def ReverseDictUniq(dictuniq):
    return {v:k for k,v in dictuniq.items()}

def ConcatenateSameMaths(mts):
    return '#'.join(mts)

def GeneratePlotting(gexf_dir, gname, gr, duniq, dcoll, alttext):
    nvertices = gr.getNumVertices()
    edges = gr.getAllEdges()

    dictuniq_reversed = ReverseDictUniq(duniq[gname])

    mms = dictuniq_reversed.items()
    mms.sort(key=op.itemgetter(0))
    xms = [mt[1].encode('utf-8') for mt in mms]

    mts = dcoll[gname].items() #{0:['id123','id456']}
    mts.sort(key=op.itemgetter(0))
    ids = [ConcatenateSameMaths(mt[1]) for mt in mts]
    tex = [alttext[mt[1][0]].encode('utf-8') if mt[1][0] in alttext else '' for mt in mts]

    igr = ig.Graph(nvertices, directed=True)
    igr.vs['mid'] = ids
    igr.vs['label'] = tex #put xms to show mathml; put tex to show tex expressions
    for edge in edges:
        igr.add_edge(edge[0], edge[1])

    #igr.write_dot(path.join(gexf_dir, gname + '.viz'))
    igr.write_graphml(path.join(gexf_dir, gname + '.gexf'))

def ConvertToNormalGephi(gexf_dir, gname):
    doc = minidom.parse(path.join(gexf_dir, gname + '.gexf'))
    newdoc = minidom.parse('format.gexf')
    nodes = doc.getElementsByTagName('node')
    edges = doc.getElementsByTagName('edge')
    if nodes[0].getElementsByTagName('data')[1].firstChild == None:
        return

    for nd in nodes:
        newele = newdoc.createElement('node')
        newele.setAttribute('id', nd.getAttribute('id'))

        data = nd.getElementsByTagName('data')
        newele.setAttribute('mid', data[0].firstChild.nodeValue.encode('utf-8'))
        if data[1].firstChild != None:
            newele.setAttribute('label', data[1].firstChild.nodeValue.encode('utf-8'))
        newdoc.firstChild.firstChild.appendChild(newele)
    for edge in edges:
        newdoc.firstChild.firstChild.appendChild(edge)

    f = open(path.join(gexf_dir, 'gexf', gname + '.gexf'), 'w')
    newdoc.writexml(f)
    f.close()


if __name__ == '__main__':
    duniq_add = 'D:/graph-accuracy/duniq'
    dcoll_add = 'D:/graph-accuracy/dcoll'
    dgraph_add = 'D:/graph-accuracy/dgraph'
    xml_dir = 'D:/Journal/sample_se/mir_evaluation/ft/ft_edited_agg/'
    gexf_dir = 'D:/graph-accuracy/graph-files/'

    f3 = open(dgraph_add, 'rb')
    dgraph = load(f3)
    f3.close()

    f1 = open(duniq_add, 'rb')
    duniq = load(f1)
    f1.close()

    f2 = open(dcoll_add, 'rb')
    dcoll = load(f2)
    f2.close()

    for gname, gr in dgraph.items():
        print gname
        #gname = 'f089989'
        #gr = dgraph['f089989']
        doc = minidom.parse(path.join(xml_dir, gname + '.xml'))
        alttext = {ele.getAttribute('id'):ele.getAttribute('alttext') for ele in doc.getElementsByTagName('math')}
        GeneratePlotting(gexf_dir, gname, gr, duniq, dcoll, alttext)
        ConvertToNormalGephi(gexf_dir, gname)

    print 'Finish'
