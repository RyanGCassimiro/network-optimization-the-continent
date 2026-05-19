"""
<<<<<<< HEAD
test_algorithms.py - Testes unitários para Prim, MSTSolver e Neighborhood.
"""
import pytest

from src.models.neighborhood import Coords, Neighborhood
from src.models.graph import FiberGraph
from src.algorithms.kruskal import Edge, KruskalResult, kruskal
from src.algorithms.prim import prim, prim_mst, prim_mst_summary
from src.algorithms.mst_solver import MSTSolver, SolverResult


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def simple_nodes():
    return ["A", "B", "C", "D"]


@pytest.fixture
def simple_edges():
    return [
        Edge(weight=1, source="A", target="B", metadata={"distance_km": 10, "terrain": "planicie", "terrain_multiplier": 1.0}),
        Edge(weight=2, source="B", target="C", metadata={"distance_km": 20, "terrain": "floresta", "terrain_multiplier": 1.4}),
        Edge(weight=3, source="C", target="D", metadata={"distance_km": 30, "terrain": "montanha", "terrain_multiplier": 2.5}),
        Edge(weight=4, source="D", target="A", metadata={"distance_km": 40, "terrain": "planicie", "terrain_multiplier": 1.0}),
        Edge(weight=10, source="A", target="C", metadata={"distance_km": 100, "terrain": "mar", "terrain_multiplier": 3.5}),
    ]


@pytest.fixture
def simple_solver(simple_nodes, simple_edges):
    neighborhoods = [
        Neighborhood(id=n, name=f"Reino {n}", region="norte", coords=Coords(x=float(i * 10), y=0.0))
        for i, n in enumerate(simple_nodes)
    ]
    connections = [
        {
            "id": f"conn_{e.source}_{e.target}",
            "source": e.source,
            "target": e.target,
            "distance_km": e.metadata["distance_km"],
            "terrain": e.metadata["terrain"],
            "cost": e.weight,
            "terrain_multiplier": e.metadata["terrain_multiplier"],
        }
        for e in simple_edges
    ]
    return MSTSolver(neighborhoods, connections)


@pytest.fixture
def connected_fiber_graph():
    g = FiberGraph()
    for node in ["A", "B", "C", "D"]:
        g.add_node(node)
    g.add_edge("A", "B", weight=1.0)
    g.add_edge("B", "C", weight=2.0)
    g.add_edge("C", "D", weight=3.0)
    g.add_edge("D", "A", weight=4.0)
    g.add_edge("A", "C", weight=10.0)
    return g


# ========================================================================
# Coords
# ========================================================================

class TestCoords:
    def test_distancia_zero_para_mesmo_ponto(self):
        c = Coords(x=5.0, y=5.0)
        assert c.distance_to(c) == pytest.approx(0.0)

    def test_distancia_positiva(self):
        a = Coords(x=0.0, y=0.0)
        b = Coords(x=3.0, y=4.0)
        assert a.distance_to(b) == pytest.approx(5.0)

    def test_distancia_simetrica(self):
        a = Coords(x=1.0, y=2.0)
        b = Coords(x=4.0, y=6.0)
        assert a.distance_to(b) == pytest.approx(b.distance_to(a))

    def test_repr(self):
        c = Coords(x=1.5, y=2.5)
        assert "1.5" in repr(c)
        assert "2.5" in repr(c)


# ========================================================================
# Neighborhood
# ========================================================================

