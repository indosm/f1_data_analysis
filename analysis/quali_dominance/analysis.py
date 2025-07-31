import marimo

__generated_with = "0.14.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import matplotlib.pyplot as plt
    from matplotlib import colormaps
    from matplotlib.collections import LineCollection
    from collections import defaultdict

    from datetime import datetime
    import pandas as pd
    import numpy as np

    import fastf1
    from fastf1 import plotting
    return datetime, fastf1, np, plotting, plt


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
    # Enable Matplotlib patches for plotting timedelta values and load
    plotting.setup_mpl(mpl_timedelta_support=True, misc_mpl_mods=False)
    fastf1.Cache.enable_cache('./working/cache')

    # load a session and its telemetry data
    session = fastf1.get_session(year_dropdown.value, gp_radio.value, 'Q')  # Q=Qualifying
    session.load()
    return (session,)


@app.cell
def _(session):
    fastest_lap_datas = {
        driver: {
            'fastest_lap': session.laps.pick_drivers(driver).pick_fastest(),
            'car_data': session.laps.pick_drivers(driver).pick_fastest().get_car_data().add_distance()
        }
        for driver in session.drivers
    }
    return (fastest_lap_datas,)


@app.cell
def _(fastest_lap_datas):
    fastest_lap_data = sorted(fastest_lap_datas.items(), key=lambda x : x[1]['fastest_lap']['LapTime'])[0][1]
    fastest_lap = fastest_lap_data['fastest_lap']
    car_data = fastest_lap_data['car_data']
    return car_data, fastest_lap


@app.cell
def _(np):
    import plotly.graph_objects as go
    import plotly.express as px

    def draw_gear_shift_visualization(fastest_lap, car_data, session):
        tel = fastest_lap.get_telemetry()

        x = tel['X'].values
        y = tel['Y'].values
        gear = tel['nGear'].to_numpy().astype(int)

        # 색상 맵 정의 (기어 1~8, 총 8개의 색)
        color_scale = px.colors.qualitative.Prism
        gear_color_map = {g: color_scale[(g - 1) % len(color_scale)] for g in np.unique(gear)}


        fig = go.Figure()

        for i in range(len(x) - 1):
            gear_val = gear[i]
            color = color_scale[(gear_val - 1) % len(color_scale)]  # 0-indexed

            fig.add_trace(go.Scatter(
                x=[x[i], x[i+1]],
                y=[y[i], y[i+1]],
                mode='lines',
                line=dict(color=color, width=4),
                hoverinfo='skip',
                showlegend=False
            ))
        # 범례용 dummy trace 추가 (기어별 1개씩)
        for g, color in sorted(gear_color_map.items()):
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                line=dict(color=color, width=4),
                name=f"Gear {g}",
                hoverinfo='skip',
                showlegend=True
            ))

        fig.update_layout(
            title={
                'text': f"<b>Fastest Lap Gear Shift Visualization</b><br>{fastest_lap['Driver']} - {session.event['EventName']} {session.event.year}",
                'x': 0.5
            },
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white',
            margin=dict(t=60, l=20, r=20, b=20)
        )

        return fig

    return (draw_gear_shift_visualization,)


@app.cell
def _(car_data, draw_gear_shift_visualization, fastest_lap, session):
    draw_gear_shift_visualization(fastest_lap, car_data, session)
    return


@app.cell
def _(session):
    circuit_info = session.get_circuit_info()
    return (circuit_info,)


@app.cell
def _(car_data, circuit_info, fastest_lap, fastf1, plt, session):
    team_color = fastf1.plotting.get_team_color(fastest_lap['Team'],
                                                session=session)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(car_data['Distance'], car_data['Speed'],
            color=team_color, label=fastest_lap['Driver'])

    # Add shaded regions where braking is True
    brake_active = car_data['Brake'].fillna(False)
    brake_regions = []

    braking = False
    start = None
    for i in range(len(car_data)):
        if brake_active.iloc[i] and not braking:
            start = car_data['Distance'].iloc[i]
            braking = True
        elif not brake_active.iloc[i] and braking:
            end = car_data['Distance'].iloc[i]
            brake_regions.append((start, end))
            braking = False

    if braking:
        brake_regions.append((start, car_data['Distance'].iloc[-1]))

    # gray area background for brack=True secion
    for start, end in brake_regions:
        ax.axvspan(start, end, color='gray', alpha=0.2)

    # Add dotted line for each corner
    v_min = car_data['Speed'].min()
    v_max = car_data['Speed'].max()
    ax.vlines(x=circuit_info.corners['Distance'], ymin=v_min-20, ymax=v_max+20,
              linestyles='dotted', colors='grey')

    for _, corner in circuit_info.corners.iterrows():
        txt = f"{corner['Number']}{corner['Letter']}"
        ax.text(corner['Distance'], v_min-30, txt,
                va='center_baseline', ha='center', size='small')

    ax.set_xlabel('Distance in m')
    ax.set_ylabel('Speed in km/h')
    ax.set_ylim([v_min - 40, v_max + 20])
    ax.legend()

    fig
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
