from Preprocess import *
from os import path
if __name__ == '__main__':
    
    paragraphDir = 'D:/ntcir10/sentences/'
    parseDir = 'D:/ntcir10/parsetrees/' #argv[2]
    featureDir = 'D:/ntcir10/features/' #argv[3]
    annLongDir = 'D:/ntcir10/bios_long/' #argv[4] #will be null for final run
    annShortDir = 'D:/ntcir10/bios_short/' #argv[4] #will be null for final run
    trainFormatFile = 'D:/test/format.arff' #argv[5]


    para = '0801.2412_6.txt'
    proc = preprocess()
    parsers, ann = proc.openParserFile(path.join(paragraphDir, para), path.join(parseDir,  para.replace('.txt', '.dep.txt')), path.join(parseDir, para.replace('.txt', '.so.txt')), path.join(annLongDir, para), path.join(annShortDir, para))

