from collections import Counter, defaultdict

import pandas as pd

from src.algorithms.mst_solver import MSTSolver, SolverResult

HUB_CRITICAL_THRESHOLD = 3


def summary(result: SolverResult, solver: MSTSolver) -> pd.DataFrame:
    """Painel resumo com as principais métricas da MST."""
    rows = [
        ("Algoritmo", result.algorithm.capitalize()),
        ("Reinos conectados", result.nodes_count),
        ("Rotas na MST", result.edges_in_mst),
        ("Rotas disponíveis", result.edges_available),
        ("Custo total da MST (k coroas)", f"{result.total_cost:,.0f}"),
        ("Custo sem otimização (k coroas)", f"{solver.total_network_cost:,.0f}"),
        ("Economia (k coroas)", f"{result.savings:,.0f}"),
        ("Economia (%)", f"{result.savings_pct:.1f}%"),
        ("Rede conectada", "Sim" if result.is_connected else "Não"),
    ]
    return pd.DataFrame(rows, columns=["Métrica", "Valor"])


def edges_table(result: SolverResult, solver: MSTSolver) -> pd.DataFrame:
    """Tabela detalhada de cada aresta na MST."""
    neighborhoods = solver.neighborhoods
    rows = []
    for e in result.mst_edges:
        rows.append({
            "Origem": neighborhoods[e.source].name,
            "Destino": neighborhoods[e.target].name,
            "Terreno": e.metadata["terrain"].capitalize(),
            "Distância (km)": e.metadata["distance_km"],
            "Custo (k coroas)": e.weight,
            "Custo/km": round(e.weight / e.metadata["distance_km"], 2) if e.metadata["distance_km"] > 0 else 0.0,
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Custo (k coroas)").reset_index(drop=True)


def cost_by_terrain(result: SolverResult) -> pd.DataFrame:
    """Custo e contagem de arestas agrupados por tipo de terreno."""
    groups: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_cost": 0.0, "total_km": 0})
    for e in result.mst_edges:
        t = e.metadata["terrain"].capitalize()
        groups[t]["count"] += 1
        groups[t]["total_cost"] += e.weight
        groups[t]["total_km"] += e.metadata["distance_km"]

    rows = []
    for terrain, g in sorted(groups.items()):
        rows.append({
            "Terreno": terrain,
            "Rotas": g["count"],
            "Distância total (km)": g["total_km"],
            "Custo total (k coroas)": g["total_cost"],
            "% do custo MST": round(g["total_cost"] / result.total_cost * 100, 1) if result.total_cost > 0 else 0.0,
        })
    return pd.DataFrame(rows).sort_values("Custo total (k coroas)", ascending=False).reset_index(drop=True)


def node_degree(result: SolverResult, solver: MSTSolver) -> pd.DataFrame:
    """Grau de cada reino na MST — reinos com maior grau são hubs críticos."""
    degree: Counter = Counter()
    for e in result.mst_edges:
        degree[e.source] += 1
        degree[e.target] += 1

    neighborhoods = solver.neighborhoods
    rows = [
        {
            "Reino": neighborhoods[node_id].name,
            "Região": neighborhoods[node_id].region.replace("_", " ").capitalize(),
            "Conexões na MST": count,
            "Hub crítico": "Sim" if count >= HUB_CRITICAL_THRESHOLD else "Não",
        }
        for node_id, count in degree.most_common()
    ]
    return pd.DataFrame(rows)


def regional_cost(result: SolverResult, solver: MSTSolver) -> pd.DataFrame:
    """Custo das arestas MST agrupado pela região de origem."""
    neighborhoods = solver.neighborhoods
    groups: dict[str, dict] = defaultdict(lambda: {"count": 0, "cost": 0.0})

    for e in result.mst_edges:
        region = neighborhoods[e.source].region.replace("_", " ").capitalize()
        groups[region]["count"] += 1
        groups[region]["cost"] += e.weight

    rows = [
        {
            "Região": region,
            "Rotas na MST": g["count"],
            "Custo (k coroas)": g["cost"],
            "% do custo MST": round(g["cost"] / result.total_cost * 100, 1) if result.total_cost > 0 else 0.0,
        }
        for region, g in sorted(groups.items())
    ]
    return pd.DataFrame(rows).sort_values("Custo (k coroas)", ascending=False).reset_index(drop=True)


def top_edges(result: SolverResult, solver: MSTSolver, n: int = 5) -> dict[str, pd.DataFrame]:
    """As N rotas mais caras e mais baratas da MST."""
    df = edges_table(result, solver)
    return {
        "mais_caras": df.nlargest(n, "Custo (k coroas)").reset_index(drop=True),
        "mais_baratas": df.nsmallest(n, "Custo (k coroas)").reset_index(drop=True),
    }


def compare_algorithms(solver: MSTSolver) -> pd.DataFrame | None:
    """
    Compara Kruskal e Prim lado a lado.
    Retorna None se Prim ainda não estiver implementado.
    """
    try:
        results = solver.compare()
    except NotImplementedError:
        return None

    rows = []
    for algo, r in results.items():
        rows.append({
            "Algoritmo": algo.capitalize(),
            "Custo MST (k coroas)": r.total_cost,
            "Rotas usadas": r.edges_in_mst,
            "Economia (k coroas)": r.savings,
            "Economia (%)": round(r.savings_pct, 1),
            "Conectado": "Sim" if r.is_connected else "Não",
        })
    return pd.DataFrame(rows)
