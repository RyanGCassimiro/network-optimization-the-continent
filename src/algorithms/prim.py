"""
prim.py - Algoritmo de Prim para Árvore Geradora Mínima (MST)
Responsável: Ryan Cassimiro
Projeto: Tema D - Otimização de Rede de Fibra Óptica (MST)

Complexidade: O((V + E) log V) com heap de prioridade.
"""

import heapq
from src.models.graph import FiberGraph


def prim_mst(graph: FiberGraph, start_node: str | None = None) -> dict:
    """
    Executa o algoritmo de Prim e retorna a Árvore Geradora Mínima (MST).

    O algoritmo de Prim cresce a MST a partir de um nó inicial, adicionando
    sempre a aresta de menor peso que conecta um nó já na árvore a um nó ainda
    fora dela.

    Args:
        graph: Instância de FiberGraph representando a rede.
        start_node: Bairro inicial. Se None, usa o primeiro nó disponível.

    Returns:
        Dicionário com:
          - "edges": lista de (u, v, weight) — arestas da MST
          - "total_weight": custo total da MST
          - "nodes_visited": ordem de visita dos nós
          - "algorithm": "Prim"

    Raises:
        ValueError: Se o grafo estiver vazio ou não for conexo.
        KeyError: Se o start_node não existir no grafo.
    """
    nodes = graph.get_nodes()

    if not nodes:
        raise ValueError("O grafo está vazio. Adicione bairros antes de executar Prim.")

    if not graph.is_connected():
        raise ValueError(
            "O grafo não é conexo. Prim requer que todos os bairros estejam conectados."
        )

    # Define nó inicial
    if start_node is None:
        start_node = nodes[0]
    elif not graph.has_node(start_node):
        raise KeyError(f"Bairro inicial '{start_node}' não encontrado no grafo.")

    nx_graph = graph.get_networkx_graph()

    # Estruturas do Prim
    in_mst = set()          # Nós já incluídos na MST
    mst_edges = []          # Arestas selecionadas para a MST
    nodes_visited = []      # Ordem de visita

    # Min-heap: (peso, nó_origem, nó_destino)
    min_heap = [(0.0, start_node, None)]

    while min_heap and len(in_mst) < graph.get_node_count():
        weight, current, parent = heapq.heappop(min_heap)

        if current in in_mst:
            continue

        in_mst.add(current)
        nodes_visited.append(current)

        # Registra a aresta que trouxe esse nó (exceto o nó inicial)
        if parent is not None:
            mst_edges.append((parent, current, weight))

        # Explora vizinhos ainda fora da MST
        for neighbor in nx_graph.neighbors(current):
            if neighbor not in in_mst:
                edge_weight = nx_graph[current][neighbor]["weight"]
                heapq.heappush(min_heap, (edge_weight, neighbor, current))

    total_weight = sum(w for _, _, w in mst_edges)

    return {
        "edges": mst_edges,
        "total_weight": round(total_weight, 4),
        "nodes_visited": nodes_visited,
        "algorithm": "Prim",
    }


def prim_mst_summary(result: dict) -> str:
    """
    Formata o resultado do Prim em texto legível.

    Args:
        result: Dicionário retornado por prim_mst().

    Returns:
        String formatada com as arestas e custo total da MST.
    """
    lines = [
        "=== Resultado - Algoritmo de Prim ===",
        f"  Custo total da MST: {result['total_weight']:.2f}",
        f"  Arestas na MST:     {len(result['edges'])}",
        "",
        "  Conexões selecionadas:",
    ]
    for u, v, w in sorted(result["edges"], key=lambda x: x[2]):
        lines.append(f"    {u} <-> {v}  [custo: {w:.2f}]")

    lines += [
        "",
        "  Ordem de visita dos bairros:",
        "    " + " -> ".join(result["nodes_visited"]),
    ]
    return "\n".join(lines)