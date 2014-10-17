from os import listdir, path

if __name__ == "__main__":
    diraddress = 'D:/ntcir10/features/nx/features-test'
    fmtaddress = 'D:/ntcir10/format.arff'
    arfftgtaddress = 'D:/ntcir10/features/nx/test.arff'
    txttgtaddress = 'D:/ntcir10/features/nx/test.txt'
    
    arfffls = [fl for fl in listdir(diraddress) if fl.endswith('.arff')]

    trainLines = open(fmtaddress).readlines()
    txtLines = []
    for fl in arfffls:
        arfflns = [ln for ln in open(path.join(diraddress, fl)).readlines() if not ln.startswith('@') and ln.strip() != '']
        trainLines.extend(arfflns)

        txtlns = [fl.replace('arff', 'txt') + '\t' + ln for ln in open(path.join(diraddress, fl.replace('.arff', '.txt'))) if ln.strip() != '']
        txtLines.extend(txtlns)

    f1 = open(arfftgtaddress, 'w')
    f1.writelines(trainLines)
    f1.close()

    f2 = open(txttgtaddress, 'w')
    f2.writelines(txtLines)
    f2.close()

    print 'finish'