class TestNeighborhood:
    def test_from_dict_campos_obrigatorios(self):
        data = {"id": "redania", "name": "Redania", "region": "norte", "coords": {"x": 295.0, "y": 205.0}}
        n = Neighborhood.from_dict(data)
        assert n.id == "redania"
        assert n.name == "Redania"
        assert n.region == "norte"
        assert isinstance(n.coords, Coords)

    def test_from_dict_campos_opcionais_com_defaults(self):
        data = {"id": "x", "name": "X", "region": "sul", "coords": {"x": 0.0, "y": 0.0}}
        n = Neighborhood.from_dict(data)
        assert n.capital == ""
        assert n.population == 0
        assert n.description == ""

    def test_from_dict_campos_opcionais_preenchidos(self):
        data = {
            "id": "kovir", "name": "Kovir", "region": "norte",
            "coords": {"x": 190.0, "y": 55.0},
            "capital": "Lan Exeter", "population_estimate": 320000, "description": "Reino rico",
        }
        n = Neighborhood.from_dict(data)
        assert n.capital == "Lan Exeter"
        assert n.population == 320000

    def test_is_in_region_case_insensitive(self):
        n = Neighborhood(id="x", name="X", region="Norte", coords=Coords(0, 0))
        assert n.is_in_region("norte") is True
        assert n.is_in_region("NORTE") is True

    def test_is_in_region_falso(self):
        n = Neighborhood(id="x", name="X", region="norte", coords=Coords(0, 0))
        assert n.is_in_region("sul") is False

    def test_hash_por_id(self):
        n1 = Neighborhood(id="redania", name="Redania", region="norte", coords=Coords(0, 0))
        n2 = Neighborhood(id="redania", name="Outro Nome", region="sul", coords=Coords(9, 9))
        assert hash(n1) == hash(n2)
        assert n1 == n2

    def test_eq_diferentes_ids(self):
        n1 = Neighborhood(id="redania", name="X", region="norte", coords=Coords(0, 0))
        n2 = Neighborhood(id="nilfgaard", name="X", region="norte", coords=Coords(0, 0))
        assert n1 != n2

    def test_repr(self):
        n = Neighborhood(id="redania", name="Redania", region="norte", coords=Coords(0, 0))
        r = repr(n)
        assert "redania" in r
        assert "Redania" in r


# ========================================================================
# prim_mst
# ========================================================================

