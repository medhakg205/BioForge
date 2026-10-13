import datetime as dt
import html

import altair as alt
import mysql.connector
import pandas as pd
import streamlit as st

from db import get_connection

st.set_page_config(page_title="BioForge", layout="wide", initial_sidebar_state="expanded")

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
st.session_state.setdefault("role_sidebar", "Researcher")
T = DARK if st.session_state["dark"] else LIGHT

css_vars = "".join(f"--{k}:{v};" for k, v in T.items() if k != "series")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

.stApp { background: var(--bg); font-family: 'Inter', system-ui, sans-serif; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 1001 !important;
}
.block-container { max-width: none; width: 100%; padding: 1.6rem 2.5rem 3rem; }
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div:first-child { padding: 1.2rem .9rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--text); }
[data-testid="stRadio"] > label { font-size: .75rem; text-transform: uppercase;
    letter-spacing: .08em; color: var(--muted) !important; }

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
.bf-sec { margin: 24px 0 10px; }
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

dark = st.session_state["dark"]
st.markdown(f"""
<style>
:root {{ color-scheme: {"dark" if dark else "light"}; }}

/* every layer of every input: fill = surface colour, text = readable colour */
[data-testid="stForm"] div[data-baseweb="input"],
[data-testid="stForm"] div[data-baseweb="input"] > div,
[data-testid="stForm"] div[data-baseweb="base-input"],
[data-testid="stForm"] div[data-baseweb="textarea"],
[data-testid="stForm"] div[data-baseweb="textarea"] > div,
[data-testid="stForm"] div[data-baseweb="select"] > div,
[data-testid="stForm"] [data-testid="stNumberInputContainer"],
[data-testid="stForm"] [data-testid="stDateInputField"] {{
    background-color: var(--bg) !important;
    border-color: var(--border) !important;
    color: var(--text) !important; }}

[data-testid="stForm"] input, [data-testid="stForm"] textarea {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--text) !important; }}
[data-testid="stForm"] ::placeholder {{
    color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; opacity: 1; }}

/* selected value + dropdown arrow */
[data-testid="stForm"] div[data-baseweb="select"] * {{ color: var(--text) !important; }}
[data-testid="stForm"] svg {{ fill: var(--muted) !important; }}

/* number +/- buttons */
[data-testid="stNumberInput"] button {{
    background-color: var(--surface) !important; color: var(--text) !important;
    border-color: var(--border) !important; }}

/* checkbox */
label[data-baseweb="checkbox"] > span:first-child {{
    background-color: var(--bg) !important; border-color: var(--muted) !important; }}
label[data-baseweb="checkbox"]:has(input:checked) > span:first-child {{
    background-color: var(--accent) !important; border-color: var(--accent) !important; }}

/* save button */
[data-testid="stForm"] button {{
    background-color: var(--accent) !important; border: none !important; }}
[data-testid="stForm"] button * {{ color: #fff !important; }}

/* calendar popup and dropdown lists (they render outside the form) */
div[data-baseweb="calendar"], div[data-baseweb="calendar"] * {{
    background-color: var(--surface) !important; color: var(--text) !important; }}
div[data-baseweb="calendar"] [aria-selected="true"],
div[data-baseweb="calendar"] [aria-selected="true"] * {{
    background-color: var(--accent) !important; color: #fff !important; }}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li {{
    background-color: var(--surface) !important; color: var(--text) !important; }}
</style>
""", unsafe_allow_html=True)

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


def download_chart_csv(df, key, filename):
    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


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
with st.sidebar:
    st.markdown('<div class="bf-brand">BioForge</div>'
                '<div class="bf-tag">Antimicrobial resistance insights</div>',
                unsafe_allow_html=True)
    st.markdown('<hr class="bf-rule">', unsafe_allow_html=True)
    selected_role = st.radio(
        "Workspace",
        ["Researcher", "Clinician", "Admin", "ETL"],
        key="role_sidebar",
    )
    st.markdown('<hr class="bf-rule">', unsafe_allow_html=True)
    st.toggle("Dark mode", key="dark")
    st.caption({
        "Researcher": "Read-only research views • prescribing physician hidden",
        "Clinician": "Submit treatment and outcome records",
        "Admin": "Review all records and update audit history",
        "ETL": "Insert strain and mutation records",
    }[selected_role])

