import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";


import { useEffect, useState } from "react";
import "./App.css";

const DEMO_REPORT = `During crane lifting operations, a worker entered the exclusion zone beneath a suspended load. The load suddenly shifted while being positioned and moved toward the worker. The lifting operation was immediately stopped.`;

function App() {
  const [report, setReport] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState("");

  const analyzeReport = async () => {
    if (!report.trim()) {
      setError("Please enter a safety report.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          report_text: report,
        }),
      });

      const data = await response.json();

      if (!response.ok || data.status === "error") {
        throw new Error(data.message || "Analysis failed.");
      }

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the AI backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = () => {
    setReport(DEMO_REPORT);
    setResult(null);
    setError("");
  };

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/dashboard");
        const data = await response.json();
        if (!response.ok || data.status === "error") {
          throw new Error(data.message || "Dashboard loading failed.");
        }
        setDashboard(data);
      } catch (err) {
        console.error(err);
        setDashboardError(
          "Unable to load dashboard data. Make sure FastAPI is running."
        );
      } finally {
        setDashboardLoading(false);
      }
    };

    loadDashboard();
  }, []);

  return (
    <div className="app">

      {/* ================= HEADER ================= */}
      <header className="header">
        <div>
          <div className="brand">INNOMINDS</div>

          <h1>SIF Intelligence Engine</h1>

          <p>
            AI-powered safety report analysis and Life-Saving Rule intelligence
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          AI ENGINE ONLINE
        </div>
      </header>


      {/* ================= MAIN ================= */}
      <main className="container">

        {/* ================= HERO ================= */}
        <section className="hero">
          <div>
            <span className="eyebrow">
              SAFETY INTELLIGENCE
            </span>

            <h2>
              Turn safety reports into actionable intelligence.
            </h2>

            <p>
              Identify SIF potential, map Life-Saving Rules, and surface
              critical safety indicators from unstructured reports.
            </p>
          </div>
        </section>


        {/* ================= ANALYZER ================= */}
        <section className="analyzer-grid">

          {/* ---------- INPUT ---------- */}
          <div className="card input-card">

            <div className="card-header">

              <div>
                <span className="section-label">
                  REPORT ANALYZER
                </span>

                <h3>
                  Safety Report
                </h3>
              </div>

              <button
                className="secondary-btn"
                onClick={loadDemo}
              >
                Load Demo
              </button>

            </div>


            <textarea
              value={report}
              onChange={(e) => setReport(e.target.value)}
              placeholder="Paste a safety report here..."
            />


            {error && (
              <div className="error">
                {error}
              </div>
            )}


            <button
              className="analyze-btn"
              onClick={analyzeReport}
              disabled={loading}
            >
              {loading
                ? "Analyzing..."
                : "Analyze Safety Report"}
            </button>

          </div>


          {/* ---------- RESULTS ---------- */}
          <div className="card result-card">

            <div className="card-header">

              <div>
                <span className="section-label">
                  AI ANALYSIS
                </span>

                <h3>
                  Risk Assessment
                </h3>
              </div>

            </div>


            {/* ---------- EMPTY ---------- */}
            {!result && !loading && (
              <div className="empty-state">

                <div className="empty-icon">
                  AI
                </div>

                <h4>
                  Ready for analysis
                </h4>

                <p>
                  Enter a safety report and run the AI engine
                  to generate safety intelligence.
                </p>

              </div>
            )}


            {/* ---------- LOADING ---------- */}
            {loading && (
              <div className="empty-state">

                <div className="loader"></div>

                <h4>
                  Analyzing report...
                </h4>

                <p>
                  Running SIF detection, event extraction
                  and rule mapping.
                </p>

              </div>
            )}


            {/* ---------- RESULT ---------- */}
            {result && (
              <AnalysisResult data={result} />
            )}

          </div>

        </section>

        <RiskDashboard
          data={dashboard}
          loading={dashboardLoading}
          error={dashboardError}
        />

      </main>

    </div>
  );
}


/* =====================================================
   RISK DASHBOARD
===================================================== */

