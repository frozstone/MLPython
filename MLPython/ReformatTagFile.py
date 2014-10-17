if __name__ == '__main__':
    tagAddress = 'D:/ntcir10/tag_np_nx.txt'
    lns = open(tagAddress).readlines()
    for i in range(len(lns)):
        if lns[i].strip() != '':
            lns[i] = lns[i].split()[2][2:] + '\n'
    
    f = open(tagAddress, 'w')
    f.writelines(lns)
    f.close()
    print 'finish'