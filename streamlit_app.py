import streamlit as st
import pydeck as pdk
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Housing Policy Explorer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
  .block-container {
    padding-top: 1.2rem; padding-bottom: 0;
    padding-left: 2rem;  padding-right: 2rem;
    max-width: 100%;
  }
  .step-label {
    font-size: 10px; font-weight: 700; color: #888;
    letter-spacing: 0.8px; text-transform: uppercase; margin: 0 0 2px 0;
  }
  .city-name {
    font-size: 26px; font-weight: 900; color: #1a1a2e;
    text-decoration: underline; margin: 0; line-height: 1.1;
  }
  .map-desc {
    background: white; border: 1px solid #ddd; border-radius: 4px;
    padding: 10px 12px; font-size: 12px; line-height: 1.6;
    max-width: 340px; margin-bottom: 6px;
  }
  .legend-wrap {
    display: flex; align-items: center; gap: 10px;
    font-size: 11px; color: #666; margin-top: 6px;
  }
  .legend-bar {
    width: 180px; height: 11px;
    background: linear-gradient(to right, #deedf0, #142850);
    border-radius: 2px; flex-shrink: 0;
  }
  .legend-labels {
    display: flex; width: 180px; justify-content: space-between;
    font-size: 10px; color: #666; margin-top: 2px;
  }
  .section-title {
    font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 4px 0 0 0;
  }
  .sub-axis-label {
    font-size: 10px; color: #888; margin-top: -4px; margin-bottom: 4px;
  }
  div[data-testid="stRadio"] > div[role="radiogroup"] { gap: 4px; }
  div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    border: 1px solid #ccc; border-radius: 20px;
    padding: 4px 13px; font-size: 13px; cursor: pointer;
  }
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
  header    { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Sample Data ──────────────────────────────────────────────────────────────
CITIES = ["Denver", "Seattle", "Portland", "Minneapolis"]
POLICY_SCENARIOS = ["Status Quo", "Transit Upzone", "Missing Middle", "Parking Change"]
ECONOMIC_SCENARIOS = ["Unfavorable", "Baseline", "Favorable"]
UNITS = ["Total Count", "Net Change", "Percent Change"]

POLICY_IMPACT = {
    "Unfavorable": {
        "Status Quo": 0,
        "Transit Upzone": 7,
        "Missing Middle": 28,
        "Parking Change": 4,
    },
    "Baseline": {
        "Status Quo": 0,
        "Transit Upzone": 12,
        "Missing Middle": 38,
        "Parking Change": 7,
    },
    "Favorable": {
        "Status Quo": 0,
        "Transit Upzone": 9,
        "Missing Middle": 35,
        "Parking Change": 6,
    },
}
ECONOMIC_IMPACT = {
    "Status Quo": {"Unfavorable": -14, "Baseline": 0, "Favorable": 20},
    "Transit Upzone": {"Unfavorable": -11, "Baseline": 0, "Favorable": 26},
    "Missing Middle": {"Unfavorable": -9, "Baseline": 0, "Favorable": 32},
    "Parking Change": {"Unfavorable": -7, "Baseline": 0, "Favorable": 17},
}


def generate_geojson(policy: str, economic: str) -> dict:
    """Return a FeatureCollection grid over Denver with colour-coded values."""
    rng = np.random.default_rng(42)
    lat_min, lat_max = 39.62, 39.84
    lon_min, lon_max = -105.12, -104.87
    rows, cols = 11, 13
    lat_step = (lat_max - lat_min) / rows
    lon_step = (lon_max - lon_min) / cols

    policy_mult = {
        "Status Quo": 1.0,
        "Transit Upzone": 1.12,
        "Missing Middle": 1.38,
        "Parking Change": 1.07,
    }
    econ_mult = {"Unfavorable": 0.55, "Baseline": 1.0, "Favorable": 1.75}

    features = []
    for i in range(rows):
        for j in range(cols):
            lat0, lat1 = lat_min + i * lat_step, lat_min + (i + 1) * lat_step
            lon0, lon1 = lon_min + j * lon_step, lon_min + (j + 1) * lon_step
            value = min(
                rng.uniform(0, 400) * policy_mult[policy] * econ_mult[economic], 700
            )
            t = value / 700.0
            color = [int(222 - 202 * t), int(237 - 197 * t), int(240 - 160 * t), 185]
            features.append(
                {
                    "type": "Feature",
                    "properties": {"value": round(value, 1), "fill_color": color},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [lon0, lat0],
                                [lon1, lat0],
                                [lon1, lat1],
                                [lon0, lat1],
                                [lon0, lat0],
                            ]
                        ],
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def make_bar_chart(labels, values, highlight_label, x_title, height=210):
    colors = ["#1a2744" if l == highlight_label else "#b5b5b5" for l in labels]
    texts = [f"+{v}%" if v >= 0 else f"{v}%" for v in values]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=texts,
            textposition="outside",
            textfont=dict(size=10),
            cliponaxis=False,
        )
    )
    fig.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=-0.5,
        y1=len(labels) - 0.5,
        line=dict(color="#444", width=1.5, dash="dot"),
    )
    x_pad = max(abs(v) for v in values) * 0.25
    fig.update_layout(
        margin=dict(l=0, r=55, t=6, b=42),
        height=height,
        xaxis=dict(
            range=[min(values) - x_pad, max(values) + x_pad],
            title=x_title,
            title_font=dict(size=9, color="#888"),
            tickfont=dict(size=8),
            gridcolor="#f0f0f0",
            zeroline=False,
        ),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return fig


# ── Top Controls ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns([1.2, 2, 2.4, 2.4])

with c1:
    st.markdown('<p class="step-label">1. Select City</p>', unsafe_allow_html=True)
    city = st.selectbox("city", CITIES, label_visibility="collapsed", key="city")
    st.markdown(f'<p class="city-name">{city.upper()} ▾</p>', unsafe_allow_html=True)

with c2:
    st.markdown(
        '<p class="step-label">2. Select Policy Scenario</p>', unsafe_allow_html=True
    )
    policy = st.selectbox(
        "policy", POLICY_SCENARIOS, index=1, label_visibility="collapsed", key="policy"
    )

with c3:
    st.markdown(
        '<p class="step-label">3. Select Economic Scenario</p>', unsafe_allow_html=True
    )
    economic = st.radio(
        "economic",
        ECONOMIC_SCENARIOS,
        index=2,
        horizontal=True,
        label_visibility="collapsed",
        key="economic",
    )

with c4:
    st.markdown('<p class="step-label">4. Select Unit</p>', unsafe_allow_html=True)
    unit = st.radio(
        "unit",
        UNITS,
        index=2,
        horizontal=True,
        label_visibility="collapsed",
        key="unit",
    )

st.markdown(
    "<hr style='margin:6px 0 10px 0; border-color:#e0e0e0;'>", unsafe_allow_html=True
)

# ── Main Layout ───────────────────────────────────────────────────────────────
map_col, right_col = st.columns([2.8, 1.2])

with map_col:
    unit_desc = {
        "Total Count": "Total expected units per year",
        "Net Change": "Net change in expected units per year",
        "Percent Change": "Percent change in expected units per year",
    }
    st.markdown(
        f'<div class="map-desc">'
        f"<strong>{unit_desc[unit]}</strong> under the "
        f"<strong>{policy}</strong> policy scenario and "
        f"<strong>{economic}</strong> economic conditions"
        f"</div>",
        unsafe_allow_html=True,
    )

    geojson = generate_geojson(policy, economic)
    layer = pdk.Layer(
        "GeoJsonLayer",
        geojson,
        opacity=0.85,
        filled=True,
        pickable=True,
        get_fill_color="properties.fill_color",
        get_line_color=[190, 190, 190, 70],
        line_width_min_pixels=1,
    )
    view = pdk.ViewState(latitude=39.73, longitude=-104.99, zoom=10.2, pitch=0)
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={"html": "<b>Value:</b> {value}%", "style": {"fontSize": "12px"}},
    )
    st.pydeck_chart(deck, use_container_width=True, height=500)

    # Legend
    st.markdown(
        """
    <div class="legend-wrap">
      <div>
        <div class="legend-bar"></div>
        <div class="legend-labels"><span>0%</span><span>+350%</span><span>+700%</span></div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


with right_col:
    # Info buttons
    btn1, btn2 = st.columns([1.9, 1.0])
    with btn1:
        st.button(
            "What is this data showing?", use_container_width=True, key="info_btn"
        )
    with btn2:
        st.button("Expand →", use_container_width=True, key="expand_btn")
    st.button(
        "What are these policy scenarios?",
        use_container_width=True,
        key="policy_info_btn",
    )

    st.markdown("---")

    # Policy impact chart
    st.markdown(
        '<p class="section-title">Impact of Policy Scenarios ℹ</p>',
        unsafe_allow_html=True,
    )
    pol_labels = list(POLICY_IMPACT[economic].keys())
    pol_values = list(POLICY_IMPACT[economic].values())
    st.plotly_chart(
        make_bar_chart(
            pol_labels,
            pol_values,
            policy,
            "Percent change in expected units per year",
            height=220,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Economic impact chart
    st.markdown(
        '<p class="section-title">Impact of Economic Scenarios ℹ</p>',
        unsafe_allow_html=True,
    )
    econ_labels = list(ECONOMIC_IMPACT[policy].keys())
    econ_values = list(ECONOMIC_IMPACT[policy].values())
    st.plotly_chart(
        make_bar_chart(
            econ_labels,
            econ_values,
            economic,
            "Percent change in expected units per year",
            height=200,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )
