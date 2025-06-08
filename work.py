import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

st.set_page_config(layout="wide")
st.title("Cyclic Voltammetry Analyzer")

uploaded_files = st.file_uploader("Upload CV Excel files", type=["xlsx"], accept_multiple_files=True)

def extract_cycle_range(filename):
    match = re.search(r'CV(\d+)(?:-(\d+))?', filename)
    if match:
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        return list(range(start, end + 1))
    return []

def find_turning_index(potential):
    peak_idx = potential.idxmax()
    valley_idx = potential.idxmin()
    return peak_idx if peak_idx < valley_idx else valley_idx

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"📄 {file.name}")
        try:
            df = pd.read_excel(file, sheet_name="Sheet1")
            df.columns = [col.strip() for col in df.columns]
            st.write("📋 Columns detected:", df.columns.tolist())
        except Exception as e:
            st.error(f"❌ Could not read {file.name}: {e}")
            continue

        required_cols = ["Time (s)", "WE(1).Potential (V)", "WE(1).Current (A)"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"❌ Missing required columns: {required_cols}")
            continue

        cycle_nums = extract_cycle_range(file.name)
        if cycle_nums:
            total_rows = len(df)
            scan_length = total_rows // len(cycle_nums)
            scan_ids = []
            for i, cycle in enumerate(cycle_nums):
                start = i * scan_length
                end = (i + 1) * scan_length if i < len(cycle_nums) - 1 else total_rows
                scan_ids.extend([cycle] * (end - start))
            df["Scan"] = scan_ids
        else:
            df["Scan"] = 1

        all_scans = []

        for cycle in df["Scan"].unique():
            scan_df = df[df["Scan"] == cycle].sort_values("Time (s)").reset_index(drop=True)
            pot_range = scan_df['WE(1).Potential (V)'].max() - scan_df['WE(1).Potential (V)'].min()
            st.write(f"Cycle {cycle} – Potential Range: {pot_range:.4f} V")

            if pot_range < 0.01:
                st.warning(f"⚠️ Cycle {cycle} skipped — potential range too small.")
                continue

            turning_idx = find_turning_index(scan_df['WE(1).Potential (V)'])
            if turning_idx < 10 or turning_idx > len(scan_df) - 10:
                st.warning(f"⚠️ Could not split Cycle {cycle} properly — skipping half-cycle plots.")
                continue

            anodic = scan_df.iloc[:turning_idx]
            cathodic = scan_df.iloc[turning_idx:]
            all_scans.append((cycle, scan_df))

            # Full cycle
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.plot(scan_df['WE(1).Potential (V)'], scan_df['WE(1).Current (A)'])
            ax1.set_title(f"Full Cycle - Cycle {cycle}")
            ax1.set_xlabel("Potential (V)")
            ax1.set_ylabel("Current (A)")
            ax1.grid(True)
            st.pyplot(fig1)

            # Half cycles
            col1, col2 = st.columns(2)
            with col1:
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                ax2.plot(anodic["Time (s)"], anodic["WE(1).Current (A)"], color='green')
                ax2.set_title("Anodic Half-Cycle – Cu⁺ → Cu²⁺")
                ax2.set_xlabel("Time (s)")
                ax2.set_ylabel("Current (A)")
                ax2.grid(True)
                st.pyplot(fig2)

            with col2:
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                ax3.plot(cathodic["Time (s)"], cathodic["WE(1).Current (A)"], color='blue')
                ax3.set_title("Cathodic Half-Cycle – Cu²⁺ → Cu⁺")
                ax3.set_xlabel("Time (s)")
                ax3.set_ylabel("Current (A)")
                ax3.grid(True)
                st.pyplot(fig3)

        # 🔁 Overlay plot at end
        if all_scans:
            st.markdown("## 📉 Overlaid CVs – Visual Comparison Across Cycles")
            fig_overlay, ax_overlay = plt.subplots(figsize=(8, 5))
            for cycle, scan_df in all_scans:
                ax_overlay.plot(scan_df['WE(1).Potential (V)'], scan_df['WE(1).Current (A)'], label=f"Cycle {cycle}")
            ax_overlay.set_title("Overlaid Cyclic Voltammograms")
            ax_overlay.set_xlabel("Potential (V)")
            ax_overlay.set_ylabel("Current (A)")
            ax_overlay.grid(True)
            ax_overlay.legend(fontsize=8, loc="upper right")
            st.pyplot(fig_overlay)
# 📈 Plot drift of starting current and potential across cycles
            st.markdown("## 📊 Drift of Starting Potential and Current Across Cycles")
            
            start_potential = []
            start_current = []
            cycle_ids = []
            
            for cycle, scan_df in all_scans:
                first_row = scan_df.iloc[0]
                cycle_ids.append(cycle)
                start_potential.append(first_row["WE(1).Potential (V)"])
                start_current.append(first_row["WE(1).Current (A)"])
            
            # Potential drift
            fig_pot, ax_pot = plt.subplots()
            ax_pot.plot(cycle_ids, start_potential, marker='o')
            ax_pot.set_title("Starting Potential Drift")
            ax_pot.set_xlabel("Cycle")
            ax_pot.set_ylabel("Potential (V)")
            ax_pot.grid(True)
            st.pyplot(fig_pot)
            
            # Current drift
            fig_curr, ax_curr = plt.subplots()
            ax_curr.plot(cycle_ids, start_current, marker='o', color='orange')
            ax_curr.set_title("Starting Current Drift")
            ax_curr.set_xlabel("Cycle")
            ax_curr.set_ylabel("Current (A)")
            ax_curr.grid(True)
            st.pyplot(fig_curr)