# ================================================================ RESEARCHER
if selected_role == "Researcher":
    _, refresh_col = st.columns([5, 1])
    if refresh_col.button("Refresh data", use_container_width=True):
        cached.clear()
        st.rerun()
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

    k = cached("researcher", """
        SELECT ROUND(100*SUM(result IN ('failed','relapsed','deceased'))/COUNT(*),1) AS fail_pct,
               ROUND(100*SUM(resistance_confirmed)/COUNT(*),1) AS res_pct
        FROM outcome WHERE is_active = TRUE
    """).iloc[0]
    worst = cached("researcher", """
        SELECT antibiotic_name, ROUND(100*SUM(resistant_count)/SUM(total_treatments),1) AS pct
        FROM v_resistance_rate_monthly GROUP BY antibiotic_name ORDER BY pct DESC LIMIT 1""")
    risk = cached("researcher", """
        SELECT gene_name, antibiotic_name, failure_rate_pct FROM v_mutation_treatment_failure
        WHERE total_treatments >= 5 ORDER BY failure_rate_pct DESC LIMIT 1""")
    st.write("")
    stats([
        ("Overall treatment failure", f"{float(k['fail_pct'])}%"),
        ("Resistance confirmed", f"{float(k['res_pct'])}%"),
        ("Most resistant antibiotic",
         f"{worst.iloc[0]['antibiotic_name']} ({float(worst.iloc[0]['pct'])}%)" if not worst.empty else "n/a"),
        ("Highest-risk mutation",
         f"{risk.iloc[0]['gene_name']} + {risk.iloc[0]['antibiotic_name']}" if not risk.empty else "n/a"),
    ])

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
            download_chart_csv(g, "download_resistance_over_time", "resistance_over_time.csv")

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
                download_chart_csv(s2, "download_failure_by_mutation", "failure_by_mutation.csv")
                st.caption("gyrA is highlighted: it is the mutation linked to fluoroquinolone failure.")

    with right:
        section("Lab resistance by antibiotic", "Share of lab susceptibility tests that are resistant")
        df3 = cached("researcher", """
            SELECT a.name AS antibiotic, COUNT(*) AS tests,
                   ROUND(100 * SUM(rp.susceptibility = 'R') / COUNT(*), 2) AS pct_resistant
            FROM resistance_phenotype rp
            JOIN strain s     ON s.strain_id = rp.strain_id AND s.is_active = TRUE
            JOIN antibiotic a ON a.antibiotic_id = rp.antibiotic_id
            GROUP BY a.name ORDER BY pct_resistant DESC
        """)
        df3 = to_num(df3, ["tests", "pct_resistant"])
        if df3.empty:
            msg("info", "No lab data found. Did 05_real_import.sql run?")
        else:
            bars3 = (alt.Chart(df3).mark_bar(cornerRadiusEnd=3, color=T["teal"])
                     .encode(y=alt.Y("antibiotic:N", sort="-x", title=None),
                             x=alt.X("pct_resistant:Q", title="Resistant (%)"),
                             tooltip=[alt.Tooltip("antibiotic:N", title="Antibiotic"),
                                      alt.Tooltip("pct_resistant:Q", title="Resistant %", format=".1f"),
                                      alt.Tooltip("tests:Q", title="Tests")]))
            st.altair_chart(finish(bars3, max(220, 26 * len(df3))), theme=None)
            download_chart_csv(df3, "download_lab_resistance", "lab_resistance_by_antibiotic.csv")
            st.caption(f"{len(df3)} antibiotics in this chart.")

    h_col, o_col = st.columns(2, gap="large")
    with h_col:
        section("Failure rate by hospital", "Share of treatments that failed, relapsed or ended in death")
        dh = to_num(cached("researcher", """
            SELECT h.name AS hospital, COUNT(*) AS total,
                   ROUND(100*SUM(o.result IN ('failed','relapsed','deceased'))/COUNT(*),1) AS failure_pct
            FROM hospital h
            JOIN strain s ON s.hospital_id = h.hospital_id AND s.is_active = TRUE
            JOIN v_treatment_deidentified t ON t.strain_id = s.strain_id
            JOIN outcome o ON o.treatment_id = t.treatment_id AND o.is_active = TRUE
            WHERE h.is_active = TRUE GROUP BY h.hospital_id, h.name
        """), ["total", "failure_pct"])
        if not dh.empty:
            ch = (alt.Chart(dh).mark_bar(cornerRadiusEnd=3, color=T["accent"])
                  .encode(y=alt.Y("hospital:N", sort="-x", title=None),
                          x=alt.X("failure_pct:Q", title="Failure (%)"),
                          tooltip=["hospital", "total", "failure_pct"]))
            st.altair_chart(finish(ch, max(200, 40 * len(dh))), theme=None)
            download_chart_csv(dh, "download_failure_by_hospital", "failure_by_hospital.csv")
    with o_col:
        section("Outcome mix", "Number of treatments by result")
        do = to_num(cached("researcher",
            "SELECT result, COUNT(*) AS n FROM outcome WHERE is_active = TRUE GROUP BY result"), ["n"])
        if not do.empty:
            co = (alt.Chart(do).mark_bar(cornerRadiusEnd=3, color=T["teal"])
                  .encode(y=alt.Y("result:N", sort="-x", title=None),
                          x=alt.X("n:Q", title="Treatments"),
                          tooltip=["result", "n"]))
            st.altair_chart(finish(co, max(200, 40 * len(do))), theme=None)
            download_chart_csv(do, "download_outcome_mix", "outcome_mix.csv")

    # ---- strain lookup
    section("Strain lookup", "Full history: mutations, treatments and outcomes. "
                             "IDs 100001+ are real, lab results only with no treatment history.")
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
if selected_role == "Clinician":
    st.markdown('<div class="bf-role">bioforge_clinician &middot; can insert treatments and outcomes</div>',
                unsafe_allow_html=True)
    abx = run_query("clinician", "SELECT antibiotic_id, name FROM antibiotic ORDER BY name")
    abx_map = dict(zip(abx["name"], abx["antibiotic_id"]))
    hospitals = run_query(
        "clinician",
        """SELECT hospital_id, name, city
           FROM hospital
           WHERE is_active = TRUE
           ORDER BY name, city, hospital_id""",
    )
    hospital_map = {
        f"{row['name']} ({row['city']}) [#{row['hospital_id']}]": int(row["hospital_id"])
        for _, row in hospitals.iterrows()
    }
    hospital_labels = list(hospital_map)
    if hospital_labels:
        selected_hospital = st.selectbox("Hospital filter", hospital_labels)
        selected_hospital_id = hospital_map[selected_hospital]
    else:
        selected_hospital_id = None
        st.info("No active hospitals are available for clinician entry.")

    side, main = st.columns([1, 2], gap="large")
    with side:
        section("Record a treatment", "Each treatment has exactly one outcome.")
        st.markdown(
            "- Enter the strain, antibiotic and dose.\n"
            "- Add the outcome and follow-up date.\n"
            "- The database enforces the rules: a follow-up date **before** the start date "
            "is rejected by a trigger, and the error is shown here.")

    with main:
        feedback = st.empty()   # result message appears here, above the form

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
            submit = st.form_submit_button(
                "Save treatment and outcome",
                type="primary",
                disabled=selected_hospital_id is None,
            )

        if submit:
            conn = None
            try:
                conn = get_connection("clinician")
                cur = conn.cursor()
                cur.execute(
                    """SELECT strain_id
                       FROM strain
                       WHERE strain_id = %s AND hospital_id = %s AND is_active = TRUE""",
                    (int(strain_id), selected_hospital_id),
                )
                if cur.fetchone() is None:
                    raise ValueError("The strain is not active at the selected hospital.")
                cur.execute(
                    """CALL sp_record_treatment(
                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                       )""",
                    (int(strain_id), int(abx_map[antibiotic]), dosage, int(duration),
                     start, physician or None, result, resistance, follow_up, notes or None),
                )
                result_row = cur.fetchone()
                if result_row is None:
                    raise RuntimeError("The treatment procedure did not return a treatment ID.")
                tid = result_row[0]
                while cur.nextset():
                    cur.fetchall()
                text = f"Saved. Treatment #{tid} (start {start}, follow-up {follow_up}) and its outcome were added."
                feedback.markdown(f'<div class="bf-msg ok">{html.escape(text)}</div>', unsafe_allow_html=True)
                st.toast("Saved", icon="✅")
            except ValueError as e:
                text = f"Invalid entry: {e}"
                feedback.markdown(f'<div class="bf-msg err">{html.escape(text)}</div>', unsafe_allow_html=True)
            except mysql.connector.Error as e:
                if conn: conn.rollback()
                text = f"Database rejected this entry: {e.msg}"
                feedback.markdown(f'<div class="bf-msg err">{html.escape(text)}</div>', unsafe_allow_html=True)
                st.toast("Rejected by the database", icon="🚫")
            except Exception as e:
                if conn: conn.rollback()
                text = f"Unexpected error: {type(e).__name__}: {e}"
                feedback.markdown(f'<div class="bf-msg err">{html.escape(text)}</div>', unsafe_allow_html=True)
            finally:
                if conn: conn.close()

    section("Most recent entries")
    if selected_hospital_id is not None:
        recent = run_query("clinician", """
            SELECT t.treatment_id, t.strain_id, a.name AS antibiotic, t.start_date,
                   o.result, o.follow_up_date
            FROM treatment t
            JOIN strain s ON s.strain_id = t.strain_id
            JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id
            LEFT JOIN outcome o ON o.treatment_id = t.treatment_id
            WHERE s.hospital_id = %s
            ORDER BY t.treatment_id DESC LIMIT 8
        """, (selected_hospital_id,))
    else:
        recent = pd.DataFrame()
    table(recent)

