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
    response = requests.post(
        get_url(),
        headers={**get_headers(), "Prefer": "return=minimal"},
        json=row,
        timeout=15,
    )
    response.raise_for_status()


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
        return "status-on-target"
    return "status-off-target"


def shot_prop_grid(rows):
    items = "".join(
        f'<div class="prop-label">{html.escape(str(label))}</div>'
        f'<div class="prop-value">{html.escape(str(value))}</div>'
        for label, value in rows
    )
    return f'<div class="prop-grid">{items}</div>'


def trend_line_chart(dataframe, value_column, label, color="#2F6B57"):
    chart_df = dataframe[["date", value_column, "bean_name"]].dropna().copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"])
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
            scale=alt.Scale(zero=False),
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
            alt.Tooltip(f"{value_column}:Q", title=label, format=".2f"),
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

html, body, [class*="css"] {
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

shots = load_data()
saved_beans = get_saved_beans(shots)

target_ratio = st.session_state.target_ratio
rated = [s["rating"] for s in shots if s.get("rating")]
ratios = [s["yield"] / s["dose"] for s in shots if s.get("dose")]
avg_rating = f"{sum(rated) / len(rated):.1f} / 5" if rated else "—"
avg_ratio = f"{sum(ratios) / len(ratios):.2f}:1" if ratios else "—"

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
        if pending_bean in bean_options:
            st.session_state.selected_bean = pending_bean
    elif (
        "selected_bean" not in st.session_state
        or st.session_state.selected_bean not in bean_options
    ):
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
                grind_size = st.text_input("Grind Size", placeholder="11 or 2.5 turns")
            with row3_col2:
                grind_direction = st.selectbox("Adjustment vs Last Shot", GRIND_DIRECTIONS)

            st.markdown('<div class="subsection-label">Taste</div>', unsafe_allow_html=True)
            rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=3)
            tasting_notes = st.text_area(
                "Tasting Notes",
                placeholder="Sweetness, acidity, body, finish, and flavors",
            )
            submitted = st.form_submit_button("Log Shot", width="stretch")

    if submitted:
        if not bean_name.strip():
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
                    "bean_name": bean_name.strip(),
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
                st.session_state.pending_quick_log_bean = bean_name.strip()
                st.rerun()

with history_tab:
    st.markdown('<div class="section-header">Shot History</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Review recipes and compare adjustments shot by shot.</div>',
        unsafe_allow_html=True,
    )

    if not shots:
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
            filtered_shots = [shot for shot in filtered_shots if shot["bean_name"] == bean_filter]
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

        for shot in filtered_shots:
            display_date = date.fromisoformat(shot["date"]).strftime("%b %d, %Y").replace(" 0", " ")
            ratio = shot["yield"] / shot["dose"] if shot["dose"] else 0
            flag = ratio_flag(shot["yield"], shot["dose"], target_ratio)
            rating_stars = star_rating(shot.get("rating"))
            badge_cls = ratio_badge_class(flag) if flag else "status-neutral"
            if flag == "On target":
                short_flag = "On target"
            elif "Over" in flag:
                short_flag = "Over"
            elif "Under" in flag:
                short_flag = "Under"
            else:
                short_flag = "—"
            label = f"{display_date} · {shot['bean_name']}"
            recipe_summary = (
                f"{fmt(shot['dose'])}g in → {fmt(shot['yield'])}g out · "
                f"{shot['brew_time']}s · {ratio:.2f}:1"
            )

            with st.expander(label, expanded=False):
                st.markdown(
                    '<div class="shot-summary">'
                    f'<span class="status-pill {badge_cls}">{html.escape(short_flag)}</span>'
                    f'<span class="shot-recipe">{html.escape(recipe_summary)}</span>'
                    f'<span class="shot-rating">{html.escape(rating_stars)}</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    shot_prop_grid([
                        ("Grind Size", shot["grind_size"] or "—"),
                        ("Direction", shot.get("grind_direction") or "—"),
                        ("Temperature", f"{shot['temperature']}°C"),
                        ("Coffee", f"{shot['roast_level']} · {shot['process_method']}"),
                        ("Tasting Notes", shot.get("tasting_notes") or "—"),
                        ("Roaster", shot["roaster"] or "—"),
                        ("Origin", shot["origin"] or "—"),
                        ("Roast Date", shot["roast_date"]),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="delete-divider"></div>', unsafe_allow_html=True)
                with st.popover("Delete shot"):
                    st.caption("This permanently removes the shot.")
                    if st.button("Delete permanently", key=f"del_{shot['id']}", type="primary"):
                        delete_shot(shot["id"])
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
                <div class="dashboard-stat-label">Average Rating</div>
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

    if not shots:
        st.markdown(
            '<div class="empty-state">Trends will appear once you have shots to compare.</div>',
            unsafe_allow_html=True,
        )
    else:
        df = pd.DataFrame(shots)
        df = df[::-1].reset_index(drop=True)
        df["Brew Ratio"] = df["yield"] / df["dose"]

        with st.container(border=True):
            st.markdown('<div class="chart-label">Brew Ratio</div>', unsafe_allow_html=True)
            ratio_chart = trend_line_chart(df, "Brew Ratio", "Brew Ratio")
            target_line = alt.Chart(pd.DataFrame({"target": [target_ratio]})).mark_rule(
                color="#8A4B32",
                strokeDash=[5, 5],
            ).encode(y="target:Q")
            st.altair_chart(ratio_chart + target_line, width="stretch")

        with st.container(border=True):
            st.markdown('<div class="chart-label">Brew Time</div>', unsafe_allow_html=True)
            st.altair_chart(
                trend_line_chart(df, "brew_time", "Brew Time", color="#376A8A"),
                width="stretch",
            )

        if df["rating"].notna().any():
            with st.container(border=True):
                st.markdown('<div class="chart-label">Rating</div>', unsafe_allow_html=True)
                st.altair_chart(
                    trend_line_chart(df, "rating", "Rating", color="#A76D28"),
                    width="stretch",
                )
