from os import listdir, path
from shutil import move

if __name__ == "__main__":
    dirFeatures = 'D:/ntcir10/features/nx/features-all/'
    dirTest = 'D:/ntcir10/features/nx/features-test/'
    testSet = 'D:/ntcir10/test_set.txt'
    testColl = [fl.strip() for fl in open(testSet).readlines() if fl.strip() != '']
    allFls = listdir(dirFeatures)

    for fl in allFls:
        if fl[:9] in testColl:
            move(path.join(dirFeatures, fl), path.join(dirTest, fl))

    print 'finish'
