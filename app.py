import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import csv
import os
import winsound  
from plyer import notification
CSV_FILE = "reminders.csv"
ALARM_SOUND = "alarm.wav"  
CATEGORY_COLORS = {
    "College": "#1f77b4", 
    "Personal": "#ff7f0e",
    "Work": "#2ca02c",  
    "Others": "#d62728" 
}
# Setup
st.set_page_config(page_title="ChronoBell", page_icon="🔔", layout="wide")
st.title("Welcome Miru! Ready to plan your day? 🌞")
# Ensure CSV exists
if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task", "datetime", "category", "repeat"])
# Layout columns
col1, col2 = st.columns([1, 2])
# === LEFT: Task Input ===
with col1:
    st.header("Add New Task")
    task = st.text_input("📝 Task Name")
    reminder_date = st.date_input("📅 Date")
    reminder_time = st.time_input("⏰ Time")
    category = st.selectbox("📁 Category", list(CATEGORY_COLORS.keys()))
    repeat = st.selectbox("🔁 Repeat", ["No", "Daily", "Weekly"])
    if st.button("Add Task"):
        full_datetime = f"{reminder_date} {reminder_time.strftime('%H:%M')}"
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([task, full_datetime, category, repeat])
        st.success(f"✅ Task '{task}' scheduled on {full_datetime}")
# === RIGHT: Tabs for Tasks View ===
with col2:
    tab1, tab2 = st.tabs(["📋 All Tasks", "📆 Calendar View"])
    with tab1:
        st.subheader("All Scheduled Tasks")
        try:
            df = pd.read_csv(CSV_FILE)
            if not df.empty:
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
                df = df.sort_values(by="datetime")
                def color_badge(cat):
                    color = CATEGORY_COLORS.get(cat, "gray")
                    return f'<span style="color:white; background-color:{color}; padding:2px 8px; border-radius:10px">{cat}</span>'
                df["Category"] = df["category"].apply(lambda c: color_badge(c))
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("No tasks scheduled.")
        except Exception as e:
            st.error(f"Error reading tasks: {e}")
    with tab2:
        st.subheader("Calendar View")
        try:
            df = pd.read_csv(CSV_FILE)
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            df["date"] = df["datetime"].dt.date
            grouped = df.groupby("date")["task"].apply(list).reset_index()
            for _, row in grouped.iterrows():
                st.markdown(f"### 📅 {row['date']}")
                for t in row["task"]:
                    st.markdown(f"- {t}")
        except:
            st.info("No upcoming events.")
# === Notification Check ===
now = datetime.now().replace(second=0, microsecond=0)
task_triggered = False
updated_rows = []
try:
    df = pd.read_csv(CSV_FILE)
    for _, row in df.iterrows():
        task_time = pd.to_datetime(row["datetime"], errors="coerce")
        repeat = row.get("repeat", "No")
        if pd.isnull(task_time):
            continue
        if now == task_time:
            notification.notify(
                title=f" {row['category']} Reminder!",
                message=row["task"],
                timeout=10
            )
            try:
                if os.path.exists(ALARM_SOUND):
                    winsound.PlaySound(ALARM_SOUND, winsound.SND_FILENAME)
                else:
                    winsound.Beep(1000, 500)
            except:
                pass
            # Repeat logic
            if repeat == "Daily":
                new_time = task_time + timedelta(days=1)
                updated_rows.append([row["task"], new_time, row["category"], repeat])
            elif repeat == "Weekly":
                new_time = task_time + timedelta(weeks=1)
                updated_rows.append([row["task"], new_time, row["category"], repeat])
            else:
                task_triggered = True  # Don’t re-add
        else:
            updated_rows.append([row["task"], row["datetime"], row["category"], repeat])
    # Save
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task", "datetime", "category", "repeat"])
        writer.writerows(updated_rows)
except Exception as e:
    st.error(f"❌ Notification Error: {e}")
# Auto-refresh every 60 seconds
st.caption("🔁 Refreshing every 60 seconds...")
time.sleep(60)
st.rerun()
