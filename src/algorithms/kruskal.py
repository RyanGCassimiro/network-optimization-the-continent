from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class Edge:
    weight: float
    source: str = field(compare=False)
    target: str = field(compare=False)
    metadata: dict = field(default_factory=dict, compare=False)

    def __repr__(self) -> str:
        return f"Edge({self.source!r} -> {self.target!r}, weight={self.weight})"


@dataclass
class KruskalResult:
    mst_edges: list[Edge]
    total_cost: float
    is_connected: bool
    nodes_count: int
    edges_considered: int

    @property
    def edges_count(self) -> int:
        return len(self.mst_edges)

    def __repr__(self) -> str:
        status = "conectado" if self.is_connected else "desconectado"
        return (
            f"KruskalResult(custo={self.total_cost}, "
            f"arestas={self.edges_count}/{self.nodes_count - 1}, "
            f"grafo={status})"
        )


class UnionFind:
    """Union-Find com path compression e union by rank."""

    def __init__(self, nodes: list[str]) -> None:
        self._parent: dict[str, str] = {n: n for n in nodes}
        self._rank: dict[str, int] = {n: 0 for n in nodes}

    def find(self, node: str) -> str:
        if self._parent[node] != node:
            self._parent[node] = self.find(self._parent[node])  # path compression
        return self._parent[node]

    def union(self, a: str, b: str) -> bool:
        """Une os conjuntos de a e b. Retorna False se já estavam unidos (ciclo)."""
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        # union by rank
        if self._rank[root_a] < self._rank[root_b]:
            root_a, root_b = root_b, root_a

        self._parent[root_b] = root_a
        if self._rank[root_a] == self._rank[root_b]:
            self._rank[root_a] += 1

        return True

    def connected(self, a: str, b: str) -> bool:
        return self.find(a) == self.find(b)


def kruskal(nodes: list[str], edges: list[Edge]) -> KruskalResult:
    """
    Algoritmo de Kruskal para MST.

    Complexidade: O(E log E) onde E = número de arestas.
    Ordena arestas por peso e usa Union-Find para evitar ciclos.
    """
    if not nodes:
        return KruskalResult(
            mst_edges=[], total_cost=0.0,
            is_connected=True, nodes_count=0, edges_considered=0,
        )

    sorted_edges = sorted(edges)  # ordena por weight (campo 'order=True' no Edge)
    uf = UnionFind(nodes)
    mst_edges: list[Edge] = []
    total_cost = 0.0
    target_edges = len(nodes) - 1

    for edge in sorted_edges:
        if len(mst_edges) == target_edges:
            break

        if uf.union(edge.source, edge.target):
            mst_edges.append(edge)
            total_cost += edge.weight

    is_connected = len(mst_edges) == target_edges

    return KruskalResult(
        mst_edges=mst_edges,
        total_cost=total_cost,
        is_connected=is_connected,
        nodes_count=len(nodes),
        edges_considered=len(sorted_edges),
    )