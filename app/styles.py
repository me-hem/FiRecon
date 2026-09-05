import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        :root {
            --navy: #0f172a;
            --text: #1e293b;
            --slate: #475569;
            --muted: #64748b;
            --border: #dbe2ea;
            --border-strong: #c6d0dc;
            --surface: #ffffff;
            --surface-soft: #f8fafc;
            --page: #f3f6fa;
            --blue: #2563eb;
            --blue-soft: #eff6ff;
            --green: #15803d;
            --green-soft: #f0fdf4;
            --amber: #b45309;
            --amber-soft: #fffbeb;
            --red: #b91c1c;
            --red-soft: #fef2f2;
        }

        .stApp {
            background: var(--page);
            color: var(--text);
        }

        header[data-testid="stHeader"] {
            display: none;
        }

        div[data-testid="stToolbar"] {
            display: none;
        }

        .block-container {
            max-width: 1420px;
            padding-top: 1.2rem;
            padding-bottom: 4rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }

        h1, h2, h3, h4 { color: var(--navy) !important; }

        /* Hero */
        .hero {
            background: white;
            padding: 25px 24px 23px;
            margin: 0 0 20px;
            text-align: center;
        }

        .hero-title {
            color: black !important;
            font-size: 44px;
            font-weight: 850;
            letter-spacing: -1.8px;
            line-height: 1;
            margin: 0;
        }

        .hero-status {
            display: inline-block;
            margin-top: 12px;
            padding: 5px 10px;
            color: gray;
            font-size: 20px;
            font-weight: 750;
        }

        /* Processing container */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border-strong) !important;
            border-radius: 12px !important;
            background: rgba(255,255,255,.78) !important;
        }

        .processing-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding: 0 2px;
        }

        .processing-title {
            color: var(--navy);
            font-size: 15px;
            font-weight: 800;
        }

        .processing-count {
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
        }

        .stButton > button {
            min-height: 42px;
            border-radius: 8px;
            border: 1px solid var(--border-strong);
            background: #fff;
            color: #172033;
            font-size: 13px;
            font-weight: 700;
            transition: all .15s ease;
        }

        .stButton > button:hover {
            border-color: var(--blue);
            color: #1d4ed8;
            background: var(--blue-soft);
            box-shadow: none;
        }

        /* Main KPIs */
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 13px;
            min-height: 84px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, .03);
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .metric-card:hover { border-color: var(--border-strong); }

        .metric-label {
            color: #475569;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .045em;
            line-height: 1.25;
            text-align: center;
        }

        .metric-value {
            color: var(--navy);
            font-size: 24px;
            font-weight: 850;
            letter-spacing: -.4px;
            margin-top: 7px;
            line-height: 1.05;
            text-align: center;
        }

        .metric-note {
            color: var(--muted);
            font-size: 10px;
            margin-top: 5px;
            line-height: 1.2;
            text-align: center;
        }

        .metric-green { border-top: 3px solid var(--green); }
        .metric-amber { border-top: 3px solid var(--amber); }
        .metric-red { border-top: 3px solid var(--red); }
        .metric-blue { border-top: 3px solid var(--blue); }
        /* Exception mini panel */
        .mini-panel {
            margin-top: 20px;
            min-height: 82px;
            border-radius: 10px;
            padding: 13px 16px;
        }

        .exception-panel {
            background: #fffafa;
            border: 1px solid #fee2e2;
            border-left: 3px solid var(--red);
        }

        .exception-clear {
            background: var(--green-soft);
            border-color: #dcfce7;
            border-left-color: var(--green);
        }

        .exception-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .exception-kicker {
            color: var(--red);
            font-size: 12px;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .045em;
        }

        .exception-clear .exception-kicker { color: var(--green); }

        .exception-count {
            color: #475569;
            font-size: 11px;
            font-weight: 750;
        }

        .exception-summary-text,
        .exception-clear-text {
            color: #334155;
            font-size: 13px;
            font-weight: 600;
            line-height: 1.5;
            margin-top: 9px;
        }

        /* Section hierarchy */
        .section-title {
            color: var(--navy);
            font-size: 21px;
            font-weight: 800;
            letter-spacing: -0.01em;
            margin-top: 34px;
            margin-bottom: 0;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }

        .section-caption {
            color: var(--muted);
            font-size: 10px;
            margin: 6px 0 12px 13px;
            line-height: 1.45;
        }

        /* Decision */
        .decision-box {
            border-radius: 9px;
            padding: 15px 17px;
            border: 1px solid var(--border);
            background: var(--surface);
            min-height: 88px;
            text-align: center;
        }

        .decision-title {
            color: #475569;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .045em;
        }

        .decision-value {
            color: var(--navy);
            font-size: 20px;
            font-weight: 850;
            margin-top: 8px;
            text-align: center;
        }

        .decision-green { border-left: 3px solid var(--green); background: var(--green-soft); }
        .decision-amber { border-left: 3px solid var(--amber); background: var(--amber-soft); }
        .decision-red { border-left: 3px solid var(--red); background: var(--red-soft); }

        /* Content cards */
        .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 9px;
            padding: 15px 17px;
            margin: 7px 0 12px;
        }

        .ai-analysis-card {
            background: #f8fbff;
            border-left: 3px solid var(--blue);
            border-color: #dbeafe;
        }

        .ai-action-card {
            background: #fffcf3;
            border-left: 3px solid var(--amber);
            border-color: #fef3c7;
        }

        .flow-arrow {
            color: #94a3b8;
            font-size: 20px;
            text-align: center;
            padding-top: 30px;
        }

        /*AI*/
        .ai-action-title {
            font-size: 15px;
            font-weight: 700;
            color: #172033;
            margin-bottom: 4px;
        }

        .ai-action-description {
            font-size: 14px;
            color: #475569;
            margin-bottom: 12px;
        }

        div.st-key-ai_generate_button button {
            min-height: 44px;
            padding: 0 20px;
            border: 1px solid #1d4ed8;
            border-radius: 9px;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            font-size: 13px;
            font-weight: 750;
            box-shadow: 0 3px 8px rgba(37, 99, 235, .18);
            transition: all .15s ease;
        }       

        div.st-key-ai_generate_button button:hover {
            border-color: #1e40af;
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            color: #ffffff;
            box-shadow: 0 5px 12px rgba(37, 99, 235, .24);
            transform: translateY(-1px);
        }

        div.st-key-ai_generate_button button:active {
            transform: translateY(0);
        }

        div.st-key-duplicate_warning {
            margin-top: 18px;
        }

        /* Trace */
        .trace-card {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 11px 13px;
            margin-bottom: 7px;
        }

        .trace-header { color: var(--navy); font-size: 12px; font-weight: 800; }
        .trace-meta { color: var(--muted); font-size: 9px; margin-top: 4px; }

        .verified-pill, .exception-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 3px 7px;
            font-size: 9px;
            font-weight: 750;
        }

        .verified-pill {
            color: var(--green);
            background: var(--green-soft);
            border: 1px solid #bbf7d0;
        }

        .exception-pill {
            color: var(--red);
            background: var(--red-soft);
            border: 1px solid #fecaca;
        }

        /* Dataframe */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 9px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(15, 23, 42, .03);
            margin-top: 4px;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            border: 1px solid var(--border) !important;
            border-radius: 9px !important;
            background: var(--surface) !important;
            margin-bottom: 7px;
        }

        div[data-testid="stExpander"] details summary {
            font-weight: 700;
        }

        div[data-testid="stExpander"] details summary:hover {
            background: var(--surface-soft);
        }

        /* Select */
        div[data-baseweb="select"] { border-radius: 8px; }

        .stSelectbox > div > div {
            border-radius: 8px;
            border-color: var(--border-strong);
            background: #fff;
        }

        /* Native metrics */
        div[data-testid="stMetric"] {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 9px 11px;
        }

        div[data-testid="stMetricLabel"] { font-size: 11px !important; font-weight: 700 !important; text-align: center !important; }
        div[data-testid="stMetricValue"] { font-size: 18px !important; }

        hr { border-color: var(--border); }
        .stCaption { color: var(--muted); }

        @media (max-width: 950px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .hero {
                padding: 22px 16px 20px;
            }
            .hero-title {
                font-size: 38px;
            }
            .hero-subtitle {
                font-size: 12px;
            }
        }

        /* Investigation selector */
        div[data-testid="stSelectbox"] {
            max-width: 560px;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] {
            width: 100%;
        }

        .subsection-title {
            color: var(--navy);
            font-size: 15px;
            font-weight: 800;
            margin: 24px 0 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

