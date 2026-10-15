"""Gráficos da fronteira inferior; dinheiro é calculado com Decimal em analysis.py."""

import plotly.graph_objects as go

from analysis import boundary_rows


def boundary_chart(zoom: bool = False) -> go.Figure:
    rows = boundary_rows()
    if zoom:
        rows = [row for row in rows if abs(row["Valor"]) <= 0.01]
    values = [row["Valor"] for row in rows]
    fig = go.Figure(go.Scatter(
        x=values, y=[1] * len(rows), mode="markers+text",
        text=[row["Ponto"] + "<br>" + row["Valor decimal"] for row in rows],
        textposition="top center",
        marker={"size": 18, "color": ["#e45d65" if x < 0 else "#29b3a4" for x in values],
                "line": {"width": 2, "color": "white"}},
        customdata=[row["Esperado"] for row in rows],
        hovertemplate="%{text}<br>%{customdata}<extra></extra>",
    ))
    low, high = (-0.016, 0.016) if zoom else (-135, 135)
    fig.add_vrect(x0=low, x1=0, fillcolor="#e45d65", opacity=0.09, line_width=0)
    fig.add_vrect(x0=0, x1=high, fillcolor="#29b3a4", opacity=0.09, line_width=0)
    fig.add_vline(x=0, line_dash="dash", line_color="#64748b")
    fig.update_layout(
        title="Fronteira ampliada: um centavo de cada lado" if zoom else "Domínio completo: regiões válida e inválida",
        height=285, margin={"l": 20, "r": 20, "t": 65, "b": 55},
        template="plotly_dark", paper_bgcolor="#10141c", plot_bgcolor="#10141c", showlegend=False,
        xaxis={"title": "Valor de entrada (R$)", "range": [low, high],
               "tickvals": values, "ticktext": [row["Valor decimal"] for row in rows], "zeroline": False},
        yaxis={"visible": False, "range": [0.65, 1.55]},
        font={"family": "Arial", "size": 12},
    )
    # Na escala completa, o trio perto de zero compartilha uma legenda para evitar sobreposição.
    if not zoom:
        fig.data[0].text = ["Exterior<br>-100,00", "", "Fronteira<br>ver ampliação", "", "Interior<br>100,00"]
    return fig
