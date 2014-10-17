import xml
import re
import codecs
from xml.dom import minidom
from xml.sax.saxutils import unescape
from os import listdir, path
from sys import argv

def ctx_dic(ctx_add):
    ctx = {} #{(para.txt, __MATH_x__): context}
    lns = open(ctx_add).readlines()
    for ln in lns:
        cells = [cell.strip() for cell in ln.rstrip().split('\t')]
        if len(cells) >= 3:
            ctx[(cells[0], cells[1])] = cells[2]
    return ctx

def feat_dic(feat_dir, tag_dir):
    feats = {} #{(para.xhtml, __MATH_x__): [desc]}
    for para in [x for x in listdir(feat_dir) if x.endswith('.txt')]:
        taglns = open(path.join(tag_dir, para.replace('.txt', '.arff'))).readlines()
        featlns = open(path.join(feat_dir, para)).readlines()
        ziplns = zip(taglns, featlns)
        for ln in ziplns:
            if ln[0].startswith('True'):
                cells = [cell for cell in ln[1].rstrip().split('\t')]
                if (para, cells[0]) in feats:
                    feats[(para, cells[0])].append(cells[1])
                else:
                    feats[(para, cells[0])] = [cells[1]]
    return feats

def mathnew_dict(mathnew_add):
    lns = open(mathnew_add).readlines()
    dict1 = {} #{S5.m1.1:<xml>}
    dict2 = {} #{(para.xhtml, __MATH_x__):<xml>}
    dict3 = {} #{S5.m1.1:(para.xhtml, __MATH_x__)}
    for ln in lns:
        if ln.strip() == '':
            continue
        cells = ln.rstrip().split('\t')
        dict1[cells[0].encode('utf-8')] = minidom.parseString(cells[3])
        dict2[(cells[1], cells[2])] = minidom.parseString(ln[ln.index(cells[3]):])
        dict3[cells[0].encode('utf-8')] = (cells[1], cells[2])
    return dict1, dict2, dict3

def adj_dict(mathadj_add):
    lns = open(mathadj_add).readlines()
    adj = {}
    for ln in lns:
        if ln.strip() == '':
            continue
        cells = ln.rstrip().split('\t')
        adj[cells[0].encode('utf-8')] = []
        if len(cells) > 1:
            for child in cells[1].split(' '):
                adj[cells[0].encode('utf-8')].append(child.encode('utf-8'))
    return adj

def handleMathInText(txt, para_add, math_dict, ptn):
    retval_without_math = txt
    retval_with_math = txt
    for res in ptn.finditer(txt):
        retval_without_math = retval_without_math.replace(res.group(0), '')
        replacement =  math_dict[(para_add.replace('.txt', '.xhtml'), res.group(0))].firstChild
        if replacement == None:
            retval_with_math = retval_with_math.replace(res.group(0), '')
        else:
            retval_with_math = retval_with_math.replace(res.group(0), replacement.toxml().encode('utf-8'))
    return retval_without_math.decode('utf-8'), retval_with_math.decode('utf-8')

