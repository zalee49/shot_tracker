import streamlit as st
import pandas as pd
import requests
from datetime import date

ROAST_LEVELS = ["Light", "Medium", "Medium-Dark", "Dark"]
PROCESS_METHODS = ["Washed", "Natural", "Honey", "Other"]
GRIND_DIRECTIONS = ["First shot with this grind", "Same", "Coarser", "Finer"]


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


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px; flex-wrap: nowrap;">
    <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0;">
        <ellipse cx="24" cy="24" rx="14" ry="20" fill="#6F4E37"/>
        <path d="M24 6 C29 13 29 21 24 28 C19 35 19 40 24 42"
              stroke="#3E1F00" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    </svg>
    <span style="font-size: 2.2rem; font-weight: bold; color: #3E1F00; font-family: Georgia, serif; white-space: nowrap;">Zach's Espresso Shot Tracker</span>
</div>
""", unsafe_allow_html=True)

shots = load_data()
saved_beans = get_saved_beans(shots)

# ── Settings ─────────────────────────────────────────────────────────────────
with st.expander("Settings"):
    if "target_ratio" not in st.session_state:
        st.session_state.target_ratio = 2.0
    st.session_state.target_ratio = st.number_input(
        "Target Brew Ratio (Yield / Dose)",
        min_value=1.0, max_value=4.0, step=0.1,
        value=st.session_state.target_ratio,
        help="A 1:2 ratio means 18g dose produces 36g yield"
    )
target_ratio = st.session_state.target_ratio

st.markdown("---")

# ── Log Mode ─────────────────────────────────────────────────────────────────
quick_mode = st.checkbox("Quick Log Mode", value=True)
st.subheader("Log a New Shot")

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

if quick_mode and not default_name:
    st.warning("Select a bean above to use Quick Log Mode, or uncheck it to log a new bean.")
else:
    with st.form("shot_form"):
        if not quick_mode:
            st.markdown("**Bean Info**")
            bean_name = st.text_input("Bean Name", value=default_name, placeholder="e.g. Ethiopia Yirgacheffe")
            roaster = st.text_input("Roaster", value=default_roaster, placeholder="e.g. Blue Bottle")
            origin = st.text_input("Origin", value=default_origin, placeholder="e.g. Ethiopia, Yirgacheffe")
            roast_level = st.selectbox("Roast Level", ROAST_LEVELS, index=ROAST_LEVELS.index(default_roast_level))
            process_method = st.selectbox("Process Method", PROCESS_METHODS, index=PROCESS_METHODS.index(default_process))
            roast_date = st.date_input("Roast Date", value=default_roast_date)
            st.markdown("---")
            st.markdown("**Shot Parameters**")
        else:
            bean_name = default_name
            roaster = default_roaster
            origin = default_origin
            roast_level = default_roast_level
            process_method = default_process
            roast_date = default_roast_date

        dose = st.number_input("Dose (g)", min_value=0.0, max_value=30.0, step=0.1, value=18.0)
        yield_ = st.number_input("Yield (g)", min_value=0.0, max_value=100.0, step=0.1, value=36.0)
        brew_time = st.number_input("Brew Time (s)", min_value=0, max_value=120, step=1, value=28)
        grind_size = st.text_input("Grind Size", placeholder="e.g. 11, or 2.5 turns")
        grind_direction = st.selectbox("Grind Direction vs Last Shot", GRIND_DIRECTIONS)
        temperature = st.number_input("Temperature (°C)", min_value=80.0, max_value=100.0, step=0.5, value=93.0)
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

# ── Shot History ──────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Shot History")

if not shots:
    st.info("No shots logged yet. Fill in the form above to log your first shot!")
else:
    for shot in shots:
        display_date = date.fromisoformat(shot["date"]).strftime("%m/%d/%y")
        ratio = shot["yield"] / shot["dose"] if shot["dose"] else 0
        flag = ratio_flag(shot["yield"], shot["dose"], target_ratio)
        rating_stars = star_rating(shot.get("rating"))
        label = (
            f"{display_date} — {shot['bean_name']}  |  "
            f"{fmt(shot['dose'])}g → {fmt(shot['yield'])}g · "
            f"{shot['brew_time']}s · {rating_stars}"
        )
        with st.expander(label):
            st.markdown(f"**Brew Ratio:** {ratio:.2f}:1 — {flag}")
            st.markdown(f"**Grind Size:** {shot['grind_size'] or '—'}  |  **Direction:** {shot.get('grind_direction') or '—'}")
            st.markdown(f"**Temperature:** {shot['temperature']}°C")
            st.markdown(f"**Tasting Notes:** {shot.get('tasting_notes') or '—'}")
            st.markdown("---")
            st.markdown(f"**Roaster:** {shot['roaster'] or '—'}  |  **Origin:** {shot['origin'] or '—'}")
            st.markdown(f"**Roast Level:** {shot['roast_level']}  |  **Process:** {shot['process_method']}  |  **Roast Date:** {shot['roast_date']}")
            if st.button("Delete", key=f"del_{shot['id']}"):
                delete_shot(shot["id"])
                st.rerun()

    # ── Trends ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Trends")

    df = pd.DataFrame(shots)
    df = df[::-1].reset_index(drop=True)
    df["Brew Ratio"] = df["yield"] / df["dose"]

    st.markdown("**Brew Ratio Over Time**")
    st.line_chart(df["Brew Ratio"])

    st.markdown("**Brew Time Over Time**")
    st.line_chart(df["brew_time"])

    if df["rating"].notna().any():
        st.markdown("**Rating Over Time**")
        st.line_chart(df["rating"].dropna())