# ================================================================ ADMIN
if selected_role == "Admin":
    st.markdown(
        '<div class="bf-role">bioforge_admin &middot; privileged local-demo access</div>',
        unsafe_allow_html=True,
    )
    st.warning(
        "This role tab is for a trusted local demo only. The app has no user "
        "authentication; do not expose it to untrusted users."
    )
    records_tab, audit_tab = st.tabs(["Recent clinical records", "Audit log"])
    with records_tab:
        section("Recent clinical records", "Active clinician submissions; soft-deleted records are hidden")
        recent_records = run_query(
            "admin",
            """
            SELECT t.treatment_id, t.strain_id, h.name AS hospital,
                   a.name AS antibiotic, t.start_date, t.prescribing_physician,
                   o.result, o.follow_up_date
            FROM treatment t
            JOIN strain s ON s.strain_id = t.strain_id
            LEFT JOIN hospital h ON h.hospital_id = s.hospital_id
            JOIN antibiotic a ON a.antibiotic_id = t.antibiotic_id
            JOIN outcome o ON o.treatment_id = t.treatment_id
            WHERE t.is_active = TRUE AND o.is_active = TRUE
            ORDER BY t.treatment_id DESC
            LIMIT 100
            """,
        )
        if recent_records.empty:
            msg("info", "No active clinical treatment records have been submitted yet.")
        else:
            table(recent_records, max_rows=100)

    with audit_tab:
        section("Audit log", "Updates and soft deletes to treatment and outcome records")
        st.info(
            "New treatment submissions are INSERTs, so they appear under Recent clinical "
            "records. The audit triggers log UPDATEs only, including soft deletes."
        )
        audit_table = st.selectbox(
            "Audited table",
            ["All tables", "treatment", "outcome"],
            key="admin_audit_table",
        )
        audit_sql = """
            SELECT audit_id, table_name, record_id, `action`, old_values, new_values,
                   changed_by, changed_at
            FROM audit_log
        """
        audit_params = ()
        if audit_table != "All tables":
            audit_sql += " WHERE table_name = %s"
            audit_params = (audit_table,)
        audit_sql += " ORDER BY changed_at DESC, audit_id DESC LIMIT 100"
        audit_rows = run_query("admin", audit_sql, audit_params)
        if audit_rows.empty:
            msg("info", "No audit records match that filter.")
        else:
            table(audit_rows, max_rows=100)

