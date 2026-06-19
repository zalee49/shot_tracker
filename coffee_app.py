import base64
import html
import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import date

ROAST_LEVELS = ["Light", "Medium", "Medium-Dark", "Dark"]
PROCESS_METHODS = ["Washed", "Natural", "Honey", "Other"]
GRIND_DIRECTIONS = ["First shot with this grind", "Same", "Coarser", "Finer"]

COFFEE_SVG = """
<svg width="{size}" height="{size}" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
    <ellipse cx="24" cy="24" rx="14" ry="20" fill="#6B4C35"/>
    <path d="M24 6 C29 13 29 21 24 28 C19 35 19 40 24 42"
          stroke="#37352F" stroke-width="2.5" fill="none" stroke-linecap="round"/>
</svg>
"""


def get_headers():
    key = st.secrets["SUPABASE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def get_url(path=""):
    return f"{st.secrets['SUPABASE_URL']}/rest/v1/shots{path}"


def load_data():
    response = requests.get(
        get_url("?order=id.desc"),
        headers=get_headers()
    )
    return response.json()


def save_shot(row):
    requests.post(
        get_url(),
        headers={**get_headers(), "Prefer": "return=minimal"},
        json=row
    )


def delete_shot(shot_id):
    requests.delete(
        get_url(f"?id=eq.{shot_id}"),
        headers=get_headers()
    )


def get_saved_beans(shots):
    seen = {}
    for shot in shots:
        name = shot["bean_name"]
        if name not in seen:
            seen[name] = shot
    return seen


def star_rating(rating):
    if not rating:
        return "Not rated"
    return "★" * int(rating) + "☆" * (5 - int(rating))


def fmt(value):
    return int(value) if value == int(value) else value


def safe_index(options, value, default=0):
    try:
        return options.index(value)
    except ValueError:
        return default


def ratio_flag(yield_, dose, target):
    if not dose:
        return ""
    ratio = yield_ / dose
    diff = ratio - target
    if abs(diff) <= 0.05:
        return "On target"
    elif diff > 0:
        return f"Over by {diff:.2f} — try less yield or more dose"
    else:
        return f"Under by {abs(diff):.2f} — try more yield or less dose"


def ratio_badge_class(flag):
    if flag == "On target":
        return "badge-on-target"
    return "badge-off-target"


def shot_prop_grid(rows):
    items = "".join(
        f'<div class="prop-label">{html.escape(str(label))}</div>'
        f'<div class="prop-value">{html.escape(str(value))}</div>'
        for label, value in rows
    )
    return f'<div class="prop-grid">{items}</div>'


def notion_line_chart(series):
    chart_df = pd.DataFrame({"value": series.values, "index": range(len(series))})
    return alt.Chart(chart_df).mark_line(color="#2383E2", strokeWidth=2).encode(
        x=alt.X(
            "index:Q",
            title=None,
            axis=alt.Axis(grid=False, domain=False, ticks=False, labels=False),
        ),
        y=alt.Y(
            "value:Q",
            title=None,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                gridColor="#F7F6F3",
                domainColor="rgba(55, 53, 47, 0.09)",
                tickColor="rgba(55, 53, 47, 0.09)",
                labelColor="#787774",
            ),
        ),
    ).properties(height=200)


st.set_page_config(
    page_title="Espresso Tracker",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="auto",
)

if "target_ratio" not in st.session_state:
    st.session_state.target_ratio = 2.0

st.html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
    --notion-bg: #FFFFFF;
    --notion-bg-subtle: #F7F6F3;
    --notion-bg-hover: #EFEDE8;
    --notion-text: #37352F;
    --notion-text-secondary: #787774;
    --notion-border: rgba(55, 53, 47, 0.09);
    --notion-border-strong: rgba(55, 53, 47, 0.16);
    --notion-blue: #2383E2;
    --notion-blue-hover: #1B6EC2;
    --notion-blue-muted: rgba(35, 131, 226, 0.08);
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--notion-text) !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: var(--notion-text) !important;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer,
[data-testid="stFooter"],
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[class*="viewerBadge"],
[class*="embeddedAppMetaInfoBar"],
[class*="AppMetaInfoBar"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    position: fixed !important;
}
.stDeployButton { display: none !important; }

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 860px;
}

[data-testid="stSidebar"] {
    background-color: var(--notion-bg-subtle) !important;
    border-right: 1px solid var(--notion-border) !important;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

.sidebar-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--notion-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
}
.sidebar-divider {
    height: 1px;
    background: var(--notion-border);
    margin: 20px 0;
}