class TestPrimMst:
    def test_retorna_dict_com_chaves_esperadas(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        assert isinstance(result, dict)
        assert {"edges", "total_weight", "nodes_visited", "algorithm"} <= result.keys()
        assert result["algorithm"] == "Prim"

    def test_mst_tem_n_menos_1_arestas(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        assert len(result["edges"]) == connected_fiber_graph.get_node_count() - 1

    def test_custo_total_igual_soma_das_arestas(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        soma = sum(w for _, _, w in result["edges"])
        assert result["total_weight"] == pytest.approx(soma, abs=1e-3)

    def test_custo_minimo_correto(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        # A-B(1) + B-C(2) + C-D(3) = 6
        assert result["total_weight"] == pytest.approx(6.0, abs=1e-3)

    def test_start_node_personalizado(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph, start_node="C")
        assert result["nodes_visited"][0] == "C"

    def test_start_node_inexistente_levanta_keyerror(self, connected_fiber_graph):
        with pytest.raises(KeyError):
            prim_mst(connected_fiber_graph, start_node="Z")

    def test_grafo_vazio_levanta_valueerror(self):
        with pytest.raises(ValueError, match="vazio"):
            prim_mst(FiberGraph())

    def test_grafo_desconectado_levanta_valueerror(self):
        g = FiberGraph()
        for node in ["A", "B", "C"]:
            g.add_node(node)
        g.add_edge("A", "B", weight=1.0)
        with pytest.raises(ValueError, match="conexo"):
            prim_mst(g)

    def test_todos_nos_visitados(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        assert set(result["nodes_visited"]) == set(connected_fiber_graph.get_nodes())


# ========================================================================
# prim() — interface compatível com MSTSolver
# ========================================================================

class TestPrimAdapter:
    def test_retorna_kruskal_result(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        assert isinstance(result, KruskalResult)

    def test_n_menos_1_arestas(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        assert result.edges_count == len(simple_nodes) - 1

    def test_custo_igual_ao_kruskal(self, simple_nodes, simple_edges):
        prim_cost = prim(simple_nodes, simple_edges, start=simple_nodes[0]).total_cost
        kruskal_cost = kruskal(simple_nodes, simple_edges).total_cost
        assert prim_cost == pytest.approx(kruskal_cost, rel=1e-3)

    def test_is_connected_true(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        assert result.is_connected is True

    def test_mst_edges_sao_do_tipo_edge(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        assert all(isinstance(e, Edge) for e in result.mst_edges)

    def test_nodes_count(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        assert result.nodes_count == len(simple_nodes)

    def test_edges_considered(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        assert result.edges_considered == len(simple_edges)

    def test_metadata_preservada_nas_arestas(self, simple_nodes, simple_edges):
        result = prim(simple_nodes, simple_edges, start=simple_nodes[0])
        for e in result.mst_edges:
            assert "terrain" in e.metadata
            assert "distance_km" in e.metadata


# ========================================================================
# prim_mst_summary
# ========================================================================

class TestPrimMstSummary:
    def test_retorna_string(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        assert isinstance(prim_mst_summary(result), str)

    def test_contem_cabecalho_prim(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        assert "Prim" in prim_mst_summary(result)

    def test_contem_custo_total(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        assert "Custo total" in prim_mst_summary(result)

    def test_contem_todos_nos_visitados(self, connected_fiber_graph):
        result = prim_mst(connected_fiber_graph)
        summary = prim_mst_summary(result)
        for node in result["nodes_visited"]:
            assert node in summary


# ========================================================================
# MSTSolver
# ========================================================================

class TestMSTSolver:
    def test_solve_kruskal_retorna_solver_result(self, simple_solver):
        result = simple_solver.solve(algorithm="kruskal")
        assert isinstance(result, SolverResult)
        assert result.algorithm == "kruskal"

    def test_solve_prim_retorna_solver_result(self, simple_solver):
        result = simple_solver.solve(algorithm="prim")
        assert isinstance(result, SolverResult)
        assert result.algorithm == "prim"

    def test_algoritmo_desconhecido_levanta_valueerror(self, simple_solver):
        with pytest.raises(ValueError, match="desconhecido"):
            simple_solver.solve(algorithm="dijkstra")  # type: ignore

    def test_custo_total_positivo(self, simple_solver):
        assert simple_solver.solve().total_cost > 0

    def test_is_connected_true(self, simple_solver):
        assert simple_solver.solve().is_connected is True

    def test_nodes_count(self, simple_solver, simple_nodes):
        assert simple_solver.solve().nodes_count == len(simple_nodes)

    def test_edges_in_mst_e_n_menos_1(self, simple_solver, simple_nodes):
        assert simple_solver.solve().edges_in_mst == len(simple_nodes) - 1

    def test_economia_nao_negativa(self, simple_solver):
        result = simple_solver.solve()
        assert result.savings >= 0
        assert result.savings_pct >= 0

    def test_compare_retorna_kruskal_e_prim(self, simple_solver):
        assert set(simple_solver.compare().keys()) == {"kruskal", "prim"}

    def test_compare_kruskal_e_prim_mesmo_custo(self, simple_solver):
        results = simple_solver.compare()
        assert results["kruskal"].total_cost == pytest.approx(results["prim"].total_cost, rel=1e-3)

    def test_property_neighborhoods(self, simple_solver, simple_nodes):
        assert set(simple_solver.neighborhoods.keys()) == set(simple_nodes)

    def test_property_edges(self, simple_solver, simple_edges):
        assert len(simple_solver.edges) == len(simple_edges)

    def test_total_network_cost(self, simple_solver, simple_edges):
        assert simple_solver.total_network_cost == pytest.approx(sum(e.weight for e in simple_edges))

    def test_solver_result_repr(self, simple_solver):
        assert "kruskal" in repr(simple_solver.solve())

    def test_grafo_desconectado_is_connected_false(self):
        neighborhoods = [
            Neighborhood(id=n, name=f"Reino {n}", region="norte", coords=Coords(float(i), 0))
            for i, n in enumerate(["A", "B", "C", "D"])
        ]
        connections = [
            {"id": "c1", "source": "A", "target": "B", "distance_km": 1, "terrain": "planicie", "cost": 1, "terrain_multiplier": 1.0},
            {"id": "c2", "source": "C", "target": "D", "distance_km": 1, "terrain": "planicie", "cost": 1, "terrain_multiplier": 1.0},
        ]
        solver = MSTSolver(neighborhoods, connections)
        assert solver.solve(algorithm="kruskal").is_connected is False
=======
Testes unitários dos algoritmos MST.
Responsável: Wanessa
"""
import pytest

from src.algorithms.kruskal import Edge, KruskalResult, UnionFind, kruskal


# Fixtures

@pytest.fixture
def triangle():
    """Grafo triângulo: A-B-C com pesos conhecidos. MST deve excluir a aresta mais cara."""
    nodes = ["A", "B", "C"]
    edges = [
        Edge(weight=1, source="A", target="B"),
        Edge(weight=2, source="B", target="C"),
        Edge(weight=10, source="A", target="C"),  # deve ser excluída
    ]
    return nodes, edges


@pytest.fixture
def square():
    """Quadrado A-B-C-D. MST tem 3 arestas."""
    nodes = ["A", "B", "C", "D"]
    edges = [
        Edge(weight=1, source="A", target="B"),
        Edge(weight=2, source="B", target="C"),
        Edge(weight=3, source="C", target="D"),
        Edge(weight=4, source="D", target="A"),
        Edge(weight=5, source="A", target="C"),  # diagonal cara
        Edge(weight=6, source="B", target="D"),  # diagonal cara
    ]
    return nodes, edges


@pytest.fixture
def disconnected():
    """Grafo desconectado: {A-B} e {C-D} sem ponte entre eles."""
    nodes = ["A", "B", "C", "D"]
    edges = [
        Edge(weight=1, source="A", target="B"),
        Edge(weight=1, source="C", target="D"),
    ]
    return nodes, edges


# UnionFind


class TestUnionFind:
    def test_cada_no_e_seu_proprio_representante(self):
        uf = UnionFind(["X", "Y", "Z"])
        assert uf.find("X") == "X"
        assert uf.find("Y") == "Y"

    def test_union_retorna_true_na_primeira_uniao(self):
        uf = UnionFind(["A", "B"])
        assert uf.union("A", "B") is True

    def test_union_retorna_false_em_ciclo(self):
        uf = UnionFind(["A", "B", "C"])
        uf.union("A", "B")
        uf.union("B", "C")
        assert uf.union("A", "C") is False  # ciclo

    def test_connected_apos_union(self):
        uf = UnionFind(["A", "B", "C"])
        uf.union("A", "B")
        assert uf.connected("A", "B") is True
        assert uf.connected("A", "C") is False

    def test_path_compression_nao_altera_resultado(self):
        uf = UnionFind(["A", "B", "C", "D"])
        uf.union("A", "B")
        uf.union("B", "C")
        uf.union("C", "D")
        # Após path compression, todos devem ter o mesmo representante
        root = uf.find("A")
        assert uf.find("D") == root

    def test_union_by_rank_nao_cria_ciclo(self):
        uf = UnionFind(["A", "B", "C", "D"])
        uf.union("A", "B")
        uf.union("C", "D")
        uf.union("A", "C")
        assert uf.connected("B", "D") is True


# Edge

class TestEdge:
    def test_edge_ordenavel_por_weight(self):
        edges = [
            Edge(weight=30, source="A", target="B"),
            Edge(weight=10, source="C", target="D"),
            Edge(weight=20, source="E", target="F"),
        ]
        assert sorted(edges)[0].weight == 10
        assert sorted(edges)[-1].weight == 30

    def test_edge_metadata_opcional(self):
        e = Edge(weight=5, source="X", target="Y")
        assert e.metadata == {}

    def test_edge_metadata_preservado(self):
        e = Edge(weight=5, source="X", target="Y", metadata={"terrain": "planicie"})
        assert e.metadata["terrain"] == "planicie"

    def test_edge_repr(self):
        e = Edge(weight=100, source="Temeria", target="Cintra")
        assert "Temeria" in repr(e)
        assert "Cintra" in repr(e)


# Kruskal — casos básicos


class TestKruskalBasico:
    def test_grafo_vazio(self):
        result = kruskal([], [])
        assert result.mst_edges == []
        assert result.total_cost == 0
        assert result.is_connected is True

    def test_no_unico(self):
        result = kruskal(["A"], [])
        assert result.edges_count == 0
        assert result.is_connected is True

    def test_dois_nos_uma_aresta(self):
        nodes = ["A", "B"]
        edges = [Edge(weight=7, source="A", target="B")]
        result = kruskal(nodes, edges)
        assert result.edges_count == 1
        assert result.total_cost == 7
        assert result.is_connected is True

    def test_triangulo_exclui_aresta_mais_cara(self, triangle):
        nodes, edges = triangle
        result = kruskal(nodes, edges)
        assert result.edges_count == 2
        assert result.total_cost == 3  # 1 + 2
        weights = {e.weight for e in result.mst_edges}
        assert 10 not in weights

    def test_quadrado_tem_3_arestas(self, square):
        nodes, edges = square
        result = kruskal(nodes, edges)
        assert result.edges_count == 3
        assert result.total_cost == 6  # 1 + 2 + 3

    def test_grafo_desconectado(self, disconnected):
        nodes, edges = disconnected
        result = kruskal(nodes, edges)
        assert result.is_connected is False
        assert result.edges_count < len(nodes) - 1


# Kruskal — propriedades da MST

class TestKruskalPropriedadesMST:
    def test_mst_tem_n_menos_1_arestas(self, triangle, square):
        for nodes, edges in [triangle, square]:
            result = kruskal(nodes, edges)
            assert result.edges_count == len(nodes) - 1

    def test_mst_sem_ciclos(self, square):
        nodes, edges = square
        result = kruskal(nodes, edges)
        # Union-Find verifica: se não houve ciclo, cada aresta une componentes distintos
        uf = UnionFind(nodes)
        for e in result.mst_edges:
            assert uf.union(e.source, e.target) is True

    def test_mst_e_subconjunto_das_arestas_originais(self, square):
        nodes, edges = square
        result = kruskal(nodes, edges)
        original_pairs = {(e.source, e.target) for e in edges} | {(e.target, e.source) for e in edges}
        for e in result.mst_edges:
            assert (e.source, e.target) in original_pairs or (e.target, e.source) in original_pairs

    def test_arestas_paralelas_usa_a_mais_barata(self):
        nodes = ["A", "B"]
        edges = [
            Edge(weight=10, source="A", target="B"),
            Edge(weight=3, source="A", target="B"),
            Edge(weight=7, source="A", target="B"),
        ]
        result = kruskal(nodes, edges)
        assert result.total_cost == 3

    def test_todos_nos_estao_na_mst(self, square):
        nodes, edges = square
        result = kruskal(nodes, edges)
        nos_na_mst = {e.source for e in result.mst_edges} | {e.target for e in result.mst_edges}
        assert nos_na_mst == set(nodes)

    def test_mst_e_minima_custo_total(self):
        """Verifica por força bruta que Kruskal acha o custo mínimo real."""
        from itertools import combinations

        nodes = ["A", "B", "C", "D"]
        edges = [
            Edge(weight=1, source="A", target="B"),
            Edge(weight=4, source="A", target="C"),
            Edge(weight=3, source="A", target="D"),
            Edge(weight=2, source="B", target="C"),
            Edge(weight=5, source="B", target="D"),
            Edge(weight=6, source="C", target="D"),
        ]

        kruskal_cost = kruskal(nodes, edges).total_cost

        # força bruta: testa todas as combinações de n-1 arestas que conectam o grafo
        def is_spanning(chosen, all_nodes):
            adj: dict[str, set] = {n: set() for n in all_nodes}
            for e in chosen:
                adj[e.source].add(e.target)
                adj[e.target].add(e.source)
            visited, queue = set(), [all_nodes[0]]
            while queue:
                node = queue.pop()
                if node in visited:
                    continue
                visited.add(node)
                queue.extend(adj[node] - visited)
            return visited == set(all_nodes)

        min_brute = min(
            sum(e.weight for e in combo)
            for combo in combinations(edges, len(nodes) - 1)
            if is_spanning(list(combo), nodes)
        )
        assert kruskal_cost == min_brute

# KruskalResult


class TestKruskalResult:
    def test_edges_count_property(self, triangle):
        nodes, edges = triangle
        result = kruskal(nodes, edges)
        assert result.edges_count == len(result.mst_edges)

    def test_repr_contem_custo_e_status(self, triangle):
        nodes, edges = triangle
        result = kruskal(nodes, edges)
        r = repr(result)
        assert "conectado" in r or "desconectado" in r
>>>>>>> origin/main
