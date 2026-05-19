"""
app.py — Streamlit: Otimização de Rede de Fibra Óptica em The Continent
"""
import base64
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.utils.data_loader import load
from src.algorithms.mst_solver import MSTSolver
from src.visualization import metrics

# -----------------------------------------------------------------------
# Configuração da página
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="The Continent — Rede de Fibra Óptica",
    page_icon="🗺️",
    layout="wide",
)

DATASET  = Path("src/data/the_continent_kingdoms.json")
MAP_PATH = Path("src/assets/the_continent_map.jpg")

# Espaço de coordenadas usado no dataset (referência: canto noroeste do mapa)
MAP_X_MAX = 750
MAP_Y_MAX = 1100

REGION_COLORS = {
    "norte":   "#5B9BD5",
    "central": "#70AD47",
    "sul":     "#ED7D31",
}

COLOR_MST_EDGE = "#F4C430"
COLOR_ALL_EDGE = "#888888"


# -----------------------------------------------------------------------
# Dados (cacheados)
# -----------------------------------------------------------------------
@st.cache_data
def get_data():
    neighborhoods, connections = load(DATASET)
    solver = MSTSolver(neighborhoods, connections)
    return neighborhoods, connections, solver


@st.cache_data
def get_result(algorithm: str):
    _, _, solver = get_data()
    return solver.solve(algorithm=algorithm.lower())


# -----------------------------------------------------------------------
# Figura Plotly
# -----------------------------------------------------------------------
def build_figure(neighborhoods, connections, result, show_all_edges: bool) -> go.Figure:
    node_map = {n.id: n for n in neighborhoods}
    mst_pairs = {frozenset({e.source, e.target}) for e in result.mst_edges}

    fig = go.Figure()

    # Imagem de fundo
    if MAP_PATH.exists():
        encoded = base64.b64encode(MAP_PATH.read_bytes()).decode()
        ext = MAP_PATH.suffix.lstrip(".")
        fig.add_layout_image(dict(
            source=f"data:image/{ext};base64,{encoded}",
            xref="x", yref="y",
            x=0, y=0,
            sizex=MAP_X_MAX, sizey=MAP_Y_MAX,
            sizing="stretch",
            opacity=1,
            layer="below",
            xanchor="left",
            yanchor="top",
        ))

    # Todas as conexões disponíveis (opcional, tracejado cinza)
    if show_all_edges:
        for c in connections:
            src = node_map[c["source"]]
            tgt = node_map[c["target"]]
            fig.add_trace(go.Scatter(
                x=[src.coords.x, tgt.coords.x, None],
                y=[src.coords.y, tgt.coords.y, None],
                mode="lines",
                line=dict(color=COLOR_ALL_EDGE, width=1, dash="dot"),
                hoverinfo="skip",
                showlegend=False,
            ))

    # Arestas da MST (linha dourada)
    mst_x, mst_y = [], []
    for e in result.mst_edges:
        src = node_map[e.source]
        tgt = node_map[e.target]
        mst_x += [src.coords.x, tgt.coords.x, None]
        mst_y += [src.coords.y, tgt.coords.y, None]

    fig.add_trace(go.Scatter(
        x=mst_x, y=mst_y,
        mode="lines",
        line=dict(color=COLOR_MST_EDGE, width=3),
        name="Rota MST",
        hoverinfo="skip",
    ))

    # Pontos invisíveis no meio de cada aresta MST para hover de custo/terreno
    for e in result.mst_edges:
        src = node_map[e.source]
        tgt = node_map[e.target]
        mid_x = (src.coords.x + tgt.coords.x) / 2
        mid_y = (src.coords.y + tgt.coords.y) / 2
        fig.add_trace(go.Scatter(
            x=[mid_x], y=[mid_y],
            mode="markers",
            marker=dict(size=10, color=COLOR_MST_EDGE, opacity=0.4),
            showlegend=False,
            hovertemplate=(
                f"<b>{src.name} ↔ {tgt.name}</b><br>"
                f"Terreno: {e.metadata['terrain'].capitalize()}<br>"
                f"Distância: {e.metadata['distance_km']} km<br>"
                f"Custo: {e.weight:,.0f} k coroas<br>"
                "<extra></extra>"
            ),
        ))

    # Nós por região (para legenda com cor)
    for region, color in REGION_COLORS.items():
        nodes = [n for n in neighborhoods if n.region == region]
        if not nodes:
            continue
        fig.add_trace(go.Scatter(
            x=[n.coords.x for n in nodes],
            y=[n.coords.y for n in nodes],
            mode="markers+text",
            marker=dict(
                size=14,
                color=color,
                line=dict(color="white", width=1.5),
                symbol="circle",
            ),
            text=[n.name for n in nodes],
            textposition="top center",
            textfont=dict(size=10, color="white",
                          family="Georgia, serif"),
            name=region.capitalize(),
            customdata=[[n.name, n.region.capitalize(), n.capital or "—", n.population] for n in nodes],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Região: %{customdata[1]}<br>"
                "Capital: %{customdata[2]}<br>"
                "População estimada: %{customdata[3]:,}<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis=dict(range=[0, MAP_X_MAX], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[MAP_Y_MAX, 0], showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        legend=dict(
            bgcolor="rgba(0,0,0,0.65)",
            font=dict(color="white", size=12),
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
            x=0.01, y=0.01,
            xanchor="left",
            yanchor="bottom",
        ),
        height=720,
    )

    return fig


