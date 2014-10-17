from ParserInfo import ParserInfo
from Annotation import Annotation

class preprocess(object):
    """description of class"""


    def openParserFile(self, address_para, address_def, address_so, address_annLong=None, address_annShort=None):
        paragraph = [sentence for sentence in open(address_para).readlines() if sentence.strip() != '']
        content_def = open(address_def).read()
        content_so = open(address_so).read()
        lineNumber = 0

        blocks_def = content_def.split('\n\n')
        blocks_so = content_so.split('\n\n')

        parserInfos = []
        if len(blocks_def) != len(blocks_so):
            print 'Different number of blocks: ' + address_def
        else:
            for i in range(len(paragraph)):
                if '__MATH_' in paragraph[i] and 'parse_status="sentence length limit exceeded"' not in blocks_so[i]:
                    parserInfos.append(ParserInfo(lineNumber, paragraph[i], blocks_def[i], blocks_so[i]))
                else:
                    parserInfos.append(ParserInfo(lineNumber, paragraph[i], None, None))
                lineNumber += 1
        
        if address_annLong != None and address_annShort != None:
            ann = Annotation(address_annLong, address_annShort)
            return parserInfos, ann
        else:
            return parserInfos