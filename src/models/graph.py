"""
graph.py - Estrutura de dados do grafo para o Otimizador de Rede de Fibra Óptica
Responsável: Ryan Cassimiro
Projeto: Tema D - Otimização de Rede de Fibra Óptica (MST)
"""

import networkx as nx


class FiberGraph:
    """
    Representa a rede de fibra óptica como um grafo ponderado não-direcionado.
    Cada nó é um bairro e cada aresta é uma conexão com custo (distância/custo em km ou R$).
    """

    def __init__(self):
        self._graph = nx.Graph()

    # ------------------------------------------------------------------
    # Manipulação de nós (bairros)
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, **attrs) -> None:
        """
        Adiciona um bairro ao grafo.

        Args:
            node_id: Identificador único do bairro (ex: "Pajuçara").
            **attrs: Atributos extras, ex: population=50000, lat=-9.66, lon=-35.73
        """
        if not node_id or not isinstance(node_id, str):
            raise ValueError("node_id deve ser uma string não-vazia.")
        self._graph.add_node(node_id, **attrs)

    def remove_node(self, node_id: str) -> None:
        """Remove um bairro e todas as conexões associadas."""
        if node_id not in self._graph:
            raise KeyError(f"Bairro '{node_id}' não encontrado no grafo.")
        self._graph.remove_node(node_id)

    def has_node(self, node_id: str) -> bool:
        """Verifica se um bairro existe no grafo."""
        return self._graph.has_node(node_id)

    def get_nodes(self) -> list[str]:
        """Retorna lista de todos os bairros."""
        return list(self._graph.nodes())

    def get_node_count(self) -> int:
        """Retorna o número de bairros."""
        return self._graph.number_of_nodes()

    def get_node_attrs(self, node_id: str) -> dict:
        """Retorna os atributos de um bairro."""
        if node_id not in self._graph:
            raise KeyError(f"Bairro '{node_id}' não encontrado.")
        return dict(self._graph.nodes[node_id])

    # ------------------------------------------------------------------
    # Manipulação de arestas (conexões de fibra)
    # ------------------------------------------------------------------

    def add_edge(self, u: str, v: str, weight: float, **attrs) -> None:
        """
        Adiciona uma conexão de fibra entre dois bairros.

        Args:
            u: Bairro de origem.
            v: Bairro de destino.
            weight: Custo da conexão (km ou R$). Deve ser >= 0.
            **attrs: Atributos extras, ex: fiber_type="monomodo"
        """
        if u == v:
            raise ValueError("Não é permitido adicionar laços (self-loops).")
        if weight < 0:
            raise ValueError(f"Peso inválido ({weight}). Deve ser >= 0.")
        if not self._graph.has_node(u):
            raise KeyError(f"Bairro '{u}' não existe. Adicione-o antes da aresta.")
        if not self._graph.has_node(v):
            raise KeyError(f"Bairro '{v}' não existe. Adicione-o antes da aresta.")
        self._graph.add_edge(u, v, weight=weight, **attrs)

    def remove_edge(self, u: str, v: str) -> None:
        """Remove a conexão entre dois bairros."""
        if not self._graph.has_edge(u, v):
            raise KeyError(f"Aresta '{u}' <-> '{v}' não encontrada.")
        self._graph.remove_edge(u, v)

    def has_edge(self, u: str, v: str) -> bool:
        """Verifica se existe conexão entre dois bairros."""
        return self._graph.has_edge(u, v)

    def get_edge_weight(self, u: str, v: str) -> float:
        """Retorna o peso (custo) de uma conexão."""
        if not self._graph.has_edge(u, v):
            raise KeyError(f"Aresta '{u}' <-> '{v}' não encontrada.")
        return self._graph[u][v]["weight"]

    def get_edges(self) -> list[tuple]:
        """Retorna lista de arestas no formato (u, v, weight)."""
        return [(u, v, data["weight"]) for u, v, data in self._graph.edges(data=True)]

    def get_edge_count(self) -> int:
        """Retorna o número de conexões."""
        return self._graph.number_of_edges()

    def get_neighbors(self, node_id: str) -> list[str]:
        """Retorna os bairros vizinhos (conectados diretamente)."""
        if node_id not in self._graph:
            raise KeyError(f"Bairro '{node_id}' não encontrado.")
        return list(self._graph.neighbors(node_id))

    # ------------------------------------------------------------------
    # Propriedades estruturais
    # ------------------------------------------------------------------

    def is_connected(self) -> bool:
        """Verifica se o grafo é conexo (todos os bairros alcançáveis)."""
        if self._graph.number_of_nodes() == 0:
            return True
        return nx.is_connected(self._graph)

    def get_total_weight(self) -> float:
        """Retorna a soma de todos os pesos das arestas."""
        return sum(w for _, _, w in self.get_edges())

    def get_density(self) -> float:
        """Retorna a densidade do grafo (0 a 1)."""
        return nx.density(self._graph)

    def get_degree(self, node_id: str) -> int:
        """Retorna o grau (número de conexões) de um bairro."""
        if node_id not in self._graph:
            raise KeyError(f"Bairro '{node_id}' não encontrado.")
        return self._graph.degree(node_id)

    # ------------------------------------------------------------------
    # Acesso ao grafo networkx subjacente
    # ------------------------------------------------------------------

    def get_networkx_graph(self) -> nx.Graph:
        """Retorna o objeto networkx.Graph interno (usado pelos algoritmos MST)."""
        return self._graph

    def clear(self) -> None:
        """Remove todos os nós e arestas."""
        self._graph.clear()

    # ------------------------------------------------------------------
    # Representação
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"FiberGraph("
            f"nodes={self.get_node_count()}, "
            f"edges={self.get_edge_count()}, "
            f"connected={self.is_connected()})"
        )

    def summary(self) -> str:
        """Retorna um resumo textual do grafo."""
        lines = [
            "=== Resumo da Rede de Fibra Óptica ===",
            f"  Bairros (nós):      {self.get_node_count()}",
            f"  Conexões (arestas): {self.get_edge_count()}",
            f"  Custo total:        {self.get_total_weight():.2f}",
            f"  Densididade:        {self.get_density():.4f}",
            f"  Grafo conexo:       {self.is_connected()}",
        ]
        return "\n".join(lines)
        