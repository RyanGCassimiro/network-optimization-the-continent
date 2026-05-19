from dataclasses import dataclass
from typing import Literal

from src.algorithms.kruskal import Edge, KruskalResult, kruskal
from src.models.neighborhood import Neighborhood

Algorithm = Literal["kruskal", "prim"]


@dataclass
class SolverResult:
    algorithm: Algorithm
    mst_edges: list[Edge]
    total_cost: float
    is_connected: bool
    nodes_count: int
    edges_in_mst: int
    edges_available: int
    savings: float
    savings_pct: float

    def __repr__(self) -> str:
        return (
            f"SolverResult(algorithm={self.algorithm!r}, "
            f"custo={self.total_cost:,.0f}, "
            f"economia={self.savings_pct:.1f}%)"
        )


class MSTSolver:
    def __init__(
        self,
        neighborhoods: list[Neighborhood],
        connections: list[dict],
    ) -> None:
        self._neighborhoods = {n.id: n for n in neighborhoods}
        self._edges = self._build_edges(connections)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(self, algorithm: Algorithm = "kruskal") -> SolverResult:
        if algorithm == "kruskal":
            return self._run_kruskal()
        if algorithm == "prim":
            return self._run_prim()
        raise ValueError(f"Algoritmo desconhecido: {algorithm!r}. Use 'kruskal' ou 'prim'.")

    def compare(self) -> dict[Algorithm, SolverResult]:
        """Roda ambos os algoritmos e retorna os resultados para comparação."""
        return {
            "kruskal": self._run_kruskal(),
            "prim": self._run_prim(),
        }

    @property
    def neighborhoods(self) -> dict[str, Neighborhood]:
        return self._neighborhoods

    @property
    def edges(self) -> list[Edge]:
        return self._edges

    @property
    def total_network_cost(self) -> float:
        return sum(e.weight for e in self._edges)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_edges(self, connections: list[dict]) -> list[Edge]:
        return [
            Edge(
                weight=c["cost"],
                source=c["source"],
                target=c["target"],
                metadata={
                    "id": c["id"],
                    "distance_km": c["distance_km"],
                    "terrain": c["terrain"],
                    "terrain_multiplier": c["terrain_multiplier"],
                    "notes": c.get("notes", ""),
                },
            )
            for c in connections
        ]

    def _make_result(self, algorithm: Algorithm, raw: KruskalResult) -> SolverResult:
        savings = self.total_network_cost - raw.total_cost
        savings_pct = (savings / self.total_network_cost * 100) if self.total_network_cost else 0.0
        return SolverResult(
            algorithm=algorithm,
            mst_edges=raw.mst_edges,
            total_cost=raw.total_cost,
            is_connected=raw.is_connected,
            nodes_count=raw.nodes_count,
            edges_in_mst=raw.edges_count,
            edges_available=raw.edges_considered,
            savings=savings,
            savings_pct=savings_pct,
        )

    def _run_kruskal(self) -> SolverResult:
        nodes = list(self._neighborhoods.keys())
        raw = kruskal(nodes, self._edges)
        return self._make_result("kruskal", raw)

    def _run_prim(self) -> SolverResult:
        # Ryan implementa prim.py — interface esperada:
        #   from src.algorithms.prim import prim
        #   raw = prim(nodes, edges, start=nodes[0])  -> KruskalResult
        try:
            from src.algorithms.prim import prim

            nodes = list(self._neighborhoods.keys())
            raw = prim(nodes, self._edges, start=nodes[0])
            return self._make_result("prim", raw)
        except ImportError:
            raise NotImplementedError(
                "prim.py ainda não implementado. "
                "Aguardando contribuição de Ryan (src/algorithms/prim.py)."
            )