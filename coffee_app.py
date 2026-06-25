import base64
import html
import math
import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import date

ROAST_LEVELS = ["Light", "Medium", "Medium-Dark", "Dark"]
PROCESS_METHODS = ["Washed", "Natural", "Honey", "Other"]
GRIND_DIRECTIONS = ["First shot with this grind", "Same", "Coarser", "Finer"]
SHOT_FIELDS = [
    "id",
    "date",
    "bean_name",
    "roaster",
    "origin",
    "roast_level",
    "process_method",
    "roast_date",
    "dose",
    "yield",
    "brew_time",
    "grind_size",
    "grind_direction",
    "temperature",
    "rating",
    "tasting_notes",
]

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


def normalize_text(value):
    if value is None:
        return ""
    return " ".join(str(value).split())


def bean_key(value):
    return normalize_text(value).casefold()


def coerce_number(value, minimum=None, maximum=None, integer=False):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if minimum is not None and number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    if integer:
        if not number.is_integer():
            return None
        return int(number)
    return number


def normalize_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def normalize_shot(row):
    if not isinstance(row, dict):
        return None
    return {
        "id": coerce_number(row.get("id"), minimum=0, integer=True),
        "date": normalize_date(row.get("date")),
        "bean_name": normalize_text(row.get("bean_name")),
        "roaster": normalize_text(row.get("roaster")),
        "origin": normalize_text(row.get("origin")),
        "roast_level": normalize_text(row.get("roast_level")),
        "process_method": normalize_text(row.get("process_method")),
        "roast_date": normalize_date(row.get("roast_date")),
        "dose": coerce_number(row.get("dose"), minimum=0),
        "yield": coerce_number(row.get("yield"), minimum=0),
        "brew_time": coerce_number(row.get("brew_time"), minimum=0, integer=True),
        "grind_size": normalize_text(row.get("grind_size")),
        "grind_direction": normalize_text(row.get("grind_direction")),
        "temperature": coerce_number(row.get("temperature")),
        "rating": coerce_number(row.get("rating"), minimum=1, maximum=10, integer=True),
        "tasting_notes": normalize_text(row.get("tasting_notes")),
    }


