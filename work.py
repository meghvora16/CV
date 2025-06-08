import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

st.set_page_config(layout="wide")
st.title("CV Analyzer – Full and Half Cycle Plotting with Peak Detection")

uploaded_files = st.file_uploader("Upload CV Excel files", type=["xlsx"], accept_multiple_files=True)

def detect_turning_point(potential_series):
    diff = potential_series.diff().fillna(0)
    return diff.abs().idxmin()

def detect_peaks(potential, current):
    # crude peak detection: local maxima/minima
    peaks = []
    for i in range(1, len(current) - 1):
        if current[i-1] < current[i] > current[i+1] or current[i-1] > current[i] < current[i+1]:
            peaks.append(i)
    return peaks

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"📄 {file.name}")
        df = pd.read_excel(file, sheet_name="Sheet1")

        # Assign scan numbers
        df["Scan"] = df.groupby(df.columns[0]).cumcount() + 1
        scan_list = df["Scan"].unique()

        for scan_num in scan_list:
            scan_df = df[df["Scan"] == scan_num].copy()
            scan_df = scan_df.sort_values("Time (s)").reset_index(drop=True)

            st.markdown(f"### 🔄 Scan {scan_num}")

            # Turning point split
            turning_idx = detect_turning_point(scan_df['WE(1).Potential (V)'])
            anodic = scan_df.loc[:turning_idx]
            cathodic = scan_df.loc[turning_idx+1:]

            # Full Cycle Plot with Peaks
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.plot(scan_df['WE(1).Potential (V)'], scan_df['WE(1).Current (A)'], label='Full Cycle')
            peak_indices = detect_peaks(scan_df['WE(1).Potential (V)'], scan_df['WE(1).Current (A)'])

            for i in peak_indices:
                ax1.plot(scan_df['WE(1).Potential (V)'][i], scan_df['WE(1).Current (A)'][i], 'ro')
                ax1.annotate(f"Peak", (scan_df['WE(1).Potential (V)'][i], scan_df['WE(1).Current (A)'][i]),
                             textcoords="offset points", xytext=(0,10), ha='center')

            ax1.set_title(f"Full Cycle - Scan {scan_num} with Peaks")
            ax1.set_xlabel("Potential (V)")
            ax1.set_ylabel("Current (A)")
            ax1.grid(True)
            st.pyplot(fig1)

            # Half Cycle Plots
            col1, col2 = st.columns(2)

            with col1:
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                ax2.plot(anodic["Time (s)"], anodic["WE(1).Current (A)"], label='Anodic', color='green')
                ax2.set_title(f"Anodic Half-Cycle – Cu⁺ → Cu²⁺")
                ax2.set_xlabel("Time (s)")
                ax2.set_ylabel("Current (A)")
                ax2.grid(True)
                st.pyplot(fig2)

            with col2:
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                ax3.plot(cathodic["Time (s)"], cathodic["WE(1).Current (A)"], label='Cathodic', color='blue')
                ax3.set_title(f"Cathodic Half-Cycle – Cu²⁺ → Cu⁺")
                ax3.set_xlabel("Time (s)")
                ax3.set_ylabel("Current (A)")
                ax3.grid(True)
                st.pyplot(fig3)
