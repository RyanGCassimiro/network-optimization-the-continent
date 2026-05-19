"""
pyvis_graph.py - Visualização interativa da rede de fibra óptica
Responsável: Ryan Cassimiro
Projeto: Tema D - Otimização de Rede de Fibra Óptica (MST)

Gera arquivos HTML interativos com pyvis, destacando a MST sobre a rede completa.
"""

import os
from pyvis.network import Network
from src.models.graph import FiberGraph


# -----------------------------------------------------------------------
# Paleta de cores do projeto
# -----------------------------------------------------------------------
COLOR_DEFAULT_NODE = "#4A90D9"       # Azul — bairro comum
COLOR_MST_NODE     = "#27AE60"       # Verde — bairro na MST
COLOR_START_NODE   = "#E74C3C"       # Vermelho — nó inicial
COLOR_DEFAULT_EDGE = "#AAAAAA"       # Cinza — aresta normal
COLOR_MST_EDGE     = "#F39C12"       # Laranja — aresta da MST


def build_network(
    graph: FiberGraph,
    mst_result: dict | None = None,
    start_node: str | None = None,
    height: str = "700px",
    width: str = "100%",
    notebook: bool = False,
) -> Network:
    """
    Constrói um objeto Network (pyvis) a partir do FiberGraph.

    Args:
        graph: Rede de fibra óptica.
        mst_result: Resultado de prim_mst() ou kruskal_mst(). Se fornecido,
                    as arestas da MST serão destacadas em laranja/verde.
        start_node: Nó inicial (pintado em vermelho).
        height: Altura do iframe HTML.
        width: Largura do iframe HTML.
        notebook: True se for renderizar dentro de Jupyter.

    Returns:
        Objeto Network configurado, pronto para exportar.
    """
    net = Network(
        height=height,
        width=width,
        bgcolor="#1A1A2E",          # Fundo escuro para contraste
        font_color="#FFFFFF",
        notebook=notebook,
        directed=False,
    )

    # Física: spring layout, mais legível para grafos esparsos
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.08
        },
        "stabilization": { "iterations": 200 }
      },
      "edges": {
        "smooth": { "type": "continuous" }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    # Conjunto de arestas MST para lookup rápido
    mst_edge_set: set[frozenset] = set()
    mst_node_set: set[str] = set()
    if mst_result:
        for u, v, _ in mst_result.get("edges", []):
            mst_edge_set.add(frozenset({u, v}))
            mst_node_set.update([u, v])

    # -----------------------------------------------------------------------
    # Adiciona nós
    # -----------------------------------------------------------------------
    for node in graph.get_nodes():
        attrs = graph.get_node_attrs(node)

        if node == start_node:
            color = COLOR_START_NODE
            shape = "star"
            size = 22
            title = f"<b>⭐ {node}</b> (nó inicial)<br>" + _format_attrs(attrs)
        elif node in mst_node_set:
            color = COLOR_MST_NODE
            shape = "dot"
            size = 18
            title = f"<b>🟢 {node}</b><br>" + _format_attrs(attrs)
        else:
            color = COLOR_DEFAULT_NODE
            shape = "dot"
            size = 14
            title = f"<b>{node}</b><br>" + _format_attrs(attrs)

        net.add_node(
            node,
            label=node,
            color=color,
            shape=shape,
            size=size,
            title=title,
            font={"size": 12, "color": "#FFFFFF"},
        )

    # -----------------------------------------------------------------------
    # Adiciona arestas
    # -----------------------------------------------------------------------
    for u, v, weight in graph.get_edges():
        is_mst = frozenset({u, v}) in mst_edge_set

        if is_mst:
            color = COLOR_MST_EDGE
            width = 4
            dashes = False
            label = f"{weight:.1f} km"
            title = f"<b>MST ✔</b><br>{u} ↔ {v}<br>Custo: {weight:.2f}"
        else:
            color = COLOR_DEFAULT_EDGE
            width = 1
            dashes = True
            label = f"{weight:.1f}"
            title = f"{u} ↔ {v}<br>Custo: {weight:.2f}"

        net.add_edge(
            u, v,
            weight=weight,
            label=label,
            title=title,
            color=color,
            width=width,
            dashes=dashes,
            font={"size": 10, "color": "#FFFFFF", "strokeWidth": 2, "strokeColor": "#000000"},
        )

    return net


def render_graph_html(
    graph: FiberGraph,
    output_path: str = "fiber_network.html",
    mst_result: dict | None = None,
    start_node: str | None = None,
) -> str:
    """
    Gera o arquivo HTML interativo da rede de fibra óptica.

    Args:
        graph: Rede de fibra óptica.
        output_path: Caminho do arquivo HTML gerado.
        mst_result: Resultado do algoritmo MST (Prim ou Kruskal).
        start_node: Nó inicial da MST.

    Returns:
        Caminho absoluto do arquivo HTML gerado.
    """
    net = build_network(graph, mst_result=mst_result, start_node=start_node)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    net.save_graph(output_path)

    return os.path.abspath(output_path)


def render_mst_only_html(
    graph: FiberGraph,
    mst_result: dict,
    output_path: str = "mst_only.html",
    start_node: str | None = None,
) -> str:
    """
    Gera um HTML mostrando APENAS a MST (sem as arestas que não fazem parte dela).

    Args:
        graph: Rede de fibra óptica original (para pegar atributos dos nós).
        mst_result: Resultado do algoritmo MST.
        output_path: Caminho do arquivo HTML.
        start_node: Nó inicial (destacado em vermelho).

    Returns:
        Caminho absoluto do arquivo HTML gerado.
    """
    mst_graph = FiberGraph()

    # Copia os nós envolvidos na MST
    mst_node_set = set()
    for u, v, _ in mst_result.get("edges", []):
        mst_node_set.update([u, v])

    for node in mst_node_set:
        try:
            attrs = graph.get_node_attrs(node)
        except KeyError:
            attrs = {}
        mst_graph.add_node(node, **attrs)

    # Adiciona apenas as arestas da MST
    for u, v, weight in mst_result.get("edges", []):
        mst_graph.add_edge(u, v, weight)

    net = build_network(
        mst_graph,
        mst_result=mst_result,
        start_node=start_node,
    )
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    net.save_graph(output_path)
    return os.path.abspath(output_path)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _format_attrs(attrs: dict) -> str:
    """Formata atributos de nó para exibição no tooltip HTML."""
    if not attrs:
        return ""
    lines = []
    for k, v in attrs.items():
        lines.append(f"{k}: {v}")
    return "<br>".join(lines)