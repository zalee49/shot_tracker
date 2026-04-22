import streamlit as st
import pandas as pd
import os
from datetime import date

DATA_FILE = "shot_log.csv"

COLUMNS = [
    "Date", "Bean Name", "Roaster", "Origin", "Roast Level",
    "Process Method", "Roast Date", "Dose (g)", "Yield (g)",
    "Brew Time (s)", "Grind Size", "Temperature (°C)", "Tasting Notes"
]


def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=COLUMNS)


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def get_saved_beans(df):
    if df.empty:
        return {}
    bean_cols = ["Bean Name", "Roaster", "Origin", "Roast Level", "Process Method", "Roast Date"]
    beans = df[bean_cols].drop_duplicates(subset=["Bean Name"]).set_index("Bean Name")
    return beans.to_dict(orient="index")


st.title("Espresso Shot Tracker")
st.subheader("Log a New Shot")

df = load_data()
saved_beans = get_saved_beans(df)

bean_options = ["-- New Bean --"] + list(saved_beans.keys())
selected_bean = st.selectbox("Select a Bean or Add New", bean_options)

if selected_bean != "-- New Bean --":
    bean_data = saved_beans[selected_bean]
    default_name = selected_bean
    default_roaster = bean_data["Roaster"]
    default_origin = bean_data["Origin"]
    default_roast_level = bean_data["Roast Level"]
    default_process = bean_data["Process Method"]
    try:
        default_roast_date = date.fromisoformat(str(bean_data["Roast Date"]))
    except Exception:
        default_roast_date = date.today()
else:
    default_name = ""
    default_roaster = ""
    default_origin = ""
    default_roast_level = "Light"
    default_process = "Washed"
    default_roast_date = date.today()

roast_levels = ["Light", "Medium", "Medium-Dark", "Dark"]
process_methods = ["Washed", "Natural", "Honey", "Other"]

with st.form("shot_form"):
    st.markdown("**Bean Info**")
    col1, col2 = st.columns(2)
    with col1:
        bean_name = st.text_input("Bean Name", value=default_name, placeholder="e.g. Ethiopia Yirgacheffe")
        origin = st.text_input("Origin", value=default_origin, placeholder="e.g. Ethiopia, Yirgacheffe")
        roast_level = st.selectbox("Roast Level", roast_levels, index=roast_levels.index(default_roast_level))
    with col2:
        roaster = st.text_input("Roaster", value=default_roaster, placeholder="e.g. Blue Bottle")
        process_method = st.selectbox("Process Method", process_methods, index=process_methods.index(default_process))
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
    df = load_data()
    new_row = {
        "Date": date.today().strftime("%Y-%m-%d"),
        "Bean Name": bean_name,
        "Roaster": roaster,
        "Origin": origin,
        "Roast Level": roast_level,
        "Process Method": process_method,
        "Roast Date": roast_date.strftime("%Y-%m-%d"),
        "Dose (g)": dose,
        "Yield (g)": yield_,
        "Brew Time (s)": brew_time,
        "Grind Size": grind_size,
        "Temperature (°C)": temperature,
        "Tasting Notes": tasting_notes,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.success("Shot logged successfully!")

st.markdown("---")
st.subheader("Shot History")

df = load_data()

if df.empty:
    st.info("No shots logged yet. Fill in the form above to log your first shot!")
else:
    header = st.columns([1.2, 1.8, 0.8, 0.8, 0.8, 0.8, 0.6])
    for col, label in zip(header, ["Date", "Bean", "Dose", "Yield", "Time", "Grind", ""]):
        col.markdown(f"**{label}**")

    for orig_idx, row in df[::-1].iterrows():
        cols = st.columns([1.2, 1.8, 0.8, 0.8, 0.8, 0.8, 0.6])
        cols[0].write(row["Date"])
        cols[1].write(row["Bean Name"])
        cols[2].write(f"{row['Dose (g)']}g")
        cols[3].write(f"{row['Yield (g)']}g")
        cols[4].write(f"{row['Brew Time (s)']}s")
        cols[5].write(str(row["Grind Size"]))
        if cols[6].button("Delete", key=f"del_{orig_idx}"):
            df = df.drop(index=orig_idx).reset_index(drop=True)
            save_data(df)
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Trends")

    col5, col6 = st.columns(2)
    with col5:
        st.markdown("**Brew Ratio Over Time** (Yield / Dose)")
        df["Brew Ratio"] = df["Yield (g)"] / df["Dose (g)"]
        st.line_chart(df["Brew Ratio"])
    with col6:
        st.markdown("**Brew Time Over Time**")
        st.line_chart(df["Brew Time (s)"])