def load_data():
    try:
        response = requests.get(
            get_url("?order=id.desc"),
            headers=get_headers(),
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException:
        return [], "Could not load shots from the database.", 0

    try:
        data = response.json()
    except ValueError:
        return [], "The database returned an unreadable response.", 0

    if not isinstance(data, list):
        return [], "The database returned an unexpected response.", 0

    normalized_shots = []
    skipped_rows = 0
    for row in data:
        shot = normalize_shot(row)
        if shot is None:
            skipped_rows += 1
        else:
            normalized_shots.append(shot)
    return normalized_shots, None, skipped_rows


def save_shot(row):
    response = requests.post(
        get_url(),
        headers={**get_headers(), "Prefer": "return=minimal"},
        json=row,
        timeout=15,
    )
    response.raise_for_status()


def delete_shot(shot_id):
    normalized_id = coerce_number(shot_id, minimum=0, integer=True)
    if normalized_id is None:
        st.error("Could not delete this shot because its ID is invalid.")
        return False

    try:
        response = requests.delete(
            get_url(),
            params={"id": f"eq.{normalized_id}", "select": "id"},
            headers={**get_headers(), "Prefer": "return=representation"},
            timeout=15,
        )
        response.raise_for_status()
        deleted_rows = response.json()
    except (requests.RequestException, ValueError):
        st.error("Could not delete the shot. Check the database connection and permissions.")
        return False

    if (
        not isinstance(deleted_rows, list)
        or len(deleted_rows) != 1
        or not isinstance(deleted_rows[0], dict)
        or coerce_number(deleted_rows[0].get("id"), minimum=0, integer=True)
        != normalized_id
    ):
        st.error("The database did not confirm that exactly one shot was deleted.")
        return False
    return True


def get_saved_beans(shots):
    """Return display bean names mapped to their most recent shot."""
    seen = {}
    saved_beans = {}
    for shot in shots:
        name = normalize_text(shot.get("bean_name"))
        key = bean_key(name)
        if key and key not in seen:
            seen[key] = name
            saved_beans[name] = shot
    return saved_beans


def saved_bean_name(saved_beans, value):
    target_key = bean_key(value)
    return next(
        (name for name in saved_beans if bean_key(name) == target_key),
        None,
    )


def score_text(rating):
    if not rating:
        return "Not scored"
    return f"{int(rating)}/10"


def fmt(value):
    if value is None:
        return "—"
    return int(value) if value == int(value) else value


def safe_index(options, value, default=0):
    try:
        return options.index(value)
    except ValueError:
        return default


def widget_default(value, default, minimum, maximum, integer=False):
    number = coerce_number(value)
    if number is None:
        number = default
    number = min(max(number, minimum), maximum)
    return int(number) if integer else float(number)


def display_date(value):
    normalized = normalize_date(value)
    if not normalized:
        return "Unknown date"
    return date.fromisoformat(normalized).strftime("%b %d, %Y").replace(" 0", " ")


def brew_ratio(yield_, dose):
    if yield_ is None or dose is None or dose <= 0:
        return None
    return yield_ / dose


def ratio_flag(yield_, dose, target):
    ratio = brew_ratio(yield_, dose)
    if ratio is None:
        return ""
    diff = ratio - target
    if abs(diff) <= 0.05:
        return "On target"
    elif diff > 0:
        return f"Over by {diff:.2f} — try less yield or more dose"
    else:
        return f"Under by {abs(diff):.2f} — try more yield or less dose"


def ratio_badge_class(flag):
    if flag == "On target":
        return "status-on-target"
    return "status-off-target"


def shot_prop_grid(rows):
    items = "".join(
        f'<div class="prop-label">{html.escape(str(label))}</div>'
        f'<div class="prop-value">{html.escape(str(value))}</div>'
        for label, value in rows
    )
    return f'<div class="prop-grid">{items}</div>'


def get_previous_shots_by_id(shots):
    """Map each shot id to its chronologically previous shot for the same bean.

    Iterates oldest-to-newest (reversed order); for each shot, the currently
    stored 'latest' for that bean is actually the immediate predecessor.
    """
    previous_shots = {}
    latest_shot_by_bean = {}
    for shot in reversed(shots):
        shot_id = shot.get("id")
        normalized_bean = bean_key(shot.get("bean_name"))
        if shot_id is not None:
            previous_shots[shot_id] = latest_shot_by_bean.get(normalized_bean)
        if normalized_bean:
            latest_shot_by_bean[normalized_bean] = shot
    return previous_shots


def history_metric_grid(shot, previous_shot):
    metrics = (
        ("Dose In", "dose", "g"),
        ("Dose Out", "yield", "g"),
        ("Time", "brew_time", "s"),
        ("Score", "rating", ""),
    )
    items = []
    for label, field, unit in metrics:
        value = shot.get(field)
        if value is None:
            display_value = "—"
        elif field == "rating":
            display_value = f"{fmt(float(value))}/10"
        else:
            display_value = f"{fmt(float(value))}{unit}"

        if previous_shot is None:
            change = "First shot"
        else:
            previous_value = previous_shot.get(field)
            if value is None or previous_value is None:
                change = "No comparison"
            else:
                difference = round(float(value) - float(previous_value), 2)
                if difference == 0:
                    change = "No change"
                else:
                    sign = "+" if difference > 0 else "−"
                    change = f"{sign}{fmt(abs(difference))}{unit}"

        items.append(
            '<div class="history-metric">'
            f'<div class="history-metric-label">{html.escape(label)}</div>'
            f'<div class="history-metric-value">{html.escape(display_value)}</div>'
            f'<div class="history-metric-change">{html.escape(change)}</div>'
            '</div>'
        )
    return f'<div class="history-metrics">{"".join(items)}</div>'


def trend_line_chart(
    dataframe,
    value_column,
    label,
    color="#2F6B57",
    y_domain=None,
    tooltip_format=".2f",
):
    chart_df = dataframe.reindex(columns=["date", value_column, "bean_name"]).dropna().copy()
    y_scale = alt.Scale(zero=False)
    if y_domain is not None:
        y_scale = alt.Scale(zero=False, domain=y_domain)
    return alt.Chart(chart_df).mark_line(
        color=color,
        strokeWidth=2.5,
        point=alt.OverlayMarkDef(size=48, filled=True),
    ).encode(
        x=alt.X(
            "date:T",
            title=None,
            axis=alt.Axis(
                grid=False,
                domain=False,
                tickColor="#DDD8D1",
                labelColor="#6F6A63",
                format="%b %-d",
            ),
        ),
        y=alt.Y(
            f"{value_column}:Q",
            title=None,
            scale=y_scale,
            axis=alt.Axis(
                gridColor="#EEEAE5",
                domain=False,
                tickColor="#DDD8D1",
                labelColor="#6F6A63",
            ),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("bean_name:N", title="Bean"),
            alt.Tooltip(f"{value_column}:Q", title=label, format=tooltip_format),
        ],
    ).properties(height=220)


st.set_page_config(
    page_title="Espresso Tracker",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="auto",
)

if "target_ratio" not in st.session_state:
    st.session_state.target_ratio = 2.0

st.html("""
<style>
:root {
    --surface: #FFFFFF;
    --surface-subtle: #F7F6F4;
    --surface-muted: #EFEEEB;
    --text: #1F1E1C;
    --text-muted: #6D6963;
    --border: #E4E1DC;
    --border-strong: #CDC8C1;
    --accent: #8A4B32;
    --accent-hover: #713B27;
    --accent-soft: #F4EAE6;
    --success: #2F6B57;
    --success-soft: #E8F1ED;
    --warning: #A35B16;
    --warning-soft: #FAEFE2;
    --danger: #B0443E;
    --radius: 8px;
    --shadow: 0 1px 2px rgba(31, 30, 28, 0.05);
}

html, body, .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    color: var(--text) !important;
}

.stApp {
    background: #FBFAF8;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text) !important;
    font-weight: 650 !important;
    letter-spacing: -0.015em;
}

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer,
[data-testid="stFooter"],
.stDeployButton {
    display: none !important;
}

.main .block-container,
[data-testid="stMainBlockContainer"] {
    width: 100%;
    max-width: 960px;
    margin: 0 auto;
    padding: 1.75rem 1.25rem 4rem;
}

.app-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}

.app-mark {
    display: grid;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    place-items: center;
    background: var(--accent-soft);
    border: 1px solid #E7D5CE;
    border-radius: var(--radius);
}

.page-title {
    margin: 0;
    color: var(--text);
    font-size: 1.125rem;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: -0.02em;
}

.page-subtitle {
    margin-top: 0.1rem;
    color: var(--text-muted);
    font-size: 0.78rem;
    line-height: 1.35;
}

.section-header {
    margin: 1.5rem 0 0.25rem;
    color: var(--text);
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.025em;
}

.section-copy {
    margin: 0 0 1.25rem;
    color: var(--text-muted);
    font-size: 0.875rem;
}

.subsection-label {
    margin: 1.25rem 0 0.65rem;
    color: var(--text);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 1.25rem;
    border-bottom: 1px solid var(--border);
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 42px;
    padding: 0 1px;
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 600;
}

[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--text) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    height: 2px;
    background: var(--accent) !important;
}

[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow) !important;
}

[data-testid="stExpander"] {
    margin-bottom: 0.5rem;
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    min-height: 46px;
    padding: 0.75rem 0.9rem !important;
    font-size: 0.875rem;
    font-weight: 600 !important;
}

[data-testid="stExpander"] summary:hover {
    background: var(--surface-subtle);
}

[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
[data-baseweb="textarea"] > div {
    background: var(--surface) !important;
    border-color: var(--border-strong) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
}

[data-baseweb="input"] > div:focus-within,
[data-baseweb="select"] > div:focus-within,
[data-baseweb="textarea"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}

[data-testid="stFormSubmitButton"] button {
    min-height: 44px;
    background: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: var(--radius) !important;
    color: white !important;
    font-weight: 650 !important;
    box-shadow: none !important;
}

[data-testid="stFormSubmitButton"] button:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}

[data-testid="stPopover"] button,
[data-testid="stButton"] button {
    min-height: 40px;
    border-color: var(--border-strong);
    border-radius: var(--radius);
    box-shadow: none;
}

.bean-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin: 0.75rem 0;
    padding: 0.75rem 0.9rem;
    background: var(--surface-subtle);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

.bean-summary-name {
    color: var(--text);
    font-size: 0.875rem;
    font-weight: 650;
}

.bean-summary-meta {
    margin-top: 0.15rem;
    color: var(--text-muted);
    font-size: 0.75rem;
}

.settings-note {
    color: var(--text-muted);
    font-size: 0.78rem;
}

.dashboard-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 1.25rem 0 1.5rem;
}

.dashboard-stat {
    min-width: 0;
    padding: 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
}

.dashboard-stat-label {
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 650;
    letter-spacing: 0.045em;
    text-transform: uppercase;
}

.dashboard-stat-value {
    margin-top: 0.2rem;
    color: var(--text);
    font-size: 1.4rem;
    font-weight: 700;
    line-height: 1.3;
    letter-spacing: -0.025em;
}

.history-count {
    margin: 0.25rem 0 0.75rem;
    color: var(--text-muted);
    font-size: 0.78rem;
}

.history-shot-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
}

.history-shot-bean {
    min-width: 0;
    color: var(--text);
    font-size: 0.9rem;
    font-weight: 650;
    overflow-wrap: anywhere;
}

.history-shot-date {
    flex: 0 0 auto;
    color: var(--text-muted);
    font-size: 0.75rem;
}

.history-metrics {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    margin-bottom: 0.75rem;
    background: var(--surface-subtle);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

.history-metric {
    min-width: 0;
    padding: 0.75rem 0.85rem;
}

.history-metric + .history-metric {
    border-left: 1px solid var(--border);
}

.history-metric-label {
    color: var(--text-muted);
    font-size: 0.66rem;
    font-weight: 650;
    letter-spacing: 0.045em;
    text-transform: uppercase;
}

.history-metric-value {
    margin-top: 0.15rem;
    color: var(--text);
    font-size: 1.1rem;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: -0.02em;
}

.history-metric-change {
    margin-top: 0.15rem;
    color: var(--text-muted);
    font-size: 0.72rem;
    line-height: 1.25;
}

.shot-summary {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.45rem 0.75rem;
    margin-bottom: 0.9rem;
}

.shot-recipe {
    color: var(--text);
    font-size: 0.875rem;
    font-weight: 600;
}

.shot-rating {
    color: var(--text-muted);
    font-size: 0.82rem;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    min-height: 24px;
    padding: 0 0.55rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 650;
}

.status-on-target {
    background: var(--success-soft);
    color: var(--success);
}

.status-off-target {
    background: var(--warning-soft);
    color: var(--warning);
}

.status-neutral {
    background: var(--surface-muted);
    color: var(--text-muted);
}

.prop-grid {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 0.55rem 1rem;
    margin: 0.25rem 0 1rem;
}

.prop-label {
    color: var(--text-muted);
    font-size: 0.8rem;
}

.prop-value {
    min-width: 0;
    color: var(--text);
    font-size: 0.85rem;
    overflow-wrap: anywhere;
}

.delete-divider {
    height: 1px;
    margin: 1rem 0 0.75rem;
    background: var(--border);
}

[data-testid="stExpander"] [data-testid="stButton"] button {
    color: var(--danger) !important;
    background: transparent !important;
    border-color: var(--border) !important;
}

.empty-state {
    padding: 2.5rem 1rem;
    color: var(--text-muted);
    text-align: center;
    background: var(--surface);
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius);
    font-size: 0.875rem;
}

.chart-label {
    margin-bottom: 0.25rem;
    color: var(--text);
    font-size: 0.85rem;
    font-weight: 650;
}

[data-testid="stAlert"] {
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

hr {
    margin: 1.25rem 0 !important;
    border: 0 !important;
    border-top: 1px solid var(--border) !important;
}

@media (max-width: 640px) {
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stDeployButton {
        display: none !important;
    }

    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        padding: calc(env(safe-area-inset-top) + 1rem) 0.85rem 2.5rem;
    }

    .app-header {
        margin-bottom: 0.45rem;
    }

    .page-subtitle {
        display: none;
    }

    .section-header {
        margin-top: 1.1rem;
        font-size: 1.15rem;
    }

    .section-copy {
        margin-bottom: 1rem;
    }

    .history-shot-header {
        display: block;
        margin-bottom: 0.7rem;
    }

    .history-shot-date {
        margin-top: 0.15rem;
    }

    .history-metric {
        padding: 0.65rem 0.45rem;
    }

    .history-metric-label {
        font-size: 0.58rem;
    }

    .history-metric-value {
        font-size: 0.95rem;
    }

    .history-metric-change {
        font-size: 0.62rem;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 1rem;
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        height: 40px;
    }

    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.35rem !important;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 100% !important;
    }

    [data-testid="stButton"] button,
    [data-testid="stPopover"] button,
    [data-testid="stFormSubmitButton"] button {
        min-height: 44px;
    }

    .dashboard-stats {
        gap: 0.4rem;
    }

    .dashboard-stat {
        padding: 0.75rem 0.6rem;
    }

    .dashboard-stat-label {
        min-height: 1.85rem;
        font-size: 0.6rem;
    }

    .dashboard-stat-value {
        font-size: 1.05rem;
    }

    .bean-summary {
        align-items: flex-start;
    }

    .prop-grid {
        grid-template-columns: 1fr;
        gap: 0.1rem;
    }

    .prop-label {
        margin-top: 0.55rem;
        font-size: 0.72rem;
        font-weight: 650;
    }

    .prop-label:first-child {
        margin-top: 0;
    }

    input, textarea, select {
        font-size: 16px !important;
    }
}
</style>
""")

st.markdown(
    f"""
    <div class="app-header">
        <div class="app-mark">
            <img src="data:image/svg+xml;base64,{base64.b64encode(COFFEE_SVG.format(size=22).encode()).decode()}" width="22" height="22" alt="">
        </div>
        <div>
            <div class="page-title">Zach's Espresso Tracker</div>
            <div class="page-subtitle">Dial in, log, and learn from every shot.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

shots, load_error, skipped_rows = load_data()
saved_beans = get_saved_beans(shots)
last_shot = shots[0] if shots else {}

target_ratio = st.session_state.target_ratio
rated = [s.get("rating") for s in shots if s.get("rating")]
ratios = [
    ratio
    for shot in shots
    if (ratio := brew_ratio(shot.get("yield"), shot.get("dose"))) is not None
]
avg_rating = f"{sum(rated) / len(rated):.1f} / 10" if rated else "—"
avg_ratio = f"{sum(ratios) / len(ratios):.2f}:1" if ratios else "—"

if load_error:
    st.error(f"{load_error} Logging and deletion are disabled until it reconnects.")
elif skipped_rows:
    st.warning(f"Skipped {skipped_rows} unreadable database row{'s' if skipped_rows != 1 else ''}.")

if "save_success" in st.session_state:
    save_message = st.session_state.pop("save_success")
    st.success(save_message)
    st.toast(save_message)

log_tab, history_tab, insights_tab = st.tabs(["Log Shot", "History", "Insights"])

with log_tab:
    st.markdown('<div class="section-header">Log a New Shot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Capture the recipe, then add what you tasted.</div>',
        unsafe_allow_html=True,
    )

    bean_options = ["New bean"] + list(saved_beans.keys())
    if "pending_quick_log_bean" in st.session_state:
        pending_bean = st.session_state.pop("pending_quick_log_bean")
        matched_bean = saved_bean_name(saved_beans, pending_bean)
        if matched_bean:
            st.session_state.selected_bean = matched_bean
    elif "selected_bean" in st.session_state:
        selected_value = st.session_state.selected_bean
        if selected_value != "New bean":
            matched_bean = saved_bean_name(saved_beans, selected_value)
            if matched_bean:
                st.session_state.selected_bean = matched_bean
            else:
                st.session_state.selected_bean = bean_options[1] if saved_beans else "New bean"
    else:
        st.session_state.selected_bean = bean_options[1] if saved_beans else "New bean"

    bean_col, settings_col = st.columns([3, 1])
    with bean_col:
        selected_bean = st.selectbox("Bean", bean_options, key="selected_bean")
    with settings_col:
        with st.popover("Logging settings", width="stretch"):
            st.markdown(
                '<div class="settings-note">Used for ratio guidance and the target line in Insights.</div>',
                unsafe_allow_html=True,
            )
            st.session_state.target_ratio = st.number_input(
                "Target Brew Ratio",
                min_value=1.0,
                max_value=4.0,
                step=0.1,
                value=st.session_state.target_ratio,
                help="A 1:2 ratio means 18g in and 36g out.",
            )

    target_ratio = st.session_state.target_ratio
    is_new_bean = selected_bean == "New bean"

    if selected_bean != "New bean":
        bean_data = saved_beans[selected_bean]
        default_name = selected_bean
        default_roaster = normalize_text(bean_data.get("roaster"))
        default_origin = normalize_text(bean_data.get("origin"))
        default_roast_level = normalize_text(bean_data.get("roast_level")) or "Light"
        default_process = normalize_text(bean_data.get("process_method")) or "Washed"
        try:
            default_roast_date = date.fromisoformat(bean_data.get("roast_date"))
        except (TypeError, ValueError):
            default_roast_date = date.today()
    else:
        default_name = ""
        default_roaster = ""
        default_origin = ""
        default_roast_level = "Light"
        default_process = "Washed"
        default_roast_date = date.today()

    if not is_new_bean:
        bean_meta = " · ".join(
            value for value in (default_roaster, default_origin, default_process) if value
        )
        st.markdown(
            '<div class="bean-summary"><div>'
            f'<div class="bean-summary-name">{html.escape(selected_bean)}</div>'
            f'<div class="bean-summary-meta">{html.escape(bean_meta or "Saved bean details")}</div>'
            '</div><span class="settings-note">Details reused automatically</span></div>',
            unsafe_allow_html=True,
        )

    with st.form("shot_form"):
            if is_new_bean:
                st.markdown('<div class="subsection-label">Bean Details</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    bean_name = st.text_input("Bean Name", value=default_name, placeholder="Ethiopia Yirgacheffe")
                    origin = st.text_input("Origin", value=default_origin, placeholder="Yirgacheffe, Ethiopia")
                    roast_date = st.date_input("Roast Date", value=default_roast_date)
                with col2:
                    roaster = st.text_input("Roaster", value=default_roaster, placeholder="Roaster name")
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
            else:
                with st.expander("Edit bean details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        bean_name = st.text_input("Bean Name", value=default_name)
                        origin = st.text_input("Origin", value=default_origin)
                        roast_date = st.date_input("Roast Date", value=default_roast_date)
                    with col2:
                        roaster = st.text_input("Roaster", value=default_roaster)
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

            st.markdown('<div class="subsection-label">Recipe</div>', unsafe_allow_html=True)
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                dose = st.number_input(
                    "Dose (g)",
                    min_value=0.0,
                    max_value=30.0,
                    step=0.1,
                    value=widget_default(last_shot.get("dose"), 18.0, 0.0, 30.0),
                )
            with row1_col2:
                yield_ = st.number_input(
                    "Yield (g)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    value=widget_default(last_shot.get("yield"), 36.0, 0.0, 100.0),
                )

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                brew_time = st.number_input(
                    "Brew Time (s)",
                    min_value=0,
                    max_value=120,
                    step=1,
                    value=widget_default(
                        last_shot.get("brew_time"),
                        28,
                        0,
                        120,
                        integer=True,
                    ),
                )
            with row2_col2:
                temperature = st.number_input(
                    "Temperature (°C)",
                    min_value=80.0,
                    max_value=100.0,
                    step=0.5,
                    value=widget_default(
                        last_shot.get("temperature"),
                        93.0,
                        80.0,
                        100.0,
                    ),
                )

            row3_col1, row3_col2 = st.columns(2)
            with row3_col1:
                grind_size = st.text_input(
                    "Grind Size",
                    value=last_shot.get("grind_size") or "",
                    placeholder="11 or 2.5 turns",
                )
            with row3_col2:
                grind_direction = st.selectbox("Adjustment vs Last Shot", GRIND_DIRECTIONS)

            st.markdown('<div class="subsection-label">Taste</div>', unsafe_allow_html=True)
            rating = st.select_slider("Score", options=list(range(1, 11)), value=6)
            tasting_notes = st.text_area(
                "Tasting Notes",
                placeholder="Sweetness, acidity, body, finish, and flavors",
            )
            submitted = st.form_submit_button(
                "Log Shot",
                width="stretch",
                disabled=load_error is not None,
            )

    if submitted:
        normalized_bean_name = normalize_text(bean_name)
        if load_error:
            st.error("Reconnect to the database before logging a shot.")
        elif not normalized_bean_name:
            error_message = "Add a bean name before logging this shot."
            st.error(error_message)
            st.toast(error_message, icon=":material/warning:")
        elif not dose:
            error_message = "Dose must be greater than zero."
            st.error(error_message)
            st.toast(error_message, icon=":material/warning:")
        else:
            try:
                save_shot({
                    "date": date.today().strftime("%Y-%m-%d"),
                    "bean_name": normalized_bean_name,
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
            except requests.RequestException as error:
                detail = "Check the Supabase connection and table permissions."
                if error.response is not None:
                    try:
                        payload = error.response.json()
                        detail = payload.get("message") or payload.get("hint") or detail
                    except ValueError:
                        pass
                error_message = f"Could not log the shot. {detail}"
                st.error(error_message)
                st.toast("The shot was not saved.", icon=":material/warning:")
            else:
                ratio = yield_ / dose
                flag = ratio_flag(yield_, dose, target_ratio)
                st.session_state.save_success = (
                    f"Shot logged. Brew ratio: {ratio:.2f}:1 — {flag}"
                )
                st.session_state.pending_quick_log_bean = normalized_bean_name
                st.rerun()

with history_tab:
    st.markdown('<div class="section-header">Shot History</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Review recipes and compare adjustments shot by shot.</div>',
        unsafe_allow_html=True,
    )

    if load_error:
        st.markdown(
            '<div class="empty-state">Shot history is unavailable until the database reconnects.</div>',
            unsafe_allow_html=True,
        )
    elif not shots:
        st.markdown(
            '<div class="empty-state">Your first shot will appear here after you log it.</div>',
            unsafe_allow_html=True,
        )
    else:
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            history_search = st.text_input(
                "Search history",
                placeholder="Search beans, roasters, origins, or tasting notes",
            )
        with filter_col2:
            bean_filter = st.selectbox("Filter by bean", ["All beans"] + list(saved_beans.keys()))

        filtered_shots = shots
        if bean_filter != "All beans":
            filter_key = bean_key(bean_filter)
            filtered_shots = [
                shot for shot in filtered_shots
                if bean_key(shot.get("bean_name")) == filter_key
            ]
        if history_search:
            query = history_search.casefold()
            filtered_shots = [
                shot for shot in filtered_shots
                if query in " ".join(
                    str(shot.get(field) or "")
                    for field in ("bean_name", "roaster", "origin", "tasting_notes")
                ).casefold()
            ]

        st.markdown(
            f'<div class="history-count">Showing {len(filtered_shots)} of {len(shots)} shots</div>',
            unsafe_allow_html=True,
        )
        if not filtered_shots:
            st.info("No shots match those filters.")

        previous_shots_by_id = get_previous_shots_by_id(shots)

        for shot in filtered_shots:
            shot_date_display = display_date(shot.get("date"))
            shot_yield = shot.get("yield")
            shot_dose = shot.get("dose")
            ratio = brew_ratio(shot_yield, shot_dose)
            ratio_display = f"{ratio:.2f}:1" if ratio is not None else "Ratio unavailable"
            flag = ratio_flag(shot_yield, shot_dose, target_ratio)
            score_display = score_text(shot.get("rating"))
            badge_cls = ratio_badge_class(flag) if flag else "status-neutral"
            if flag == "On target":
                short_flag = "On target"
            elif "Over" in flag:
                short_flag = "Over"
            elif "Under" in flag:
                short_flag = "Under"
            else:
                short_flag = "—"
            previous_shot = previous_shots_by_id.get(shot.get("id"))
            shot_bean = shot.get("bean_name") or "Unknown bean"

            with st.container(border=True):
                st.markdown(
                    '<div class="history-shot-header">'
                    f'<div class="history-shot-bean">{html.escape(shot_bean)}</div>'
                    f'<div class="history-shot-date">{html.escape(shot_date_display)}</div>'
                    '</div>'
                    f'{history_metric_grid(shot, previous_shot)}',
                    unsafe_allow_html=True,
                )

                with st.expander(
                    f"{shot_bean} · {shot_date_display} · {ratio_display}",
                    expanded=False,
                ):
                    st.markdown(
                        '<div class="shot-summary">'
                        f'<span class="status-pill {badge_cls}">{html.escape(short_flag)}</span>'
                        f'<span class="shot-recipe">{html.escape(ratio_display)}</span>'
                        f'<span class="shot-rating">{html.escape(score_display)}</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    shot_temp = shot.get("temperature")
                    temperature_display = f"{fmt(shot_temp)}°C" if shot_temp is not None else "—"
                    shot_roast = shot.get("roast_level")
                    shot_process = shot.get("process_method")
                    coffee_display = " · ".join(
                        value for value in (shot_roast, shot_process) if value
                    ) or "—"
                    st.markdown(
                        shot_prop_grid([
                            ("Grind Size", shot.get("grind_size") or "—"),
                            ("Direction", shot.get("grind_direction") or "—"),
                            ("Temperature", temperature_display),
                            ("Coffee", coffee_display),
                            ("Tasting Notes", shot.get("tasting_notes") or "—"),
                            ("Roaster", shot.get("roaster") or "—"),
                            ("Origin", shot.get("origin") or "—"),
                            ("Roast Date", shot.get("roast_date") or "—"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown('<div class="delete-divider"></div>', unsafe_allow_html=True)
                    with st.popover(f"Delete {shot_bean} shot"):
                        st.caption("This permanently removes the shot.")
                        shot_id = shot.get("id")
                        if shot_id is None:
                            st.caption("This shot cannot be deleted because its ID is unavailable.")
                        elif st.button(
                            f"Delete {shot_bean} shot from {shot_date_display}",
                            key=f"del_{shot_id}",
                            type="primary",
                        ):
                            if delete_shot(shot_id):
                                st.rerun()

with insights_tab:
    st.markdown('<div class="section-header">Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">See how your recipe and results change over time.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="dashboard-stats">
            <div class="dashboard-stat">
                <div class="dashboard-stat-label">Shots Logged</div>
                <div class="dashboard-stat-value">{len(shots)}</div>
            </div>
            <div class="dashboard-stat">
                <div class="dashboard-stat-label">Average Score</div>
                <div class="dashboard-stat-value">{html.escape(avg_rating)}</div>
            </div>
            <div class="dashboard-stat">
                <div class="dashboard-stat-label">Average Ratio</div>
                <div class="dashboard-stat-value">{html.escape(avg_ratio)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if load_error:
        st.markdown(
            '<div class="empty-state">Insights are unavailable until the database reconnects.</div>',
            unsafe_allow_html=True,
        )
    elif not shots:
        st.markdown(
            '<div class="empty-state">Trends will appear once you have shots to compare.</div>',
            unsafe_allow_html=True,
        )
    else:
        df = pd.DataFrame(shots).reindex(columns=SHOT_FIELDS)
        df = df[::-1].reset_index(drop=True)
        for column in ("dose", "yield", "brew_time", "rating"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        ratio_df = df[df["date"].notna() & df["dose"].gt(0) & df["yield"].notna()].copy()
        ratio_df["Brew Ratio"] = ratio_df["yield"] / ratio_df["dose"]
        brew_time_df = df[df["date"].notna() & df["brew_time"].notna()].copy()
        rating_df = df[df["date"].notna() & df["rating"].notna()].copy()

        if ratio_df.empty and brew_time_df.empty and rating_df.empty:
            st.markdown(
                '<div class="empty-state">No valid recipe data is available for trends.</div>',
                unsafe_allow_html=True,
            )
        else:
            if not ratio_df.empty:
                with st.container(border=True):
                    st.markdown('<div class="chart-label">Brew Ratio</div>', unsafe_allow_html=True)
                    ratio_chart = trend_line_chart(ratio_df, "Brew Ratio", "Brew Ratio")
                    target_line = alt.Chart(pd.DataFrame({"target": [target_ratio]})).mark_rule(
                        color="#8A4B32",
                        strokeDash=[5, 5],
                    ).encode(y="target:Q")
                    st.altair_chart(ratio_chart + target_line, width="stretch")

            if not brew_time_df.empty:
                with st.container(border=True):
                    st.markdown('<div class="chart-label">Brew Time</div>', unsafe_allow_html=True)
                    st.altair_chart(
                        trend_line_chart(
                            brew_time_df,
                            "brew_time",
                            "Brew Time",
                            color="#376A8A",
                        ),
                        width="stretch",
                    )

            if not rating_df.empty:
                with st.container(border=True):
                    st.markdown('<div class="chart-label">Score</div>', unsafe_allow_html=True)
                    st.altair_chart(
                        trend_line_chart(
                            rating_df,
                            "rating",
                            "Score",
                            color="#A76D28",
                            y_domain=[1, 10],
                            tooltip_format=".0f",
                        ),
                        width="stretch",
                    )