# ================================================================ ETL
if selected_role == "ETL":
    st.markdown(
        '<div class="bf-role">bioforge_etl &middot; insert-only data entry</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "This form uses only the ETL account's INSERT permissions for strain, mutation, "
        "and strain_mutation. It cannot read, update, or delete existing records. "
        "Set Hospital ID to 0 for no hospital."
    )
    section("Add strain and mutation", "The strain, mutation, and link are inserted together.")
    with st.form("etl_entry"):
        etl_strain, etl_mutation = st.columns(2)
        with etl_strain:
            etl_hospital_id = st.number_input("Hospital ID (0 = none)", min_value=0, value=0, step=1)
            etl_species = st.text_input("Species", value="Escherichia coli")
            etl_source = st.text_input("Isolate source")
            etl_collection_date = st.date_input("Collection date", value=dt.date.today())
            etl_geography = st.text_input("Geographic origin")
            etl_accession = st.text_input("Genome accession")
        with etl_mutation:
            etl_gene = st.text_input("Gene name")
            etl_mutation_type = st.selectbox(
                "Mutation type",
                ["SNP", "insertion", "deletion", "frameshift", "duplication", "inversion"],
            )
            etl_position = st.number_input("Genome position (0 = unknown)", min_value=0, value=0, step=1)
            etl_ref = st.text_input("Reference allele")
            etl_alt = st.text_input("Alternate allele")
            etl_description = st.text_area("Mutation description")
            etl_detection_date = st.date_input("Detection date", value=dt.date.today())
            etl_method = st.text_input("Sequencing method", value="WGS")
            etl_confidence = st.slider("Confidence score", 0.0, 1.0, 1.0, 0.01)
        etl_submit = st.form_submit_button("Insert ETL records", type="primary")

    if etl_submit:
        etl_conn = None
        try:
            if not etl_species.strip() or not etl_gene.strip():
                raise ValueError("Species and gene name are required.")
            etl_conn = get_connection("etl")
            etl_cur = etl_conn.cursor()
            etl_cur.execute(
                """INSERT INTO strain
                       (hospital_id, species, isolate_source, collection_date,
                        geographic_origin, genome_accession)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    int(etl_hospital_id) or None,
                    etl_species.strip(),
                    etl_source.strip() or None,
                    etl_collection_date,
                    etl_geography.strip() or None,
                    etl_accession.strip() or None,
                ),
            )
            etl_strain_id = etl_cur.lastrowid
            etl_cur.execute(
                """INSERT INTO mutation
                       (gene_name, mutation_type, genome_position, ref_allele, alt_allele, description)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    etl_gene.strip(),
                    etl_mutation_type,
                    int(etl_position) or None,
                    etl_ref.strip() or None,
                    etl_alt.strip() or None,
                    etl_description.strip() or None,
                ),
            )
            etl_mutation_id = etl_cur.lastrowid
            etl_cur.execute(
                """INSERT INTO strain_mutation
                       (strain_id, mutation_id, detection_date, sequencing_method, confidence_score)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    etl_strain_id,
                    etl_mutation_id,
                    etl_detection_date,
                    etl_method.strip() or None,
                    etl_confidence,
                ),
            )
            etl_conn.commit()
            st.success(
                f"Inserted strain #{etl_strain_id}, mutation #{etl_mutation_id}, "
                "and their association."
            )
        except ValueError as e:
            st.error(f"Invalid entry: {e}")
        except mysql.connector.Error as e:
            if etl_conn:
                etl_conn.rollback()
            st.error(f"Database rejected this entry: {e.msg}")
        except Exception as e:
            if etl_conn:
                etl_conn.rollback()
            st.error(f"Unexpected error: {type(e).__name__}: {e}")
        finally:
            if etl_conn:
                etl_conn.close()

st.markdown('<div class="bf-foot">Patient-level data is synthetic for demonstration; '
            'strains marked BV-BRC are real public data.</div>', unsafe_allow_html=True)