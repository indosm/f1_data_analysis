import marimo

__generated_with = "0.14.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    from IPython.display import display, Markdown
    import plotly.express as px
    import plotly.graph_objects as go
    return Markdown, display, go


@app.cell
def _():
    import fastf1
    from fastf1 import plotting
    from fastf1 import utils
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    plotting.setup_mpl()
    fastf1.Cache.enable_cache('./working/cache')

    session = fastf1.get_session(2023, 'Spain', 'R')  # R=Race
    session.load()

    laps = session.laps
    # LapTime을 초 단위로 변환
    laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
    laps['StintLapNumber'] = laps.groupby(['Driver', 'Stint']).cumcount() + 1
    return laps, plotting, session


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Tyre Dregadation Visualization

     * x axis - Lap Number
     * y axis - Lap Time
     * show lap time trends with compounds and lap number in stint
        * we could see tyre life time, and time difference via compounds, ...
    """
    )
    return


@app.cell
def _(laps):
    # Filter meaningful laps for analysis
    non_pit_laps = laps[(laps['PitOutTime'].isnull()) & (laps['PitInTime'].isnull()) & (laps['LapNumber'] != 1)]
    return (non_pit_laps,)


@app.cell
def _(go, plotting):
    from typing import Union

    compound_marker_map = {
        'SOFT': 'circle',
        'MEDIUM': 'triangle-up',
        'HARD': 'square'
    }

    def show_tyre_degradation(session, non_pit_laps, drivers: Union[str, list[str]] = "All"):
        total_driver_list = [session.get_driver(driver)['Abbreviation'] for driver in session.drivers]
        if drivers == "All":
            drivers = total_driver_list
        else:
            drivers = [driver for driver in drivers if driver in total_driver_list]
        driver_colors = {
            drv: plotting.get_driver_color(drv, session) for drv in drivers
        }

        fig = go.Figure()

        for drv in drivers:
            target_driver_laps = non_pit_laps[non_pit_laps['Driver'] == drv]

            for stint_value, group_df in target_driver_laps.groupby('Stint'):
                compound = group_df['Compound'].mode()[0] if not group_df['Compound'].isnull().all() else 'UNKNOWN'
                marker_symbol = compound_marker_map.get(compound.upper(), 'x')  # 기본은 x

                fig.add_trace(go.Scatter(
                    x=group_df['LapNumber'],
                    y=group_df['LapTimeSeconds'],
                    mode='lines+markers',
                    name=f"{session.get_driver(drv)['FullName']} - #{int(stint_value)}",
                    line=dict(color=driver_colors[drv], width=2),
                    marker=dict(symbol=marker_symbol, size=8),
                    opacity=0.8,
                    hoverinfo='text',
                    text=[
                        f"{session.get_driver(drv)['FullName']}<br>"
                        f"Stint: {stint_value}<br>"
                        f"Compound : {comp}<br>"
                        f"LapByStint : {lapByStint}<br>"
                        f"Lap: {lap}<br>"
                        f"LapTime: {lt:.3f}s"
                        for lapByStint, lap, lt, comp in zip(group_df['StintLapNumber'], group_df['LapNumber'], group_df['LapTimeSeconds'], group_df['Compound'])
                    ]
                ))

        # Layout 설정
        fig.update_layout(
            title=f"Tyre Degradation per Driver - {session.session_info['Meeting']['Name']} {session.date.strftime("%Y")}",
            xaxis_title="Lap Number",
            yaxis_title="Lap Time (seconds)",
            legend_title="Driver",
            hovermode="closest",
            width=1000,
            height=600
        )

        return fig
    return (show_tyre_degradation,)


@app.cell
def _(Markdown, display, mo):
    display(Markdown("""
     ### submit analysis wanted driver name
      * supported format : ["VER", "HAM", ...]
      * or you just Submit "All" to analysis all driver's data"""))
    driver = mo.ui.text().form()
    return (driver,)


@app.cell
def _(driver):
    driver
    return


@app.cell
def _(driver, non_pit_laps, session, show_tyre_degradation):
    show_tyre_degradation(session, non_pit_laps, drivers=[] if driver.value is None else eval(driver.value))
    return


if __name__ == "__main__":
    app.run()
