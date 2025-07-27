# 🏎️ F1 Data Analysis Toolkit

This repository is a personal project that explores **Formula 1 data analysis and visualization**, built using [FastF1](https://theoehrly.github.io/Fast-F1/), `plotly`, and other Python data tools.  
My goal is to develop **interpretable and visually compelling tools** that can explain race dynamics, tyre strategies, driver performance, and anomalies in F1 races.

---

## 📌 Project Goals

- Analyze various aspects of Formula 1 races using open telemetry and timing data
- Build reusable modules for analyzing **tyre degradation**, **pit strategies**, **track dominance**, and more
- Visualize the findings interactively using `plotly` or `altair`
- Generate standalone `.html` outputs for easy sharing and presentation

---

## 📁 Project Structure
```
f1_data_analysis/
├── analysis/
│ ├── tyre_degradation/
│ │ └── analysis.py # Main logic for tyre wear detection
│ ├── quali_dominance/
│ │ └── analysis.py # Track sector dominance using qualifying/practice data
│ └── ...
├── output/
│ ├── tyre_degradation.html # Interactive result visualization
│ ├── quali_dominance.html
│ └── ...
└── README.md
```

Each directory under `analysis/` corresponds to a specific type of analysis.  
The results are exported to the `output/` folder as standalone HTML dashboards.

---

## 🧪 Current Analyses

| Module               | Description                                       |
|----------------------|---------------------------------------------------|
| `tyre_degradation/`  | Calculates tyre life expectancy via piecewise or linear fitting |

More modules and visual styles are in progress.

---