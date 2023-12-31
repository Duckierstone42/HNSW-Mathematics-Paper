class Node:
    """
    Node for a navigable small world graph.

    Parameters
    ----------
    idx : int
        For uniquely identifying a node.

    value : 1d np.ndarray
        To access the embedding associated with this node.

    neighborhood : set
        For storing adjacent nodes.

    References
    ----------
    https://book.pythontips.com/en/latest/__slots__magic.html
    https://hynek.me/articles/hashes-and-equality/
    """
    __slots__ = ['idx', 'value', 'neighborhood']

    def __init__(self, idx, value):
        self.idx = idx
        self.value = value
        self.neighborhood = set()

    def __hash__(self):
        return hash(self.idx)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.idx == other.idx
        )

from scipy.spatial import distance


def build_nsw_graph(index_factors: np.ndarray, k: int) -> List[Node]:
    n_nodes = index_factors.shape[0]

    graph = []
    for i, value in enumerate(index_factors):
        node = Node(i, value)
        if i > k:
            neighbors, hops = nsw_knn_search(graph, node.value, k)
            neighbors_indices = [node_idx for _, node_idx in neighbors]
        else:
            neighbors_indices = list(range(i))

        # insert bi-directional connection
        node.neighborhood.update(neighbors_indices)
        for i in neighbors_indices:
            graph[i].neighborhood.add(node.idx)
        
        graph.append(node)

    return graph


import heapq
import random
from typing import List, Tuple


def nsw_knn_search(
    graph: List[Node],
    query: np.ndarray,
    k: int=5,
    m: int=50) -> Tuple[List[Tuple[float, int]], float]:
    """
    Performs knn search using the navigable small world graph.

    Parameters
    ----------
    graph :
        Navigable small world graph from build_nsw_graph.

    query : 1d np.ndarray
        Query embedding that we wish to find the nearest neighbors.

    k : int
        Number of nearest neighbors returned.

    m : int
        The recall set will be chosen from m different entry points.

    Returns
    -------
    The list of nearest neighbors (distance, index) tuple.
    and the average number of hops that was made during the search.
    """
    result_queue = []
    visited_set = set()
    
    hops = 0
    for _ in range(m):
        # random entry point from all possible candidates
        entry_node = random.randint(0, len(graph) - 1)
        entry_dist = distance.cosine(query, graph[entry_node].value)
        candidate_queue = []
        heapq.heappush(candidate_queue, (entry_dist, entry_node))

        temp_result_queue = []
        while candidate_queue:
            candidate_dist, candidate_idx = heapq.heappop(candidate_queue)

            if len(result_queue) >= k:
                # if candidate is further than the k-th element from the result,
                # then we would break the repeat loop
                current_k_dist, current_k_idx = heapq.nsmallest(k, result_queue)[-1]
                if candidate_dist > current_k_dist:
                    break

            for friend_node in graph[candidate_idx].neighborhood:
                if friend_node not in visited_set:
                    visited_set.add(friend_node)

                    friend_dist = distance.cosine(query, graph[friend_node].value)
                    heapq.heappush(candidate_queue, (friend_dist, friend_node))
                    heapq.heappush(temp_result_queue, (friend_dist, friend_node))
                    hops += 1

        result_queue = list(heapq.merge(result_queue, temp_result_queue))

    return heapq.nsmallest(k, result_queue), hops / m

if __name__ == "__main__":
    k = 10

    index_factors = model.get_output_matrix()
    graph = build_nsw_graph(index_factors, k)
    # graph[0].neighborhood
    results = nsw_knn_search(graph, query_factors, k=5)
    print(results)