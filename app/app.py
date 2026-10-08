import datetime as dt
import html

import altair as alt
import mysql.connector
import pandas as pd
import streamlit as st

from db import get_connection

st.set_page_config(page_title="BioForge", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- themes
LIGHT = dict(
    bg="#FAF8F4", surface="#FFFFFF", text="#1F1B16", muted="#7A7268", border="#E6E0D6",
    grid="#ECE6DB", accent="#B4532A", neutral="#CFC8BC", teal="#2F6F6B",
    ok="#2F6F4F", ok_bg="rgba(47,111,79,.10)", err="#B3261E", err_bg="rgba(179,38,30,.08)",
    series=["#B4532A", "#2F6F6B", "#6B5B95", "#C49A1A", "#3E6FA3"],
)
DARK = dict(
    bg="#151412", surface="#1F1D1A", text="#ECE8E1", muted="#9C948A", border="#33302B",
    grid="#2A2723", accent="#E0875A", neutral="#4A453E", teal="#6CB5AE",
    ok="#6CC08E", ok_bg="rgba(108,192,142,.12)", err="#F08A82", err_bg="rgba(240,138,130,.12)",
    series=["#E0875A", "#6CB5AE", "#A99BD6", "#E3BE4A", "#7FAAD6"],
)

st.session_state.setdefault("dark", False)
top_l, top_r = st.columns([6, 1])
with top_r:
    st.toggle("Dark mode", key="dark")
T = DARK if st.session_state["dark"] else LIGHT

css_vars = "".join(f"--{k}:{v};" for k, v in T.items() if k != "series")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

.stApp { background: var(--bg); font-family: 'Inter', system-ui, sans-serif; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
.block-container { max-width: 1100px; padding: 2.2rem 2rem 4rem; }

/* text colours */
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li { color: var(--text) !important; }
.stApp [data-testid="stWidgetLabel"] p { color: var(--muted) !important; font-size: .82rem; font-weight: 500; }
.stApp label, .stApp label p { color: var(--text); }

/* brand + headings */
.bf-brand { font-family: 'Fraunces', Georgia, serif; font-size: 1.9rem; font-weight: 600;
            letter-spacing: -0.02em; color: var(--text); line-height: 1.1; }
.bf-tag { color: var(--muted); font-size: .9rem; margin-top: 4px; }
.bf-rule { border: 0; border-top: 1px solid var(--border); margin: 14px 0 6px; }
.bf-sec { margin: 34px 0 10px; }
.bf-sec .t { font-family: 'Fraunces', Georgia, serif; font-size: 1.3rem; font-weight: 600;
             color: var(--text); letter-spacing: -0.01em; }
.bf-sec .s { color: var(--muted); font-size: .88rem; margin-top: 2px; }
.bf-role { font-family: ui-monospace, Consolas, monospace; font-size: .76rem; color: var(--muted);
           margin: 10px 0 18px; }

/* stat strip */
.bf-stats { display: grid; grid-template-columns: repeat(4, 1fr);
            border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.bf-stat { padding: 18px 4px; }
.bf-stat .n { font-family: 'Fraunces', Georgia, serif; font-size: 2.1rem; font-weight: 500;
              color: var(--text); line-height: 1; }
.bf-stat .l { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em;
              color: var(--muted); margin-top: 8px; }
@media (max-width: 700px) { .bf-stats { grid-template-columns: repeat(2, 1fr); } }

/* tabs */
button[data-baseweb="tab"] { background: transparent !important; }
.stApp button[data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {
    color: var(--muted) !important; font-weight: 500; font-size: .95rem; }
.stApp button[data-baseweb="tab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p {
    color: var(--text) !important; }
div[data-baseweb="tab-highlight"] { background: var(--accent) !important; }
div[data-baseweb="tab-border"] { background: var(--border) !important; }

/* inputs */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"],
div[data-baseweb="select"] > div, .stTextArea textarea {
    background: var(--surface) !important; border-color: var(--border) !important;
    color: var(--text) !important; border-radius: 8px !important; }
input, textarea { color: var(--text) !important; }
div[data-baseweb="select"] * { color: var(--text); }
span[data-baseweb="tag"] { background: var(--accent) !important; }
span[data-baseweb="tag"] * { color: #fff !important; }
.stNumberInput button { background: var(--surface) !important; color: var(--text) !important; }
div[data-baseweb="popover"], div[data-baseweb="popover"] ul,
div[data-baseweb="menu"], ul[role="listbox"] { background: var(--surface) !important; }
li[role="option"] { color: var(--text) !important; background: var(--surface) !important; }
li[role="option"]:hover { background: var(--bg) !important; }
[data-testid="stForm"] { border: 1px solid var(--border); border-radius: 12px;
                         background: var(--surface); padding: 22px; }

/* buttons */
[data-testid^="stBaseButton-primary"] { background: var(--accent) !important; border: none !important;
    border-radius: 8px !important; }
.stApp [data-testid^="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p {
    color: #fff !important; font-weight: 500; }

/* table */
.bf-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px;
             background: var(--surface); }
.bf-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.bf-table th { text-align: left !important; font-weight: 500; color: var(--muted);
               font-size: .7rem; text-transform: uppercase; letter-spacing: .07em;
               padding: 10px 14px; border-bottom: 1px solid var(--border); white-space: nowrap; }
.bf-table td { padding: 9px 14px; border-bottom: 1px solid var(--border); color: var(--text); }
.bf-table tr:last-child td { border-bottom: none; }

/* messages */
.bf-msg { padding: 12px 16px; border-radius: 8px; border: 1px solid; font-size: .9rem; margin-top: 14px; }
.bf-msg.ok { background: var(--ok_bg); border-color: var(--ok); color: var(--ok); }
.bf-msg.err { background: var(--err_bg); border-color: var(--err); color: var(--err); }
.bf-msg.info { border-color: var(--border); color: var(--muted); background: var(--surface); }
.bf-foot { color: var(--muted); font-size: .78rem; margin-top: 48px; padding-top: 14px;
           border-top: 1px solid var(--border); }
""".replace("var(--ok_bg)", "var(--ok_bg)").replace("var(--err_bg)", "var(--err_bg)")

st.markdown("<style>:root{" + css_vars + "}" + CSS + "</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def run_query(role, sql, params=None):
    conn = get_connection(role)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return pd.DataFrame(cur.fetchall())
    finally:
        conn.close()


@st.cache_data(ttl=60)
def cached(role, sql, params=()):
    return run_query(role, sql, params)


def to_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c])
    return df


def section(title, sub=""):
    st.markdown(f'<div class="bf-sec"><div class="t">{html.escape(title)}</div>'
                f'<div class="s">{html.escape(sub)}</div></div>', unsafe_allow_html=True)


def stats(items):
    cells = "".join(f'<div class="bf-stat"><div class="n">{html.escape(str(v))}</div>'
                    f'<div class="l">{html.escape(l)}</div></div>' for l, v in items)
    st.markdown(f'<div class="bf-stats">{cells}</div>', unsafe_allow_html=True)


def table(df, max_rows=200):
    body = df.head(max_rows).to_html(index=False, border=0, classes="bf-table", na_rep="-")
    st.markdown(f'<div class="bf-scroll">{body.replace(chr(10), "")}</div>', unsafe_allow_html=True)


def msg(kind, text):
    st.markdown(f'<div class="bf-msg {kind}">{html.escape(text)}</div>', unsafe_allow_html=True)


def finish(chart, height):
    return (chart.properties(height=height)
            .configure(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelColor=T["muted"], titleColor=T["muted"], gridColor=T["grid"],
                            domainColor=T["border"], tickColor=T["border"],
                            labelFontSize=12, titleFontSize=12, titleFontWeight="normal")
            .configure_legend(labelColor=T["text"], titleColor=T["muted"], orient="top",
                              labelFontSize=12, symbolType="stroke"))


# ---------------------------------------------------------------- header
with top_l:
    st.markdown('<div class="bf-brand">BioForge</div>'
                '<div class="bf-tag">Linking bacterial mutations to antibiotic treatment outcomes</div>',
                unsafe_allow_html=True)
st.markdown('<hr class="bf-rule">', unsafe_allow_html=True)

tab_r, tab_c = st.tabs(["Researcher dashboard", "Clinician entry"])

# ================================================================ RESEARCHER
with tab_r:
    st.markdown('<div class="bf-role">bioforge_researcher &middot; read-only &middot; '
                'prescribing_physician hidden</div>', unsafe_allow_html=True)

    c = cached("researcher", """
        SELECT (SELECT COUNT(*) FROM strain WHERE is_active = TRUE) AS strains,
               (SELECT COUNT(*) FROM v_treatment_deidentified)      AS treatments,
               (SELECT COUNT(*) FROM mutation)                      AS mutations,
               (SELECT COUNT(*) FROM resistance_phenotype)          AS lab_tests
    """).iloc[0]
    stats([("Strains", f"{int(c['strains']):,}"), ("Treatments", f"{int(c['treatments']):,}"),
           ("Known mutations", f"{int(c['mutations']):,}"),
           ("Lab susceptibility tests", f"{int(c['lab_tests']):,}")])

    # ---- resistance over time
    section("Resistance over time", "Share of treatments where resistance was confirmed")
    df = cached("researcher", "SELECT * FROM v_resistance_rate_monthly ORDER BY month_label")
    df = to_num(df, ["total_treatments", "resistant_count", "resistance_rate_pct"])
    if df.empty:
        msg("info", "No data returned from v_resistance_rate_monthly.")
    else:
        df["month"] = pd.to_datetime(df["month_label"] + "-01")
        names = sorted(df["antibiotic_name"].unique())
        default = [a for a in ["Ciprofloxacin", "Amoxicillin", "Gentamicin"] if a in names] or names[:3]
        f1, f2 = st.columns([3, 1])
        chosen = f1.multiselect("Antibiotics", names, default=default)
        quarterly = f2.toggle("Group by quarter", value=True)
        sub = df[df["antibiotic_name"].isin(chosen)].copy()
        if sub.empty:
            msg("info", "Pick at least one antibiotic.")
        else:
            if quarterly:
                sub["period"] = sub["month"].dt.to_period("Q").dt.start_time
                g = sub.groupby(["period", "antibiotic_name"], as_index=False).agg(
                    resistant=("resistant_count", "sum"), total=("total_treatments", "sum"))
                g["rate"] = 100 * g["resistant"] / g["total"]
            else:
                g = sub.rename(columns={"month": "period", "resistance_rate_pct": "rate",
                                        "total_treatments": "total"})
            line = (alt.Chart(g).mark_line(strokeWidth=2.2, point=alt.OverlayMarkDef(size=36))
                    .encode(x=alt.X("period:T", title=None, axis=alt.Axis(format="%Y")),
                            y=alt.Y("rate:Q", title="Resistance confirmed (%)"),
                            color=alt.Color("antibiotic_name:N", title=None,
                                            scale=alt.Scale(range=T["series"])),
                            tooltip=[alt.Tooltip("antibiotic_name:N", title="Antibiotic"),
                                     alt.Tooltip("period:T", title="Period"),
                                     alt.Tooltip("rate:Q", title="Rate %", format=".1f"),
                                     alt.Tooltip("total:Q", title="Treatments")])
                    .interactive())
            st.altair_chart(finish(line, 340), theme=None)

    # ---- two charts side by side
    left, right = st.columns(2, gap="large")

    with left:
        section("Failure rate by mutation", "Failed, relapsed or deceased")
        df2 = cached("researcher", "SELECT * FROM v_mutation_treatment_failure")
        df2 = to_num(df2, ["total_treatments", "failed_treatments", "failure_rate_pct"])
        if df2.empty:
            msg("info", "No data returned from v_mutation_treatment_failure.")
        else:
            abx2 = sorted(df2["antibiotic_name"].unique())
            idx = abx2.index("Ciprofloxacin") if "Ciprofloxacin" in abx2 else 0
            pick = st.selectbox("Antibiotic", abx2, index=idx)
            min_n = st.slider("Minimum treatments per mutation", 1, 10, 3)
            s2 = df2[(df2["antibiotic_name"] == pick) & (df2["total_treatments"] >= min_n)].copy()
            if s2.empty:
                msg("info", "No mutations meet that threshold. Lower the slider.")
            else:
                s2["mutation"] = s2["gene_name"] + " #" + s2["mutation_id"].astype(str)
                bars = (alt.Chart(s2).mark_bar(cornerRadiusEnd=3)
                        .encode(y=alt.Y("mutation:N", sort="-x", title=None),
                                x=alt.X("failure_rate_pct:Q", title="Failure (%)",
                                        scale=alt.Scale(domain=[0, 100])),
                                color=alt.condition(alt.datum.gene_name == "gyrA",
                                                    alt.value(T["accent"]), alt.value(T["neutral"])),
                                tooltip=[alt.Tooltip("gene_name:N", title="Gene"),
                                         alt.Tooltip("failure_rate_pct:Q", title="Failure %", format=".1f"),
                                         alt.Tooltip("failed_treatments:Q", title="Failed"),
                                         alt.Tooltip("total_treatments:Q", title="Total")]))
                st.altair_chart(finish(bars, max(220, 26 * len(s2))), theme=None)
                st.caption("gyrA is highlighted: it is the mutation linked to fluoroquinolone failure.")

    with right:
        section("Lab resistance, real strains", "BV-BRC E. coli, share of tests that are resistant")
        df3 = cached("researcher", """
            SELECT a.name AS antibiotic, COUNT(*) AS tests,
                   ROUND(100 * SUM(rp.susceptibility = 'R') / COUNT(*), 2) AS pct_resistant
            FROM resistance_phenotype rp
            JOIN strain s     ON s.strain_id = rp.strain_id AND s.is_active = TRUE
            JOIN antibiotic a ON a.antibiotic_id = rp.antibiotic_id
            WHERE s.genomic_metadata->>'$.data_source' = 'BV-BRC'
            GROUP BY a.name ORDER BY pct_resistant DESC
        """)
        df3 = to_num(df3, ["tests", "pct_resistant"])
        if df3.empty:
            msg("info", "No BV-BRC lab data found. Did 05_real_import.sql run?")
        else:
            bars3 = (alt.Chart(df3).mark_bar(cornerRadiusEnd=3, color=T["teal"])
                     .encode(y=alt.Y("antibiotic:N", sort="-x", title=None),
                             x=alt.X("pct_resistant:Q", title="Resistant (%)"),
                             tooltip=[alt.Tooltip("antibiotic:N", title="Antibiotic"),
                                      alt.Tooltip("pct_resistant:Q", title="Resistant %", format=".1f"),
                                      alt.Tooltip("tests:Q", title="Tests")]))
            st.altair_chart(finish(bars3, max(220, 26 * len(df3))), theme=None)

    # ---- strain lookup
    section("Strain lookup", "Full history: mutations, treatments and outcomes. "
                             "IDs 1-500 are synthetic with full history; 100001+ are real, lab results only.")
    sid = st.number_input("Strain ID", min_value=1, value=1, step=1)
    hist = run_query("researcher", """
        SELECT s.strain_id, s.species, s.collection_date, h.name AS hospital,
               m.gene_name, m.mutation_type,
               a.name AS antibiotic, t.start_date, o.result, o.resistance_confirmed
        FROM strain s
        LEFT JOIN hospital h         ON h.hospital_id = s.hospital_id
        LEFT JOIN strain_mutation sm ON sm.strain_id = s.strain_id
        LEFT JOIN mutation m         ON m.mutation_id = sm.mutation_id
        LEFT JOIN v_treatment_deidentified t ON t.strain_id = s.strain_id
        LEFT JOIN antibiotic a       ON a.antibiotic_id = t.antibiotic_id
        LEFT JOIN outcome o          ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
        WHERE s.strain_id = %s AND s.is_active = TRUE
        ORDER BY t.start_date, m.gene_name
    """, (int(sid),))
    if hist.empty:
        msg("info", "No strain with that ID.")
    else:
        stats([("Species", hist.iloc[0]["species"]),
               ("Mutations", hist["gene_name"].nunique()),
               ("Treatments", int(hist["antibiotic"].notna().sum() and hist["start_date"].nunique())),
               ("Rows", len(hist))])
        st.write("")
        table(hist)
        st.caption("Rows repeat because every mutation is joined to every treatment. This is expected.")

# ================================================================ CLINICIAN
with tab_c:
    st.markdown('<div class="bf-role">bioforge_clinician &middot; can insert treatments and outcomes</div>',
                unsafe_allow_html=True)
    abx = run_query("clinician", "SELECT antibiotic_id, name FROM antibiotic ORDER BY name")
    abx_map = dict(zip(abx["name"], abx["antibiotic_id"]))

    side, main = st.columns([1, 2], gap="large")
    with side:
        section("Record a treatment", "Each treatment has exactly one outcome.")
        st.markdown(
            "- Enter the strain, antibiotic and dose.\n"
            "- Add the outcome and follow-up date.\n"
            "- The database enforces the rules: a follow-up date **before** the start date "
            "is rejected by a trigger, and the error is shown here.")

    with main:
        with st.form("entry"):
            a1, a2 = st.columns(2)
            strain_id = a1.number_input("Strain ID", min_value=1, value=1, step=1)
            antibiotic = a2.selectbox("Antibiotic", list(abx_map.keys()))
            b1, b2, b3 = st.columns(3)
            dosage = b1.number_input("Dosage (mg)", min_value=0.0, value=500.0)
            duration = b2.number_input("Duration (days)", min_value=1, value=7, step=1)
            start = b3.date_input("Start date", value=dt.date.today())
            physician = st.text_input("Prescribing physician")
            d1, d2 = st.columns(2)
            result = d1.selectbox("Outcome", ["cured", "failed", "relapsed", "deceased", "ongoing"])
            follow_up = d2.date_input("Follow-up date", value=dt.date.today() + dt.timedelta(days=14))
            resistance = st.checkbox("Resistance confirmed")
            notes = st.text_area("Notes")
            submit = st.form_submit_button("Save treatment and outcome", type="primary")

        if submit:
            conn = get_connection("clinician")
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO treatment
                       (strain_id, antibiotic_id, dosage_mg, duration_days, start_date, prescribing_physician)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (int(strain_id), int(abx_map[antibiotic]), dosage, int(duration),
                     start, physician or None))
                tid = cur.lastrowid
                cur.execute(
                    """INSERT INTO outcome
                       (treatment_id, result, resistance_confirmed, follow_up_date, notes)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (tid, result, resistance, follow_up, notes or None))
                conn.commit()
                msg("ok", f"Saved. Treatment #{tid} and its outcome were added.")
            except mysql.connector.Error as e:
                conn.rollback()
                msg("err", f"Database rejected this entry: {e.msg}")
            finally:
                conn.close()

    section("Most recent entries")
    recent = run_query("clinician", """
        SELECT t.treatment_id, t.strain_id, a.name AS antibiotic, t.start_date,
               o.result, o.follow_up_date
        FROM treatment t
        JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id
        LEFT JOIN outcome o ON o.treatment_id = t.treatment_id
        ORDER BY t.treatment_id DESC LIMIT 8
    """)
    table(recent)

st.markdown('<div class="bf-foot">Patient-level data is synthetic for demonstration; '
            'strains marked BV-BRC are real public data.</div>', unsafe_allow_html=True)