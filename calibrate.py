"""
calibrate.py — Calibrador de posições dos reinos no mapa de The Continent.

Como usar:
  1. Rode:  streamlit run calibrate.py
  2. No mapa, passe o mouse sobre a posição CORRETA de um reino.
     As coordenadas X e Y em pixels aparecem no canto superior direito do gráfico.
  3. Na barra lateral, selecione o reino, digite as coordenadas lidas e clique "Salvar".
  4. O mapa atualiza imediatamente com a nova posição.
  5. Quando todos os reinos estiverem corretos, feche e abra o app principal.
"""
import json
from pathlib import Path

import base64
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Calibrador — The Continent",
    page_icon="🎯",
    layout="wide",
)

MAP_PATH   = Path("src/assets/the_continent_map.jpg")
COORDS_FILE = Path("src/data/kingdom_pixel_coords.json")

IMG_W = 2880
IMG_H = 4096


@st.cache_data
def load_map_b64() -> tuple[str, str]:
    data = MAP_PATH.read_bytes()
    return base64.b64encode(data).decode(), MAP_PATH.suffix.lstrip(".")


def load_coords() -> dict:
    with open(COORDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_coords(coords: dict) -> None:
    with open(COORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f, indent=2, ensure_ascii=False)


def build_calibration_figure(coords: dict, selected_id: str | None) -> go.Figure:
    fig = go.Figure()

    if MAP_PATH.exists():
        encoded, ext = load_map_b64()
        fig.add_layout_image(dict(
            source=f"data:image/{ext};base64,{encoded}",
            xref="x", yref="y",
            x=0, y=0,
            sizex=IMG_W, sizey=IMG_H,
            sizing="stretch",
            opacity=1,
            layer="below",
            xanchor="left",
            yanchor="top",
        ))

    # Todos os reinos — pontos normais
    others = {k: v for k, v in coords.items() if k != selected_id}
    if others:
        fig.add_trace(go.Scatter(
            x=[v["x"] for v in others.values()],
            y=[v["y"] for v in others.values()],
            mode="markers+text",
            marker=dict(size=12, color="#5B9BD5", line=dict(color="white", width=1.5)),
            text=[v["name"] for v in others.values()],
            textposition="top center",
            textfont=dict(size=9, color="white", family="Georgia, serif"),
            name="Reinos",
            hovertemplate="<b>%{text}</b><br>x=%{x}  y=%{y}<extra></extra>",
        ))

    # Reino selecionado — destaque em amarelo com mira
    if selected_id and selected_id in coords:
        v = coords[selected_id]
        # Linhas de mira
        fig.add_shape(type="line", x0=v["x"], y0=0, x1=v["x"], y1=IMG_H,
                      line=dict(color="#F4C430", width=1, dash="dot"))
        fig.add_shape(type="line", x0=0, y0=v["y"], x1=IMG_W, y1=v["y"],
                      line=dict(color="#F4C430", width=1, dash="dot"))
        fig.add_trace(go.Scatter(
            x=[v["x"]], y=[v["y"]],
            mode="markers+text",
            marker=dict(size=18, color="#F4C430", symbol="x",
                        line=dict(color="black", width=2)),
            text=[v["name"]],
            textposition="top center",
            textfont=dict(size=11, color="#F4C430", family="Georgia, serif"),
            name=v["name"],
            hovertemplate=f"<b>{v['name']}</b><br>x=%{{x}}  y=%{{y}}<extra></extra>",
        ))

    fig.update_layout(
        xaxis=dict(range=[0, IMG_W], showgrid=False, zeroline=False,
                   showticklabels=True, title="X (pixels)"),
        yaxis=dict(range=[IMG_H, 0], showgrid=False, zeroline=False,
                   showticklabels=True, title="Y (pixels)"),
        margin=dict(l=40, r=10, t=10, b=40),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        legend=dict(bgcolor="rgba(0,0,0,0.6)", font=dict(color="white", size=11)),
        height=820,
    )
    return fig


# -----------------------------------------------------------------------
# Estado persistente
# -----------------------------------------------------------------------
if "coords" not in st.session_state:
    st.session_state.coords = load_coords()

coords = st.session_state.coords
kingdom_ids = sorted(coords.keys())
kingdom_labels = {k: coords[k]["name"] for k in kingdom_ids}

# -----------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------
with st.sidebar:
    st.title("🎯 Calibrador")
    st.caption(
        "Passe o mouse sobre a posição correta do reino no mapa.\n"
        "Leia **X** e **Y** no canto superior direito do gráfico\n"
        "e digite abaixo."
    )
    st.divider()

    selected_id = st.selectbox(
        "Reino a posicionar",
        options=kingdom_ids,
        format_func=lambda k: kingdom_labels[k],
    )

    current = coords[selected_id]
    st.markdown(f"**Posição atual:** x={current['x']}  y={current['y']}")
    st.divider()

    new_x = st.number_input("Novo X (pixels)", min_value=0, max_value=IMG_W,
                            value=current["x"], step=1)
    new_y = st.number_input("Novo Y (pixels)", min_value=0, max_value=IMG_H,
                            value=current["y"], step=1)

    if st.button("💾 Salvar posição", type="primary", use_container_width=True):
        st.session_state.coords[selected_id]["x"] = new_x
        st.session_state.coords[selected_id]["y"] = new_y
        save_coords(st.session_state.coords)
        st.success(f"{kingdom_labels[selected_id]} salvo: x={new_x}, y={new_y}")
        st.rerun()

    st.divider()
    if st.button("↩️ Recarregar do arquivo", use_container_width=True):
        st.session_state.coords = load_coords()
        st.rerun()

    st.divider()
    st.caption("Progresso")
    st.write(f"{len(coords)} reinos no arquivo")

# -----------------------------------------------------------------------
# Mapa principal
# -----------------------------------------------------------------------
st.title("🎯 Calibrador de posições — The Continent")
st.caption(
    "Passe o mouse sobre o ponto correto no mapa → leia **x** e **y** no canto do gráfico → "
    "digite na barra lateral → **Salvar**."
)

fig = build_calibration_figure(st.session_state.coords, selected_id)
st.plotly_chart(fig, use_container_width=True)

# Tabela de referência
with st.expander("Ver todas as coordenadas salvas"):
    import pandas as pd
    rows = [{"Reino": v["name"], "X (px)": v["x"], "Y (px)": v["y"]}
            for v in st.session_state.coords.values()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
