"""
Testes dos algoritmos MST, data_loader, metrics e pipeline de integração.
Responsável: Wanessa
"""
import json
import pytest
from pathlib import Path

from src.algorithms.kruskal import Edge, KruskalResult, UnionFind, kruskal
from src.models.neighborhood import Coords, Neighborhood

DATASET = Path(__file__).parent.parent / "src" / "data" / "the_continent_kingdoms.json"



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
    @pytest.mark.parametrize("fixture_name", ["triangle", "square"])
    def test_mst_tem_n_menos_1_arestas(self, request, fixture_name):
        nodes, edges = request.getfixturevalue(fixture_name)
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


# ========================================================================
# DataLoader
# ========================================================================

class TestDataLoader:
    def test_load_dataset_real_retorna_listas(self):
        from src.utils.data_loader import load
        neighborhoods, connections = load(DATASET)
        assert isinstance(neighborhoods, list)
        assert isinstance(connections, list)
        assert len(neighborhoods) > 0
        assert len(connections) > 0

    def test_load_neighborhoods_sao_neighborhood(self):
        from src.utils.data_loader import load
        from src.models.neighborhood import Neighborhood
        neighborhoods, _ = load(DATASET)
        assert all(isinstance(n, Neighborhood) for n in neighborhoods)

    def test_load_connections_tem_campos_obrigatorios(self):
        from src.utils.data_loader import load
        _, connections = load(DATASET)
        required = {"id", "source", "target", "distance_km", "terrain", "cost", "terrain_multiplier"}
        for c in connections:
            assert required <= c.keys(), f"Conexão {c.get('id')} faltam campos: {required - c.keys()}"

    def test_load_arquivo_inexistente_levanta_filenotfounderror(self, tmp_path):
        from src.utils.data_loader import load
        with pytest.raises(FileNotFoundError):
            load(tmp_path / "nao_existe.json")

    def test_load_json_invalido_levanta_valueerror(self, tmp_path):
        from src.utils.data_loader import load
        bad = tmp_path / "bad.json"
        bad.write_text("{ isso nao é json }", encoding="utf-8")
        with pytest.raises(ValueError, match="JSON inválido"):
            load(bad)

    def test_load_campo_kingdoms_ausente_levanta_valueerror(self, tmp_path):
        from src.utils.data_loader import load
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"connections": []}), encoding="utf-8")
        with pytest.raises(ValueError, match="kingdoms"):
            load(bad)

    def test_load_campo_connections_ausente_levanta_valueerror(self, tmp_path):
        from src.utils.data_loader import load
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"kingdoms": []}), encoding="utf-8")
        with pytest.raises(ValueError, match="connections"):
            load(bad)

    def test_load_reino_sem_campo_obrigatorio_levanta_valueerror(self, tmp_path):
        from src.utils.data_loader import load
        bad = tmp_path / "bad.json"
        data = {
            "kingdoms": [{"id": "x", "name": "X"}],  # faltam region e coords
            "connections": [],
        }
        bad.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError):
            load(bad)

    def test_load_id_duplicado_levanta_valueerror(self, tmp_path):
        from src.utils.data_loader import load
        bad = tmp_path / "bad.json"
        reino = {"id": "dup", "name": "X", "region": "norte", "coords": {"x": 0, "y": 0}}
        data = {"kingdoms": [reino, reino], "connections": []}
        bad.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="duplicado"):
            load(bad)

    def test_load_conexao_com_source_inexistente_levanta_valueerror(self, tmp_path):
        from src.utils.data_loader import load
        bad = tmp_path / "bad.json"
        data = {
            "kingdoms": [{"id": "A", "name": "A", "region": "norte", "coords": {"x": 0, "y": 0}}],
            "connections": [{"id": "c1", "source": "INEXISTENTE", "target": "A",
                             "distance_km": 1, "terrain": "planicie", "cost": 1, "terrain_multiplier": 1.0}],
        }
        bad.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError):
            load(bad)

    def test_metadata_retorna_dict(self):
        from src.utils.data_loader import metadata
        meta = metadata(DATASET)
        assert isinstance(meta, dict)
        assert "name" in meta


# ========================================================================
# Metrics
# ========================================================================

@pytest.fixture
def solver_result_real():
    """Carrega dataset real e executa Kruskal — base para testes de métricas."""
    from src.utils.data_loader import load
    from src.algorithms.mst_solver import MSTSolver
    neighborhoods, connections = load(DATASET)
    solver = MSTSolver(neighborhoods, connections)
    return solver, solver.solve(algorithm="kruskal")


