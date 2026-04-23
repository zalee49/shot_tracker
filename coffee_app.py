import streamlit as st
import pandas as pd
import requests
from datetime import date

ROAST_LEVELS = ["Light", "Medium", "Medium-Dark", "Dark"]
PROCESS_METHODS = ["Washed", "Natural", "Honey", "Other"]


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


st.markdown("""
<style>
    .stApp {
        background-color: #FDF6EC;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #3E1F00 !important;
        font-family: Georgia, serif;
    }
    p, label, div, span, .stMarkdown {
        color: #3E1F00 !important;
    }
    .stButton > button {
        background-color: #6F4E37;
        color: #FDF6EC;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #3E1F00;
        color: #FDF6EC;
    }
    .stForm {
        background-color: #F5E6D3;
        border-radius: 10px;
        padding: 16px;
    }
    .stExpander {
        background-color: #F5E6D3;
        border: 1px solid #C8A882;
        border-radius: 8px;
    }
    .stSelectbox label, .stTextInput label, .stNumberInput label,
    .stTextArea label, .stDateInput label {
        color: #3E1F00;
        font-weight: bold;
    }
    hr {
        border-color: #C8A882;
    }
</style>
""", unsafe_allow_html=True)

st.title("Zach's Espresso Shot Tracker")
st.subheader("Log a New Shot")

shots = load_data()
saved_beans = get_saved_beans(shots)

bean_options = ["-- New Bean --"] + list(saved_beans.keys())
selected_bean = st.selectbox("Select a Bean or Add New", bean_options)

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

with st.form("shot_form"):
    st.markdown("**Bean Info**")
    col1, col2 = st.columns(2)
    with col1:
        bean_name = st.text_input("Bean Name", value=default_name, placeholder="e.g. Ethiopia Yirgacheffe")
        origin = st.text_input("Origin", value=default_origin, placeholder="e.g. Ethiopia, Yirgacheffe")
        roast_level = st.selectbox("Roast Level", ROAST_LEVELS, index=ROAST_LEVELS.index(default_roast_level))
    with col2:
        roaster = st.text_input("Roaster", value=default_roaster, placeholder="e.g. Blue Bottle")
        process_method = st.selectbox("Process Method", PROCESS_METHODS, index=PROCESS_METHODS.index(default_process))
        roast_date = st.date_input("Roast Date", value=default_roast_date)

    st.markdown("---")
    st.markdown("**Shot Parameters**")
    col3, col4 = st.columns(2)
    with col3:
        dose = st.number_input("Dose (g)", min_value=0.0, max_value=30.0, step=0.1, value=18.0)
        brew_time = st.number_input("Brew Time (s)", min_value=0, max_value=120, step=1, value=28)
        temperature = st.number_input("Temperature (°C)", min_value=80.0, max_value=100.0, step=0.5, value=93.0)
    with col4:
        yield_ = st.number_input("Yield (g)", min_value=0.0, max_value=100.0, step=0.1, value=36.0)
        grind_size = st.text_input("Grind Size", placeholder="e.g. 11, or 2.5 turns")

    st.markdown("---")
    tasting_notes = st.text_area("Tasting Notes", placeholder="e.g. Bright acidity, notes of blueberry and dark chocolate...")

    submitted = st.form_submit_button("Log Shot")

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
        "temperature": temperature,
        "tasting_notes": tasting_notes,
    })
    st.success("Shot logged successfully!")
    st.rerun()

st.markdown("---")
st.subheader("Shot History")

if not shots:
    st.info("No shots logged yet. Fill in the form above to log your first shot!")
else:
    for shot in shots:
        display_date = date.fromisoformat(shot['date']).strftime("%m/%d/%y")
        label = f"{display_date} — {shot['bean_name']}  |  {shot['dose']}g in · {shot['yield']}g out · {shot['brew_time']}s"
        with st.expander(label):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Roaster:** {shot['roaster']}")
                st.write(f"**Origin:** {shot['origin']}")
                st.write(f"**Roast Level:** {shot['roast_level']}")
                st.write(f"**Process Method:** {shot['process_method']}")
                st.write(f"**Roast Date:** {shot['roast_date']}")
            with col2:
                st.write(f"**Grind Size:** {shot['grind_size']}")
                st.write(f"**Temperature:** {shot['temperature']}°C")
                st.write(f"**Brew Ratio:** {shot['yield'] / shot['dose']:.2f}:1")
            st.write(f"**Tasting Notes:** {shot['tasting_notes']}")
            if st.button("Delete", key=f"del_{shot['id']}"):
                delete_shot(shot["id"])
                st.rerun()

    st.markdown("---")
    st.subheader("Trends")

    df = pd.DataFrame(shots)
    df = df[::-1].reset_index(drop=True)

    col5, col6 = st.columns(2)
    with col5:
        st.markdown("**Brew Ratio Over Time** (Yield / Dose)")
        df["Brew Ratio"] = df["yield"] / df["dose"]
        st.line_chart(df["Brew Ratio"])
    with col6:
        st.markdown("**Brew Time Over Time**")
        st.line_chart(df["brew_time"])
