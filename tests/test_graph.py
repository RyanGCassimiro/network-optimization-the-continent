"""
test_graph.py - Testes unitários para FiberGraph (graph.py)
Responsável: Ryan Cassimiro
Projeto: Tema D - Otimização de Rede de Fibra Óptica (MST)

Execução:
    pytest tests/test_graph.py -v
    pytest tests/test_graph.py -v --cov=src
"""

import pytest
from src.models.graph import FiberGraph


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def empty_graph():
    """Grafo vazio."""
    return FiberGraph()


@pytest.fixture
def small_graph():
    """Grafo pequeno com 4 bairros e 5 arestas (conexo)."""
    g = FiberGraph()
    for bairro in ["Pajuçara", "Ponta Verde", "Jatiúca", "Cruz das Almas"]:
        g.add_node(bairro)
    g.add_edge("Pajuçara", "Ponta Verde", weight=2.5)
    g.add_edge("Pajuçara", "Jatiúca", weight=4.0)
    g.add_edge("Ponta Verde", "Jatiúca", weight=1.8)
    g.add_edge("Jatiúca", "Cruz das Almas", weight=3.2)
    g.add_edge("Pajuçara", "Cruz das Almas", weight=6.1)
    return g


@pytest.fixture
def disconnected_graph():
    """Grafo com dois componentes desconectados."""
    g = FiberGraph()
    g.add_node("A")
    g.add_node("B")
    g.add_node("C")
    g.add_edge("A", "B", weight=1.0)
    # C está isolado
    return g


# ========================================================================
# Testes — Nós
# ========================================================================

class TestNodes:
    def test_add_single_node(self, empty_graph):
        empty_graph.add_node("Pajuçara")
        assert empty_graph.has_node("Pajuçara")
        assert empty_graph.get_node_count() == 1

    def test_add_multiple_nodes(self, empty_graph):
        bairros = ["Pajuçara", "Ponta Verde", "Jatiúca"]
        for b in bairros:
            empty_graph.add_node(b)
        assert empty_graph.get_node_count() == 3
        assert set(empty_graph.get_nodes()) == set(bairros)

    def test_add_node_with_attributes(self, empty_graph):
        empty_graph.add_node("Pajuçara", population=45000, lat=-9.666, lon=-35.730)
        attrs = empty_graph.get_node_attrs("Pajuçara")
        assert attrs["population"] == 45000
        assert attrs["lat"] == pytest.approx(-9.666)

    def test_add_duplicate_node_updates_attrs(self, empty_graph):
        """Adicionar nó duplicado deve sobrescrever atributos (comportamento networkx)."""
        empty_graph.add_node("Pajuçara", population=1000)
        empty_graph.add_node("Pajuçara", population=2000)
        assert empty_graph.get_node_attrs("Pajuçara")["population"] == 2000
        assert empty_graph.get_node_count() == 1

    def test_add_node_empty_id_raises(self, empty_graph):
        with pytest.raises(ValueError, match="string não-vazia"):
            empty_graph.add_node("")

    def test_add_node_non_string_raises(self, empty_graph):
        with pytest.raises(ValueError):
            empty_graph.add_node(123)  # type: ignore

    def test_remove_node(self, small_graph):
        small_graph.remove_node("Pajuçara")
        assert not small_graph.has_node("Pajuçara")
        assert small_graph.get_node_count() == 3

    def test_remove_node_removes_edges(self, small_graph):
        """Remover um nó deve remover as arestas associadas."""
        small_graph.remove_node("Pajuçara")
        assert not small_graph.has_edge("Pajuçara", "Ponta Verde")
        assert not small_graph.has_edge("Pajuçara", "Jatiúca")

    def test_remove_nonexistent_node_raises(self, empty_graph):
        with pytest.raises(KeyError):
            empty_graph.remove_node("Inexistente")

    def test_get_node_attrs_nonexistent_raises(self, empty_graph):
        with pytest.raises(KeyError):
            empty_graph.get_node_attrs("Inexistente")

    def test_has_node_false(self, empty_graph):
        assert not empty_graph.has_node("Qualquer")


# ========================================================================
# Testes — Arestas
# ========================================================================

class TestEdges:
    def test_add_edge(self, empty_graph):
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        empty_graph.add_edge("A", "B", weight=3.0)
        assert empty_graph.has_edge("A", "B")
        assert empty_graph.has_edge("B", "A")   # não-direcionado

    def test_edge_weight(self, small_graph):
        assert small_graph.get_edge_weight("Pajuçara", "Ponta Verde") == pytest.approx(2.5)

    def test_edge_weight_symmetric(self, small_graph):
        w1 = small_graph.get_edge_weight("Pajuçara", "Ponta Verde")
        w2 = small_graph.get_edge_weight("Ponta Verde", "Pajuçara")
        assert w1 == pytest.approx(w2)

    def test_add_edge_zero_weight(self, empty_graph):
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        empty_graph.add_edge("A", "B", weight=0.0)
        assert empty_graph.get_edge_weight("A", "B") == pytest.approx(0.0)

    def test_add_edge_negative_weight_raises(self, empty_graph):
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        with pytest.raises(ValueError, match="Peso inválido"):
            empty_graph.add_edge("A", "B", weight=-1.0)

    def test_add_selfloop_raises(self, empty_graph):
        empty_graph.add_node("A")
        with pytest.raises(ValueError, match="laços"):
            empty_graph.add_edge("A", "A", weight=1.0)

    def test_add_edge_missing_node_raises(self, empty_graph):
        empty_graph.add_node("A")
        with pytest.raises(KeyError):
            empty_graph.add_edge("A", "INEXISTENTE", weight=1.0)

    def test_remove_edge(self, small_graph):
        small_graph.remove_edge("Pajuçara", "Ponta Verde")
        assert not small_graph.has_edge("Pajuçara", "Ponta Verde")

    def test_remove_nonexistent_edge_raises(self, empty_graph):
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        with pytest.raises(KeyError):
            empty_graph.remove_edge("A", "B")

    def test_get_edges_format(self, small_graph):
        edges = small_graph.get_edges()
        assert isinstance(edges, list)
        for item in edges:
            assert len(item) == 3    # (u, v, weight)
            assert isinstance(item[2], (int, float))

    def test_get_edge_count(self, small_graph):
        assert small_graph.get_edge_count() == 5

    def test_get_neighbors(self, small_graph):
        neighbors = small_graph.get_neighbors("Jatiúca")
        assert set(neighbors) == {"Pajuçara", "Ponta Verde", "Cruz das Almas"}

    def test_get_neighbors_nonexistent_raises(self, empty_graph):
        with pytest.raises(KeyError):
            empty_graph.get_neighbors("Inexistente")

    def test_get_edge_weight_nonexistent_raises(self, empty_graph):
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        with pytest.raises(KeyError):
            empty_graph.get_edge_weight("A", "B")


