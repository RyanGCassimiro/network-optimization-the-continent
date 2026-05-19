"""
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