.page-title {
    font-size: 1.625rem;
    font-weight: 600;
    color: var(--notion-text);
    line-height: 1.3;
    margin: 0;
}
.page-subtitle {
    font-size: 0.875rem;
    color: var(--notion-text-secondary);
    margin-top: 4px;
}

.section-header {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--notion-text);
    margin: 2rem 0 1rem 0;
}
.subsection-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--notion-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 1rem 0 0.75rem 0;
}
.chart-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--notion-text-secondary);
    margin: 1.25rem 0 0.5rem 0;
}

.stats-row {
    margin-bottom: 1.5rem;
}
[data-testid="stMetric"] {
    background: var(--notion-bg);
    border: 1px solid var(--notion-border);
    border-radius: var(--radius-lg);
    padding: 1rem 1.25rem;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    color: var(--notion-text-secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--notion-text) !important;
}

input[type="text"], input[type="number"], textarea, select {
    background-color: var(--notion-bg) !important;
    border: 1px solid var(--notion-border-strong) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--notion-text) !important;
}
input[type="text"]:focus, input[type="number"]:focus, textarea:focus, select:focus {
    border-color: var(--notion-blue) !important;
    box-shadow: 0 0 0 2px var(--notion-blue-muted) !important;
}

[data-testid="stExpander"] {
    background-color: var(--notion-bg) !important;
    border: 1px solid var(--notion-border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: none !important;
    margin-bottom: 6px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-weight: 500 !important;
    padding: 12px 16px !important;
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.4 !important;
}
[data-testid="stExpander"] summary:hover {
    background-color: var(--notion-bg-subtle) !important;
}

[data-testid="stFormSubmitButton"] button {
    background: var(--notion-blue) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: var(--radius-md) !important;
    border: none !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: var(--notion-blue-hover) !important;
}

[data-testid="stExpander"] [data-testid="stButton"] button {
    background: rgba(55, 53, 47, 0.06) !important;
    color: #E03E3E !important;
    border: 1px solid var(--notion-border) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] [data-testid="stButton"] button:hover {
    background: rgba(224, 62, 62, 0.08) !important;
    border-color: rgba(224, 62, 62, 0.2) !important;
}

hr {
    border: none !important;
    height: 1px !important;
    background: var(--notion-border) !important;
    margin: 1.5rem 0 !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--notion-border) !important;
}

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 8px;
}
.badge-roast { background: rgba(107, 76, 53, 0.1); color: #6B4C35; }
.badge-process { background: rgba(35, 131, 226, 0.1); color: #2383E2; }
.badge-on-target { background: rgba(46, 125, 50, 0.1); color: #2E7D32; }
.badge-off-target { background: rgba(237, 108, 2, 0.1); color: #ED6C02; }
.badge-neutral { background: rgba(55, 53, 47, 0.06); color: #787774; }

.prop-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px 16px;
    margin: 12px 0;
}
.prop-label {
    font-size: 0.875rem;
    color: var(--notion-text-secondary);
}
.prop-value {
    font-size: 0.875rem;
    color: var(--notion-text);
}

.delete-divider {
    height: 1px;
    background: var(--notion-border);
    margin: 16px 0 12px 0;
}

.shot-summary-line {
    font-size: 0.875rem;
    color: var(--notion-text-secondary);
    margin-bottom: 10px;
}

@media (max-width: 640px) {
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stDeployButton {
        display: none !important;
    }

    [data-testid="stAppViewContainer"] > section.main {
        padding-top: 0 !important;
    }

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: calc(2rem + 52px);
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }

    .page-title {
        font-size: 1.25rem;
    }
    .page-subtitle {
        font-size: 0.8125rem;
    }

    .section-header {
        font-size: 1.125rem;
        margin: 1.5rem 0 0.75rem 0;
    }

    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 0 !important;
    }

    [data-testid="stMetric"] {
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
    }

    [data-testid="stExpander"] summary {
        padding: 14px 12px !important;
        min-height: 44px !important;
        font-size: 0.875rem !important;
    }

    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button {
        min-height: 44px !important;
        font-size: 1rem !important;
    }

    .prop-grid {
        grid-template-columns: 1fr;
        gap: 2px 0;
    }
    .prop-label {
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 10px;
    }
    .prop-label:first-child {
        margin-top: 0;
    }
    .prop-value {
        font-size: 0.875rem;
        margin-bottom: 4px;
        word-break: break-word;
    }

    input[type="text"], input[type="number"], textarea, select {
        font-size: 16px !important;
    }

    .stApp::after {
        content: "";
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 52px;
        background: var(--notion-bg);
        z-index: 999999;
        pointer-events: none;
    }
}
</style>
<script>
(function () {
    function hideBranding() {
        document.querySelectorAll(
            'footer, [data-testid="stFooter"], [data-testid="stBottom"], ' +
            '[data-testid="stBottomBlockContainer"], [class*="viewerBadge"], ' +
            '[class*="embeddedAppMetaInfoBar"], [class*="AppMetaInfoBar"]'
        ).forEach(function (el) {
            el.style.setProperty("display", "none", "important");
        });
    }
    hideBranding();
    new MutationObserver(hideBranding).observe(document.body, { childList: true, subtree: true });
})();
</script>
""")

st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <img src="data:image/svg+xml;base64,{base64.b64encode(COFFEE_SVG.format(size=32).encode()).decode()}" width="32" height="32" style="flex-shrink:0;">
        <div>
            <div class="page-title">Zach's Espresso Tracker</div>
            <div class="page-subtitle">Track · Taste · Dial In</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

shots = load_data()
saved_beans = get_saved_beans(shots)

if "quick_mode" not in st.session_state:
    st.session_state.quick_mode = bool(saved_beans)

if shots:
    rated = [s["rating"] for s in shots if s.get("rating")]
    avg_rating_display = (
        "★" * round(sum(rated) / len(rated)) + "☆" * (5 - round(sum(rated) / len(rated)))
        if rated else "—"
    )
    ratios = [s["yield"] / s["dose"] for s in shots if s.get("dose")]
    avg_ratio = f"{sum(ratios)/len(ratios):.2f}:1" if ratios else "—"

    st.markdown('<div class="stats-row">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Shots Logged", len(shots))
    with col2:
        st.metric("Avg Rating", avg_rating_display)
    with col3:
        st.metric("Avg Brew Ratio", avg_ratio)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-header">Log a New Shot</div>', unsafe_allow_html=True)

settings_col1, settings_col2 = st.columns(2)
with settings_col1:
    st.session_state.quick_mode = st.checkbox(
        "Quick Log Mode",
        value=st.session_state.quick_mode,
        help="When a saved bean is selected, only show shot fields.",
    )
with settings_col2:
    st.session_state.target_ratio = st.number_input(
        "Target Brew Ratio",
        min_value=1.0,
        max_value=4.0,
        step=0.1,
        value=st.session_state.target_ratio,
        help="A 1:2 ratio means 18g dose produces 36g yield (yield ÷ dose).",
    )

quick_mode = st.session_state.quick_mode
target_ratio = st.session_state.target_ratio

bean_options = ["-- New Bean --"] + list(saved_beans.keys())
selected_bean = st.selectbox("Select Bean", bean_options)

if selected_bean != "-- New Bean --":
    bean_data = saved_beans[selected_bean]
    default_name = selected_bean
    default_roaster = bean_data["roaster"]
    default_origin = bean_data["origin"]
    default_roast_level = bean_data["roast_level"]
    default_process = bean_data["process_method"]
    try:
        default_roast_date = date.fromisoformat(str(bean_data["roast_date"]))
    except Exception:
        default_roast_date = date.today()
else:
    default_name = ""
    default_roaster = ""
    default_origin = ""
    default_roast_level = "Light"
    default_process = "Washed"
    default_roast_date = date.today()

is_new_bean = selected_bean == "-- New Bean --"
show_bean_fields = is_new_bean or not quick_mode

if quick_mode and not is_new_bean:
    st.caption("Quick Log: using saved bean details. Turn off Quick Log Mode to edit them.")

with st.container(border=True):
    with st.form("shot_form"):
        if show_bean_fields:
            st.markdown('<div class="subsection-label">Bean Info</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                bean_name = st.text_input("Bean Name", value=default_name, placeholder="e.g. Ethiopia Yirgacheffe")
                origin = st.text_input("Origin", value=default_origin, placeholder="e.g. Ethiopia, Yirgacheffe")
                roast_date = st.date_input("Roast Date", value=default_roast_date)
            with col2:
                roaster = st.text_input("Roaster", value=default_roaster, placeholder="e.g. Blue Bottle")
                roast_level = st.selectbox(
                    "Roast Level",
                    ROAST_LEVELS,
                    index=safe_index(ROAST_LEVELS, default_roast_level),
                )
                process_method = st.selectbox(
                    "Process Method",
                    PROCESS_METHODS,
                    index=safe_index(PROCESS_METHODS, default_process),
                )
            st.markdown('<div class="subsection-label">Shot Parameters</div>', unsafe_allow_html=True)
        else:
            bean_name = default_name
            roaster = default_roaster
            origin = default_origin
            roast_level = default_roast_level
            process_method = default_process
            roast_date = default_roast_date

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            dose = st.number_input("Dose (g)", min_value=0.0, max_value=30.0, step=0.1, value=18.0)
        with row1_col2:
            yield_ = st.number_input("Yield (g)", min_value=0.0, max_value=100.0, step=0.1, value=36.0)

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            brew_time = st.number_input("Brew Time (s)", min_value=0, max_value=120, step=1, value=28)
        with row2_col2:
            temperature = st.number_input("Temperature (°C)", min_value=80.0, max_value=100.0, step=0.5, value=93.0)

        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            grind_size = st.text_input("Grind Size", placeholder="e.g. 11, or 2.5 turns")
        with row3_col2:
            grind_direction = st.selectbox("Grind Direction vs Last Shot", GRIND_DIRECTIONS)

        rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=3)
        tasting_notes = st.text_area("Tasting Notes", placeholder="e.g. Bright acidity, notes of blueberry...")

        submitted = st.form_submit_button("Log Shot", use_container_width=True)

if submitted:
    save_shot({
        "date": date.today().strftime("%Y-%m-%d"),
        "bean_name": bean_name,
        "roaster": roaster,
        "origin": origin,
        "roast_level": roast_level,
        "process_method": process_method,
        "roast_date": roast_date.strftime("%Y-%m-%d"),
        "dose": dose,
        "yield": yield_,
        "brew_time": brew_time,
        "grind_size": grind_size,
        "grind_direction": grind_direction,
        "temperature": temperature,
        "rating": rating,
        "tasting_notes": tasting_notes or "",
    })
    ratio = yield_ / dose if dose else 0
    flag = ratio_flag(yield_, dose, target_ratio)
    st.success(f"Shot logged! Brew ratio: {ratio:.2f}:1 — {flag}")
    st.rerun()

st.markdown('<div class="section-header">Shot History</div>', unsafe_allow_html=True)

if not shots:
    st.info("No shots logged yet. Fill in the form above to log your first shot!")
else:
    for shot in shots:
        display_date = date.fromisoformat(shot["date"]).strftime("%m/%d/%y")
        ratio = shot["yield"] / shot["dose"] if shot["dose"] else 0
        flag = ratio_flag(shot["yield"], shot["dose"], target_ratio)
        rating_stars = star_rating(shot.get("rating"))
        badge_cls = ratio_badge_class(flag) if flag else "badge-neutral"
        if flag == "On target":
            short_flag = "On target"
        elif "Over" in flag:
            short_flag = "Over"
        elif "Under" in flag:
            short_flag = "Under"
        else:
            short_flag = "—"
        label = f"{display_date} · {shot['bean_name']}"
        summary_line = (
            f"{short_flag} · {fmt(shot['dose'])}g → {fmt(shot['yield'])}g · "
            f"{shot['brew_time']}s · {rating_stars}"
        )

        with st.expander(label, expanded=False):
            st.markdown(
                f'<div class="shot-summary-line">{html.escape(summary_line)}</div>'
                f'<span class="badge {badge_cls}">{html.escape(short_flag)}</span>'
                f'<span class="badge badge-roast">{html.escape(shot["roast_level"])}</span>'
                f'<span class="badge badge-process">{html.escape(shot["process_method"])}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                shot_prop_grid([
                    ("Brew Ratio", f"{ratio:.2f}:1 — {flag}"),
                    ("Grind Size", shot["grind_size"] or "—"),
                    ("Direction", shot.get("grind_direction") or "—"),
                    ("Temperature", f"{shot['temperature']}°C"),
                    ("Tasting Notes", shot.get("tasting_notes") or "—"),
                    ("Roaster", shot["roaster"] or "—"),
                    ("Origin", shot["origin"] or "—"),
                    ("Roast Date", shot["roast_date"]),
                ]),
                unsafe_allow_html=True,
            )
            st.markdown('<div class="delete-divider"></div>', unsafe_allow_html=True)
            if st.button("Delete", key=f"del_{shot['id']}"):
                delete_shot(shot["id"])
                st.rerun()

    st.markdown('<div class="section-header">Trends</div>', unsafe_allow_html=True)

    df = pd.DataFrame(shots)
    df = df[::-1].reset_index(drop=True)
    df["Brew Ratio"] = df["yield"] / df["dose"]

    st.markdown('<div class="chart-label">Brew Ratio Over Time</div>', unsafe_allow_html=True)
    st.altair_chart(notion_line_chart(df["Brew Ratio"]), use_container_width=True)

    st.markdown('<div class="chart-label">Brew Time Over Time</div>', unsafe_allow_html=True)
    st.altair_chart(notion_line_chart(df["brew_time"]), use_container_width=True)

    if df["rating"].notna().any():
        st.markdown('<div class="chart-label">Rating Over Time</div>', unsafe_allow_html=True)
        st.altair_chart(notion_line_chart(df["rating"].dropna()), use_container_width=True)
