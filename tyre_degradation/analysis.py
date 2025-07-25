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
    from datetime import datetime
    import fastf1
    from fastf1 import plotting
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    return Markdown, datetime, display, fastf1, go, np, pd, plotting, plt, px


@app.cell
def _(datetime, mo):
    now = datetime.now()
    year_dropdown = mo.ui.dropdown(
        options=[x for x in range(2021, now.year + 1)], value=now.year, label="Year : "
    )
    year_dropdown
    return now, year_dropdown


@app.cell
def _(fastf1, mo, now, year_dropdown):
    events = fastf1.get_event_schedule(year_dropdown.value)
    support_session_options = events[(events['EventFormat'] != 'testing') & (events['EventDate'] <= now)]['EventName'].unique()
    gp_radio = mo.ui.radio(options=support_session_options, value=support_session_options[0])
    return (gp_radio,)


@app.cell
def _(gp_radio, mo, year_dropdown):
    mo.hstack([gp_radio, mo.md(f"Selected Session: {year_dropdown.value} - {gp_radio.value}")])
    return


@app.cell
def _(fastf1, gp_radio, plotting, year_dropdown):
    import os

    plotting.setup_mpl()
    os.makedirs('./working/cache', exist_ok=True)
    fastf1.Cache.enable_cache('./working/cache')

    session = fastf1.get_session(year_dropdown.value, gp_radio.value, 'R')  # R=Race
    session.load()

    laps = session.laps
    laps['Stint'] = laps['Stint'].fillna(0)
    laps = laps.astype({'LapNumber':'int', 'Stint':'int'})
    laps = laps[~laps['LapTime'].isna()]

    # Convert LapTime to second level
    laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
    laps['StintLapNumber'] = laps.groupby(['Driver', 'Stint']).cumcount() + 1
    return laps, session


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Tyre Degradation Visualization

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
def _(go, np, pd, plotting, plt):
    from sklearn.linear_model import LinearRegression
    from typing import Union
    import altair as alt
    import pwlf

    compound_marker_map = {
        'SOFT': 'circle',
        'MEDIUM': 'triangle-up',
        'HARD': 'square'
    }

    def fit_piecewise_laptime(lap_numbers, lap_times, n_segments=2, plot=True):
        """
        lap_numbers: List or Series of lap numbers
        lap_times: List or Series of lap times (in seconds)
        n_segments: number of line segments for piecewise linear fit
        """
        # sort data based on lap
        df = pd.DataFrame({'Lap': lap_numbers, 'LapTime': lap_times}).dropna().sort_values('Lap')
        x = df['Lap'].values
        y = df['LapTime'].values

        # Piecewise linear fit
        model = pwlf.PiecewiseLinFit(x, y)
        breakpoints = model.fit(n_segments)

        # prediction lap time
        x_hat = np.linspace(x.min(), x.max(), 100)
        y_hat = model.predict(x_hat)

        if plot:
            print(model.ssr)
            plt.figure(figsize=(10, 5))
            plt.plot(x, y, 'o', label='Actual Lap Times', alpha=0.6)
            plt.plot(x_hat, y_hat, '-', label='Piecewise Fit', color='red')
            for bp in breakpoints[1:-1]:
                plt.axvline(bp, color='gray', linestyle='--', label=f'Breakpoint @ Lap {bp:.1f}')
            plt.xlabel("Lap Number")
            plt.ylabel("Lap Time (seconds)")
            plt.title("Piecewise Linear Fit for Tyre Degradation")
            plt.legend()
            plt.grid(True)
            plt.show()

        return {
            'model': model,
            'breakpoints': breakpoints,
            'x_hat': x_hat,
            'y_hat': y_hat,
        }

    def analyze_laptime(fit_result):
        model = fit_result['model']
        slopes = [round(x,3) for x in model.calc_slopes()]

        tyre_lifespan = 0
        tyre_lifespan_remain = False
        needs_warmup = False
        warmup_laps = 0
        if slopes[0] <= 0 and slopes[2] >= 0:
            # at first, lap time decreases by using fresh tyre, and increases after tyre graining
            if slopes[1] < 0:
                tyre_lifespan = fit_result['breakpoints'][2]
            else :
                tyre_lifespan = fit_result['breakpoints'][1]
        elif slopes[0] <= 0 and slopes[1] <= 0 and slopes[2] <= 0:
            tyre_lifespan = fit_result['breakpoints'][-1]
            tyre_lifespan_remain = True
        else:
            if slopes[1] <= 0 and slopes[2] >= 0:
                tyre_lifespan = fit_result['breakpoints'][2]
                needs_warmup = True
                warmup_laps = fit_result['breakpoints'][1]
            else :
                tyre_lifespan = fit_result['breakpoints'][-1]
                tyre_lifespan_remain = True
                needs_warmup = True
                warmup_laps = fit_result['breakpoints'][1]
        return {
            "tyre_lifespan" : tyre_lifespan,
            "tyre_lifespan_remain" : tyre_lifespan_remain,
            "needs_warmup" : needs_warmup,
            "warmup_laps" : warmup_laps
        }

    def show_tyre_degradation(session, non_pit_laps, drivers: list[str] = []):
        def make_tyre_info_message(tyre_info):
            message = ""
            if tyre_info['needs_warmup']:
                message += f"tyre needs {tyre_info['warmup_laps']:.01f} laps to warm up<br>"
            message += f"estimated tyre lifespan : {f"{tyre_info["tyre_lifespan"]:.01f}+" if tyre_info['tyre_lifespan_remain'] else f"around {tyre_info["tyre_lifespan"]:.01f}"} laps"
            return message

        driver_colors = {
            drv: plotting.get_driver_color(drv, session) for drv in drivers
        }
        fig = go.Figure()

        for drv in drivers:
            target_driver_laps = non_pit_laps[non_pit_laps['Driver'] == drv]
            name = session.get_driver(drv)['FullName']
            team_name = session.get_driver(drv)['TeamName']

            for stint_value, group_df in target_driver_laps.groupby('Stint'):
                compound = group_df['Compound'].mode()[0] if not group_df['Compound'].isnull().all() else 'UNKNOWN'
                marker_symbol = compound_marker_map.get(compound.upper(), 'x')  # set default marker symbol as 'x'

                # calculate degradation regression and draw it
                fit_result = fit_piecewise_laptime(
                    group_df['StintLapNumber'],
                    group_df['LapTimeSeconds'],
                    n_segments=3,
                    plot=False
                )
                slopes = fit_result['model'].calc_slopes()

                tyre_info = analyze_laptime(fit_result)

                # Lap Time trace
                fig.add_trace(go.Scatter(
                    x=group_df['LapNumber'],
                    y=group_df['LapTimeSeconds'],
                    mode='lines+markers',
                    name=f"{name} - #{int(stint_value)}",
                    line=dict(color=driver_colors[drv], width=2),
                    marker=dict(symbol=marker_symbol, size=8),
                    opacity=0.8,
                    hoverinfo='text',
                    text=[
                        f"{name}<br>"
                        f"Stint: {stint_value}<br>"
                        f"Compound : {comp}<br>"
                        f"LapByStint : {lapByStint}<br>"
                        f"Lap: {lap}<br>"
                        f"LapTime: {lt:.3f}s"
                        for lapByStint, lap, lt, comp in zip(group_df['StintLapNumber'], group_df['LapNumber'], group_df['LapTimeSeconds'], group_df['Compound'])
                    ],
                    legendgroup=f'{name}-#{stint_value}',
                ))

                # degradation regression trace
                fig.add_trace(go.Scatter(
                    x = fit_result['x_hat'] + group_df['LapNumber'].min()  - group_df['StintLapNumber'].min(),
                    y = fit_result['y_hat'],
                    mode='lines',
                    line=dict(color='red', dash='dot', width=2),
                    hoverinfo='text',
                    text=[make_tyre_info_message(tyre_info)] * len(fit_result['y_hat']),
                    legendgroup=f'{name}-#{stint_value}',
                    showlegend=False
                ))
        # Layout Configuration
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
    return analyze_laptime, fit_piecewise_laptime, show_tyre_degradation