class TestMetrics:
    def test_summary_retorna_dataframe(self, solver_result_real):
        from src.visualization.metrics import summary
        import pandas as pd
        solver, result = solver_result_real
        df = summary(result, solver)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["Métrica", "Valor"]

    def test_summary_contem_algoritmo(self, solver_result_real):
        from src.visualization.metrics import summary
        solver, result = solver_result_real
        df = summary(result, solver)
        assert "Kruskal" in df["Valor"].values

    def test_edges_table_retorna_dataframe(self, solver_result_real):
        from src.visualization.metrics import edges_table
        import pandas as pd
        solver, result = solver_result_real
        df = edges_table(result, solver)
        assert isinstance(df, pd.DataFrame)
        assert "Custo (k coroas)" in df.columns

    def test_edges_table_custo_por_km_sem_divisao_por_zero(self, solver_result_real):
        from src.visualization.metrics import edges_table
        solver, result = solver_result_real
        df = edges_table(result, solver)
        assert df["Custo/km"].notna().all()
        assert (df["Custo/km"] >= 0).all()

    def test_cost_by_terrain_retorna_dataframe(self, solver_result_real):
        from src.visualization.metrics import cost_by_terrain
        import pandas as pd
        solver, result = solver_result_real
        df = cost_by_terrain(result)
        assert isinstance(df, pd.DataFrame)
        assert "Terreno" in df.columns
        assert "% do custo MST" in df.columns

    def test_cost_by_terrain_percentual_valido(self, solver_result_real):
        from src.visualization.metrics import cost_by_terrain
        solver, result = solver_result_real
        df = cost_by_terrain(result)
        assert (df["% do custo MST"] >= 0).all()
        assert (df["% do custo MST"] <= 100).all()

    def test_node_degree_retorna_dataframe(self, solver_result_real):
        from src.visualization.metrics import node_degree
        import pandas as pd
        solver, result = solver_result_real
        df = node_degree(result, solver)
        assert isinstance(df, pd.DataFrame)
        assert "Conexões na MST" in df.columns
        assert "Hub crítico" in df.columns

    def test_regional_cost_retorna_dataframe(self, solver_result_real):
        from src.visualization.metrics import regional_cost
        import pandas as pd
        solver, result = solver_result_real
        df = regional_cost(result, solver)
        assert isinstance(df, pd.DataFrame)
        assert "% do custo MST" in df.columns

    def test_regional_cost_percentual_valido(self, solver_result_real):
        from src.visualization.metrics import regional_cost
        solver, result = solver_result_real
        df = regional_cost(result, solver)
        assert (df["% do custo MST"] >= 0).all()
        assert (df["% do custo MST"] <= 100).all()

    def test_top_edges_retorna_mais_caras_e_baratas(self, solver_result_real):
        from src.visualization.metrics import top_edges
        solver, result = solver_result_real
        tops = top_edges(result, solver, n=3)
        assert "mais_caras" in tops and "mais_baratas" in tops
        assert len(tops["mais_caras"]) <= 3
        assert len(tops["mais_baratas"]) <= 3

    def test_compare_algorithms_retorna_dataframe_com_prim(self, solver_result_real):
        from src.visualization.metrics import compare_algorithms
        import pandas as pd
        solver, _ = solver_result_real
        df = compare_algorithms(solver)
        assert isinstance(df, pd.DataFrame)
        algos = df["Algoritmo"].str.lower().tolist()
        assert "kruskal" in algos
        assert "prim" in algos


# ========================================================================
# Pipeline completo (integração real)
# ========================================================================

class TestPipelineCompleto:
    def test_load_e_solve_kruskal(self):
        from src.utils.data_loader import load
        from src.algorithms.mst_solver import MSTSolver
        neighborhoods, connections = load(DATASET)
        solver = MSTSolver(neighborhoods, connections)
        result = solver.solve(algorithm="kruskal")
        assert result.is_connected is True
        assert result.total_cost > 0
        assert result.edges_in_mst == result.nodes_count - 1

    def test_load_e_solve_prim(self):
        from src.utils.data_loader import load
        from src.algorithms.mst_solver import MSTSolver
        neighborhoods, connections = load(DATASET)
        solver = MSTSolver(neighborhoods, connections)
        result = solver.solve(algorithm="prim")
        assert result.is_connected is True
        assert result.total_cost > 0
        assert result.edges_in_mst == result.nodes_count - 1

    def test_kruskal_e_prim_mesmo_custo_dataset_real(self):
        from src.utils.data_loader import load
        from src.algorithms.mst_solver import MSTSolver
        neighborhoods, connections = load(DATASET)
        solver = MSTSolver(neighborhoods, connections)
        results = solver.compare()
        assert results["kruskal"].total_cost == pytest.approx(results["prim"].total_cost, rel=1e-3)

    def test_pipeline_completo_load_solve_metrics(self):
        from src.utils.data_loader import load
        from src.algorithms.mst_solver import MSTSolver
        from src.visualization import metrics
        neighborhoods, connections = load(DATASET)
        solver = MSTSolver(neighborhoods, connections)
        result = solver.solve()
        assert metrics.summary(result, solver) is not None
        assert metrics.edges_table(result, solver) is not None
        assert metrics.cost_by_terrain(result) is not None
        assert metrics.node_degree(result, solver) is not None
        assert metrics.regional_cost(result, solver) is not None

    def test_economia_menor_que_custo_total(self):
        from src.utils.data_loader import load
        from src.algorithms.mst_solver import MSTSolver
        neighborhoods, connections = load(DATASET)
        solver = MSTSolver(neighborhoods, connections)
        result = solver.solve()
        assert result.savings <= solver.total_network_cost
        assert 0 <= result.savings_pct <= 100