# ========================================================================
# Testes — Propriedades estruturais
# ========================================================================

class TestStructure:
    def test_is_connected_true(self, small_graph):
        assert small_graph.is_connected() is True

    def test_is_connected_false(self, disconnected_graph):
        assert disconnected_graph.is_connected() is False

    def test_is_connected_empty_graph(self, empty_graph):
        assert empty_graph.is_connected() is True

    def test_is_connected_single_node(self, empty_graph):
        empty_graph.add_node("Solo")
        assert empty_graph.is_connected() is True

    def test_get_total_weight(self, small_graph):
        expected = 2.5 + 4.0 + 1.8 + 3.2 + 6.1
        assert small_graph.get_total_weight() == pytest.approx(expected)

    def test_get_total_weight_empty(self, empty_graph):
        assert empty_graph.get_total_weight() == pytest.approx(0.0)

    def test_get_density(self, small_graph):
        density = small_graph.get_density()
        assert 0.0 <= density <= 1.0

    def test_get_density_empty(self, empty_graph):
        assert empty_graph.get_density() == pytest.approx(0.0)

    def test_get_degree(self, small_graph):
        # Pajuçara conecta a: Ponta Verde, Jatiúca, Cruz das Almas → grau 3
        assert small_graph.get_degree("Pajuçara") == 3

    def test_get_degree_nonexistent_raises(self, empty_graph):
        with pytest.raises(KeyError):
            empty_graph.get_degree("Inexistente")

    def test_clear(self, small_graph):
        small_graph.clear()
        assert small_graph.get_node_count() == 0
        assert small_graph.get_edge_count() == 0

    def test_repr(self, small_graph):
        r = repr(small_graph)
        assert "FiberGraph" in r
        assert "nodes=4" in r
        assert "edges=5" in r

    def test_summary(self, small_graph):
        s = small_graph.summary()
        assert "Bairros" in s
        assert "Conexões" in s
        assert "Custo total" in s
        expected_weight = 2.5 + 4.0 + 1.8 + 3.2 + 6.1
        assert f"{expected_weight:.2f}" in s
        assert "4" in s   # 4 nós
        assert "5" in s   # 5 arestas

    def test_get_networkx_graph(self, small_graph):
        import networkx as nx
        g = small_graph.get_networkx_graph()
        assert isinstance(g, nx.Graph)
        assert g.number_of_nodes() == 4


# ========================================================================
# Testes — Cenários de integração simples
# ========================================================================

class TestIntegrationScenarios:
    def test_build_maceio_subgraph(self):
        """Cria um subgrafo baseado em bairros reais de Maceió e verifica conectividade."""
        g = FiberGraph()
        bairros = [
            "Pajuçara", "Ponta Verde", "Jatiúca", "Cruz das Almas",
            "Farol", "Centro", "Poço", "Pinheiro"
        ]
        for b in bairros:
            g.add_node(b)

        conexoes = [
            ("Pajuçara", "Ponta Verde", 1.2),
            ("Ponta Verde", "Jatiúca", 0.9),
            ("Jatiúca", "Cruz das Almas", 2.1),
            ("Cruz das Almas", "Farol", 1.5),
            ("Farol", "Centro", 2.3),
            ("Centro", "Poço", 1.0),
            ("Poço", "Pinheiro", 3.4),
            ("Pinheiro", "Pajuçara", 4.0),
        ]
        for u, v, w in conexoes:
            g.add_edge(u, v, weight=w)

        assert g.is_connected()
        assert g.get_node_count() == 8
        assert g.get_edge_count() == 8

    def test_add_remove_preserves_consistency(self, small_graph):
        """Adicionar e remover nó volta ao estado original."""
        original_count = small_graph.get_node_count()
        small_graph.add_node("Temp")
        small_graph.add_edge("Temp", "Pajuçara", weight=1.0)
        small_graph.remove_node("Temp")
        assert small_graph.get_node_count() == original_count

    def test_overwrite_edge_weight(self, empty_graph):
        """Adicionar aresta existente sobrescreve o peso (comportamento networkx)."""
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        empty_graph.add_edge("A", "B", weight=5.0)
        empty_graph.add_edge("A", "B", weight=2.0)
        assert empty_graph.get_edge_weight("A", "B") == pytest.approx(2.0)
        assert empty_graph.get_edge_count() == 1