@app.cell
def _(Markdown, display, mo, session):
    display(Markdown("""
     ### submit analysis wanted driver name"""))
    driver_options = [session.get_driver(drv)['Abbreviation'] for drv in session.drivers]
    drivers_select = mo.ui.multiselect(options=driver_options, value=driver_options[:3])
    return driver_options, drivers_select


@app.cell
def _(drivers_select, mo):
    mo.hstack([drivers_select, mo.md(f"Analysis Target Driver: {drivers_select.value}")])
    return


@app.cell
def _(drivers_select, non_pit_laps, session, show_tyre_degradation):
    show_tyre_degradation(session, non_pit_laps, drivers_select.value)
    return


@app.cell
def _(analyze_laptime, driver_options, fit_piecewise_laptime, pd, plotting):
    def analysis_tyre_lifespan(session, non_pit_laps):
        tyre_infos = []
        for drv in driver_options:
            target_driver_laps = non_pit_laps[non_pit_laps['Driver'] == drv]
            name = session.get_driver(drv)['FullName']
            team_name = session.get_driver(drv)['TeamName']
            driver_color = plotting.get_driver_color(drv, session)

            for stint_value, group_df in target_driver_laps.groupby('Stint'):
                compound = group_df['Compound'].mode()[0] if not group_df['Compound'].isnull().all() else 'UNKNOWN'

                # calculate degradation regression and draw it
                fit_result = fit_piecewise_laptime(
                    group_df['StintLapNumber'],
                    group_df['LapTimeSeconds'],
                    n_segments=3,
                    plot=False
                )
                slopes = fit_result['model'].calc_slopes()

                tyre_info = analyze_laptime(fit_result)
                tyre_info.update({'driver' : drv, 'team': team_name, 'compound' : compound, 'color' : driver_color})
                tyre_infos.append(tyre_info)

        return pd.DataFrame(tyre_infos)
    return (analysis_tyre_lifespan,)


@app.cell
def _(analysis_tyre_lifespan, non_pit_laps, session):
    lifespan_df = analysis_tyre_lifespan(session, non_pit_laps)
    return (lifespan_df,)


@app.cell
def _(lifespan_df, px):
    fig2 = px.box(
        lifespan_df.sort_values('compound', ascending=False),
        y='compound',
        x='tyre_lifespan',
        color='compound',
        points="all",  # 개별 데이터 점 표시
        hover_data=['driver', 'team'],
        title="Expected Tyre Lifespan Distribution by Compound",
    )

    fig2.update_layout(
        xaxis_title="Tyre Compound",
        yaxis_title="Expected Tyre Lifespan (Laps)",
        showlegend=False,
        width=800,
        height=500
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