function RiskDashboard({ data, loading, error }) {
  if (loading) {
    return (
      <section className="dashboard-section">
        <div className="card dashboard-card">
          <span className="section-label">RISK DASHBOARD</span>
          <h3>Loading safety intelligence...</h3>
          <div className="dashboard-loading">
            <div className="loader"></div>
            <p>Loading precursor analytics from the safety dataset.</p>
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="dashboard-section">
        <div className="card dashboard-card">
          <span className="section-label">RISK DASHBOARD</span>
          <h3>Dashboard unavailable</h3>
          <div className="error">{error || "No dashboard data available."}</div>
        </div>
      </section>
    );
  }

  const chartData = data.sif_vs_non_sif || [];

  return (
    <section className="dashboard-section">
      <div className="dashboard-title">
        <div>
          <span className="section-label">RISK DASHBOARD</span>
          <h2>Recurring SIF precursor intelligence.</h2>
          <p>
            Aggregate safety signals to help HSE teams identify recurring
            high-risk activities, hazards and barrier failures.
          </p>
        </div>
      </div>

      <div className="dashboard-kpis">
        <DashboardKPI label="Total Reports" value={Number(data.total_reports || 0).toLocaleString()} />
        <DashboardKPI label="SIF-Potential" value={Number(data.sif_potential || 0).toLocaleString()} danger />
        <DashboardKPI label="Non-SIF" value={Number(data.non_sif || 0).toLocaleString()} />
        <DashboardKPI label="High Priority" value={Number(data.high_priority || 0).toLocaleString()} danger />
      </div>

      <div className="dashboard-two-column">
        <div className="card dashboard-panel">
          <div className="panel-heading">
            <div>
              <span className="section-label">DISTRIBUTION</span>
              <h3>SIF vs Non-SIF</h3>
            </div>
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={52}
                  paddingAngle={3}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-legend">
            {chartData.map((item, index) => (
              <div className="legend-item" key={index}>
                <span className="legend-dot"></span>
                <span>{item.name}</span>
                <strong>{Number(item.count).toLocaleString()}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="card dashboard-panel insight-panel">
          <span className="section-label">HSE INSIGHT</span>
          <h3>Recurring precursor signal</h3>
          <p>{data.insight}</p>
          <div className="insight-highlight">
            <strong>Priority focus</strong>
            <span>
              Review recurring combinations of activity, hazard and failed
              safety barriers.
            </span>
          </div>
        </div>
      </div>

      <div className="dashboard-three-column">
        <DashboardList title="Top Activities" items={data.top_activities} />
        <DashboardList title="Top Hazards" items={data.top_hazards} />
        <DashboardList title="Top Barrier Failures" items={data.top_barriers} />
      </div>

      <div className="card dashboard-panel">
        <div className="panel-heading">
          <div>
            <span className="section-label">IOGP</span>
            <h3>Top Life-Saving Rules</h3>
          </div>
        </div>

        <div className="rule-ranking">
          {(data.top_life_saving_rules || []).map((item, index) => (
            <div className="rule-ranking-row" key={index}>
              <span className="ranking-number">{index + 1}</span>
              <span className="ranking-name">{item.name}</span>
              <strong>{Number(item.count).toLocaleString()}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="card dashboard-panel">
        <div className="panel-heading">
          <div>
            <span className="section-label">PRECURSOR INTELLIGENCE</span>
            <h3>Recurring Precursor Patterns</h3>
          </div>
        </div>

        <div className="precursor-list">
          {(data.recurring_precursors || []).map((item, index) => (
            <div className="precursor-row" key={index}>
              <div className="precursor-number">{index + 1}</div>
              <div className="precursor-content">
                <strong>{item.activity}</strong>
                <span>{item.hazard} → {item.barrier_failure}</span>
              </div>
              <div className="precursor-count">
                {Number(item.count).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-disclaimer">
        <strong>Prototype data note:</strong> {data.disclaimer}
      </div>
    </section>
  );
}

function DashboardKPI({ label, value, danger = false }) {
  return (
    <div className={`dashboard-kpi ${danger ? "dashboard-kpi-danger" : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DashboardList({ title, items = [] }) {
  const max = Math.max(...items.map((item) => Number(item.count) || 0), 1);

  return (
    <div className="card dashboard-panel dashboard-list-panel">
      <div className="panel-heading">
        <h3>{title}</h3>
      </div>

      <div className="dashboard-list">
        {items.map((item, index) => {
          const count = Number(item.count) || 0;
          const width = Math.max((count / max) * 100, 5);

          return (
            <div className="list-item" key={index}>
              <div className="list-item-top">
                <span>{item.name}</span>
                <strong>{count.toLocaleString()}</strong>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${width}%` }}></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


/* =====================================================
   ANALYSIS RESULT
===================================================== */

function AnalysisResult({ data }) {

  /*
   * Backend structure:
   *
   * sif_analysis
   *    ├── sif_classification
   *    │      ├── label
   *    │      ├── confidence
   *    │      ├── ml_score
   *    │      ├── safety_score
   *    │      ├── priority
   *    │      ├── indicators
   *    │      └── reasons
   *    │
   *    ├── event_count
   *    └── events
   */

  const sifAnalysis = data.sif_analysis || {};

  const sif =
    sifAnalysis.sif_classification || {};

  const events =
    sifAnalysis.events || [];

  const rules =
    data.life_saving_rules || [];


  /* ---------- SIF CLASSIFICATION ---------- */

  const isSif =
    sif.label === "SIF-POTENTIAL";


  /* ---------- INDICATORS ---------- */

  const indicators =
    Array.isArray(sif.indicators)
      ? sif.indicators
      : [];


  /* ---------- REASONS ---------- */

  const reasons =
    Array.isArray(sif.reasons)
      ? sif.reasons
      : [];


  /* ---------- SCORES ---------- */

  const safetyScore =
    typeof sif.safety_score === "number"
      ? Math.round(sif.safety_score * 100)
      : null;

  const mlScore =
    typeof sif.ml_score === "number"
      ? Math.round(sif.ml_score * 100)
      : null;


  return (
    <div className="results">


      {/* =================================================
         SIF BANNER
      ================================================= */}

      <div
        className={`sif-banner ${
          isSif ? "danger" : "safe"
        }`}
      >

        <div>

          <span className="result-label">
            SIF POTENTIAL
          </span>

          <strong>
            {isSif
              ? "SIF-POTENTIAL"
              : "NON-SIF-POTENTIAL"}
          </strong>

        </div>


        <div className="priority">
          {sif.priority || "LOW"}
        </div>

      </div>


      {/* =================================================
         METRICS
      ================================================= */}

      <div className="metrics">

        <Metric
          title="Safety Score"
          value={
            safetyScore !== null
              ? `${safetyScore}%`
              : "—"
          }
        />

        <Metric
          title="ML Score"
          value={
            mlScore !== null
              ? `${mlScore}%`
              : "—"
          }
        />

        <Metric
          title="Priority"
          value={sif.priority || "LOW"}
        />

      </div>


      {/* =================================================
         CRITICAL INDICATORS
      ================================================= */}

      {indicators.length > 0 && (

        <div className="result-section">

          <h4>
            Critical Safety Indicators
          </h4>


          <div className="tag-list">

            {indicators.map(
              (indicator, index) => (

                <span
                  className="tag danger-tag"
                  key={index}
                >

                  {typeof indicator === "object"
                    ? indicator.name ||
                      indicator.type ||
                      indicator.indicator ||
                      "Critical Safety Indicator"
                    : String(indicator)}

                </span>

              )
            )}

          </div>

        </div>

      )}


      {/* =================================================
         REASONS
      ================================================= */}

      {reasons.length > 0 && (

        <div className="result-section">

          <h4>
            Why was this classified?
          </h4>


          <ul className="reason-list">

            {reasons.map(
              (reason, index) => (

                <li key={index}>
                  {String(reason)}
                </li>

              )
            )}

          </ul>

        </div>

      )}


      {/* =================================================
         SAFETY EVENT
      ================================================= */}

      {events.length > 0 && (

        <div className="result-section">

          <h4>
            Safety Event
          </h4>


          {events.map(
            (event, index) => (

              <div
                className="event-box"
                key={index}
              >

                <div className="event-row">

                  <span>
                    Activity
                  </span>

                  <strong>
                    {event.activity || "—"}
                  </strong>

                </div>


                <div className="event-row">

                  <span>
                    Hazard
                  </span>

                  <strong>
                    {event.hazard || "—"}
                  </strong>

                </div>


                <div className="event-row">

                  <span>
                    Barrier Failure
                  </span>

                  <strong>
                    {event.barrier_failure || "—"}
                  </strong>

                </div>


                <div className="event-row">

                  <span>
                    Consequence
                  </span>

                  <strong>
                    {event.consequence || "—"}
                  </strong>

                </div>


                {event.evidence &&
                  event.evidence.length > 0 && (

                    <div className="evidence-box">

                      <span>
                        Evidence
                      </span>

                      <ul>

                        {event.evidence.map(
                          (sentence, evidenceIndex) => (

                            <li
                              key={evidenceIndex}
                            >
                              {sentence}
                            </li>

                          )
                        )}

                      </ul>

                    </div>

                  )}

              </div>

            )
          )}

        </div>

      )}


      {/* =================================================
         IOGP LIFE-SAVING RULE
      ================================================= */}

      {rules.length > 0 && (

        <div className="result-section">

          <h4>
            IOGP Life-Saving Rule
          </h4>


          <div className="rule-box">

            <strong>
              {rules[0].rule ||
                "Rule not identified"}
            </strong>


            <span>

              {rules[0].match_strength ||
                "Supporting"}

              {" · "}

              {rules[0].match_type ||
                "Semantic match"}

            </span>

          </div>


          {/* ---------- SUPPORTING RULES ---------- */}

          {rules.length > 1 && (

            <div className="supporting-rules">

              <span>
                Supporting Rules
              </span>

              <div className="tag-list">

                {rules
                  .slice(1)
                  .map(
                    (rule, index) => (

                      <span
                        className="tag supporting-tag"
                        key={index}
                      >
                        {rule.rule}
                      </span>

                    )
                  )}

              </div>

            </div>

          )}

        </div>

      )}


      {/* =================================================
         SAFETY OVERRIDE
      ================================================= */}

      {sif.override_applied && (

        <div className="info-box">

          <strong>
            Safety override applied
          </strong>

          <p>
            A critical high-energy safety indicator
            was detected and used to prioritize the
            report for SIF review.
          </p>

        </div>

      )}

    </div>
  );
}


/* =====================================================
   METRIC COMPONENT
===================================================== */

function Metric({ title, value }) {

  return (

    <div className="metric">

      <span>
        {title}
      </span>

      <strong>
        {value}
      </strong>

    </div>

  );
}


export default App;