# -----------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configurações")

    algorithm = st.radio(
        "Algoritmo MST",
        ["Kruskal", "Prim"],
        index=0,
        help="Kruskal ordena todas as arestas; Prim cresce a partir de um nó.",
    )

    show_all = st.checkbox("Mostrar todas as conexões disponíveis", value=False)

    st.divider()
    st.caption("Projeto: Otimização de Rede de Fibra Óptica\nThe Continent (The Witcher)\n2025")


# -----------------------------------------------------------------------
# Conteúdo principal
# -----------------------------------------------------------------------
st.title("🗺️ The Continent — Rede de Fibra Óptica")
st.caption(
    "Visualização da Árvore Geradora Mínima (MST) sobre o mapa de The Continent. "
    "As rotas douradas formam a rede ótima de fibra óptica entre os reinos."
)

if not MAP_PATH.exists():
    st.warning(
        "Mapa não encontrado. Salve a imagem em `assets/the_continent_map.jpg` "
        "para exibi-la como fundo.",
        icon="⚠️",
    )

neighborhoods, connections, solver = get_data()
result = get_result(algorithm)

# Mapa interativo
fig = build_figure(neighborhoods, connections, result, show_all_edges=show_all)
st.plotly_chart(fig, width="stretch")

# KPIs
st.subheader("📊 Métricas da MST")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Custo total (k coroas)", f"{result.total_cost:,.0f}")
col2.metric("Economia gerada", f"{result.savings_pct:.1f}%")
col3.metric("Reinos conectados", result.nodes_count)
col4.metric("Rotas na MST", result.edges_in_mst)

# Tabelas em abas
tab1, tab2, tab3, tab4 = st.tabs(["Resumo", "Por terreno", "Por região", "Top rotas"])

with tab1:
    df_summary = metrics.summary(result, solver)
    df_summary["Valor"] = df_summary["Valor"].astype(str)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

with tab2:
    st.dataframe(metrics.cost_by_terrain(result), use_container_width=True, hide_index=True)

with tab3:
    st.dataframe(metrics.regional_cost(result, solver), use_container_width=True, hide_index=True)

with tab4:
    tops = metrics.top_edges(result, solver, n=5)
    c1, c2 = st.columns(2)
    with c1:
        st.caption("5 rotas mais caras")
        st.dataframe(tops["mais_caras"], use_container_width=True, hide_index=True)
    with c2:
        st.caption("5 rotas mais baratas")
        st.dataframe(tops["mais_baratas"], use_container_width=True, hide_index=True)
