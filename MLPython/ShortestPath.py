from itertools import chain
from scipy.sparse import coo_matrix
from numpy import ones, Inf
from scipy.sparse.csgraph._shortest_path import floyd_warshall

class ShortestPath(object):
    __dist = []
    __pred = []
    __rels = []
    __arcm = ''
    def __init__(self, relations):
        self.__rels = []
        self.__rels = relations
        edges = []
        size = 0
        for relation in relations:
            rel = relation[0]
            fm = relation[1]
            to = relation[2]
            if size < max(fm, to):
                size = max(fm, to)
            if fm == -1 or to == -1:
                continue
            edges.append((rel, fm ,to))
        rels = [edge[0] for edge in edges]
        fms = [edge[1] for edge in edges]
        tos = [edge[2] for edge in edges]
        
        size += 1
        arcm = coo_matrix((ones(len(fms)), (fms, tos)), shape=(size, size)).tocsr()
        self.__dist, self.__pred = floyd_warshall(arcm, directed = False, return_predecessors = True, unweighted = True)

    def __ObtainDistanceAndPath(self, np_startidx, np_endidx, math_idx):
        distance = Inf
        np_target = -1
        for id in range(np_startidx, np_endidx + 1):
            if distance > self.__dist[math_idx][id] and math_idx != id:
                distance = self.__dist[math_idx][id]
                np_target = id
        nodes = []
        path = []
        if math_idx != np_target:
            nodes = self.__ConstructSP(math_idx, np_target)
            path = self.__NodesToRels(nodes)
        else:
            path = []
        return distance, np_target, nodes, path
            
    def __ConstructSP(self, first, second):
        k = self.__pred[first][second]
        #print [first, k, second]
        if k < 0 or k == first or k == second:
            return [first, second]
        else:
            recurrence_first = self.__ConstructSP(first, k)
            recurrence_second = self.__ConstructSP(k, second)
            
            return recurrence_first + recurrence_second[1:]
        
    def __listCheckFirstOccurence(self, fm ,to):
        for rel in self.__rels:
            if (rel[1] == fm and rel[2] == to) or (rel[1] == to and rel[2] == fm):
                return rel[0]
        return ''

    def __NodesToRels(self, nodes):
        if len(nodes) <= 1:
            return ''
        path = []
        for i in range(len(nodes) - 1):
            path.append(self.__listCheckFirstOccurence(nodes[i], nodes[i+1]))
        
        return ' '.join(path)

    def TenthFeature(self, np_startidx, np_endidx, math_idx):
        distance, np_target, nodes, path = self.__ObtainDistanceAndPath(np_startidx, np_endidx, math_idx)
        rel_math = []
        rel_np = []
        
        node_in_path = [nd for nd in path.split(' ') if nd.strip() != '']
        #print node_in_path
        #Calculate the dep relation
        rel_math = node_in_path[:3]
        rel_np = node_in_path[-3:]
            
        math_out = None
        np_out = None
        if len(node_in_path) > 0:
            math_out = len([rel[0] for rel in self.__rels if rel[1] == math_idx and rel[2] == nodes[0]]) > 0
            np_out = len([rel[0] for rel in self.__rels if rel[1] == nodes[-1] and rel[2] == nodes[-2]]) > 0
            
        #return distance, rel_math, rel_np, math_out, np_out
        return distance, node_in_path