def generateXMLWithoutDep(ctx, feats, dict2, dict3, adjdict, format_add, xml_add):
    doc = minidom.parse(format_add)
    ptn = re.compile(r'__MATH_\d*__')

    for k,v in dict2.items():
        elexml = doc.createElement('expression')
        mid = k[1][7:-2]
        gpid = 'ntcir-math2/' + k[0]
        elexml.setAttribute('mid', mid)
        elexml.setAttribute('gmid', gpid + '#' + mid)
        #elexml.setAttribute('gumid', '')
        elexml.setAttribute('gpid', gpid)
        
        mml = v.firstChild
        mmlxml = doc.createElement('mathml')
        mmlxml.appendChild(mml)
        elexml.appendChild(mmlxml)

        if (k[0].replace('xhtml', 'txt'), k[1]) in ctx:
            ctx_wo_mt, ctx_mt = handleMathInText(ctx[(k[0].replace('xhtml', 'txt'), k[1])], k[0], dict2, ptn)
            if ctx_mt.strip() != '':
                ctxxml = minidom.parseString('<context>' + ctx_mt.encode('utf-8') + '</context>').firstChild
                elexml.appendChild(ctxxml)

        summary = (0,'')
        if (k[0].replace('xhtml', 'txt'), k[1]) in feats:
            for desc in set(feats[(k[0].replace('xhtml', 'txt'), k[1])]):
                dsc_wo_mt, dsc_mt = handleMathInText(desc, k[0], dict2, ptn)
                if dsc_mt.strip() != '':
                    descxml = minidom.parseString('<description>' + dsc_mt.encode('utf-8') + '</description>').firstChild
                    elexml.appendChild(descxml)
                if summary[0] < len(desc.split()):
                    summary = (len(desc.split()), desc)

        if summary[0] != 0:
            smr_wo_mt, smr_mt = handleMathInText(summary[1], k[0], dict2, ptn)
            smrxml = minidom.parseString('<summary>' + smr_mt.encode('utf-8') + '</summary>').firstChild
            elexml.appendChild(smrxml)


        childs = adjdict[mml.attributes['id'].value.encode('utf-8')]
        for child in childs:
            child_id = dict3[child.encode('utf-8')]
            if (child_id[0].replace('xhtml', 'txt'), child_id[1]) in ctx:
                ctx_wo_mt, ctx_mt = handleMathInText(ctx[(child_id[0].replace('xhtml', 'txt'), child_id[1])], child_id[0], dict2, ptn)
                if ctx_mt.strip() != '':
                    ctxxml = minidom.parseString('<context>' + ctx_mt.encode('utf-8') + '</context>').firstChild
                    ctxxml.setAttribute('type', 'child')
                    elexml.appendChild(ctxxml)

            if (child_id[0].replace('xhtml', 'txt'), child_id[1]) in feats:
                for desc in set(feats[(child_id[0].replace('xhtml', 'txt'), child_id[1])]):
                    dsc_wo_mt, dsc_mt = handleMathInText(desc, child_id[0], dict2, ptn)
                    if dsc_mt.strip() != '':
                        descxml = minidom.parseString('<description>' + dsc_mt.encode('utf-8') + '</description>').firstChild
                        descxml.setAttribute('type', 'child')
                        elexml.appendChild(descxml)

        doc.childNodes[0].appendChild(elexml)
    
    f = open(xml_add, 'w')
    f.write(doc.toxml('utf-8'))
    f.close()


if __name__ == '__main__':
    #ctx_add = 'D:/test/context/1/0704.0097.txt'
    #feat_dir = 'D:/test/features/feats/1/0704.0097/'
    #tag_dir = 'D:/test/features/tags/1/0704.0097/'
    #mathml_add = 'D:/test/mathml/math_new/1/0704.0097.txt'
    #mathadj_add = 'D:/test/mathml/math_adj/1/0704.0097.txt'
    #format_add = 'format.xml'
    #xml_dir = 'D:/test/xml/'

    ctx_add = argv[1]
    feat_dir = argv[2]
    tag_dir = argv[3]
    mathml_add = argv[4]
    mathadj_add = argv[5]
    format_add = argv[6]
    xml_dir = argv[7]

    ptn = re.compile(r'__MATH_\d*__')
    ctx = ctx_dic(ctx_add) #{(para.txt, __MATH_x__): context}
    feats = feat_dic(feat_dir, tag_dir) #{(para.xhtml, __MATH_x__): [desc]}
    dict1, dict2, dict3 = mathnew_dict(mathml_add) #{S5.m1.1:<xml>} {(para.xhtml, __MATH_x__):<xml>}
    adj = adj_dict(mathadj_add)
    
    generateXMLWithoutDep(ctx, feats, dict2, dict3, adj, format_add, path.join(xml_dir, path.basename(ctx_add).replace('.txt', '.xml')))
