// CYBER SHIELD - Complete React Frontend Application
const { useState, useEffect } = React;

function App() {
  const [currentView, setCurrentView] = useState("home"); // home, admin, employee, training
  const [employees, setEmployees] = useState([]);
  const [currentEmployeeId, setCurrentEmployeeId] = useState(1);
  const [stats, setStats] = useState({
    total_employees: 0,
    total_simulations: 0,
    total_clicks: 0,
    total_reported: 0,
    average_awareness: 100
  });
  const [simulations, setSimulations] = useState([]);
  const [selectedSim, setSelectedSim] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [trainingData, setTrainingData] = useState(null);
  const [feedbackAlert, setFeedbackAlert] = useState(null);
  
  // Create Simulation Form State
  const [newSim, setNewSim] = useState({
    title: "",
    sender: "",
    subject: "",
    body_text: "",
    simulated_url: "https://safe-training-domain.local/demo",
    difficulty: "Medium",
    is_suspicious: true,
    red_flags: "Urgency, External Link"
  });
  const [mlResult, setMlResult] = useState(null);
  const [isAnalyzingML, setIsAnalyzingML] = useState(false);

  // Quiz State
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizFeedback, setQuizFeedback] = useState(null);

  // Fetch Core Data
  const loadStats = async () => {
    try {
      const res = await fetch("/api/stats");
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to load stats", err);
    }
  };

  const loadEmployees = async () => {
    try {
      const res = await fetch("/api/employees");
      if (res.ok) {
        const data = await res.json();
        setEmployees(data);
        if (data.length > 0 && !currentEmployeeId) {
          setCurrentEmployeeId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load employees", err);
    }
  };

  const loadSimulations = async () => {
    try {
      const res = await fetch("/api/simulations");
      if (res.ok) {
        const data = await res.json();
        setSimulations(data);
        if (data.length > 0 && !selectedSim) {
          setSelectedSim(data[0]);
        }
      }
    } catch (err) {
      console.error("Failed to load simulations", err);
    }
  };

  const loadInteractions = async () => {
    try {
      const res = await fetch("/api/interactions");
      if (res.ok) {
        const data = await res.json();
        setInteractions(data);
      }
    } catch (err) {
      console.error("Failed to load interactions", err);
    }
  };

  const loadTraining = async (empId) => {
    if (!empId) return;
    try {
      const res = await fetch(`/api/training/${empId}`);
      if (res.ok) {
        const data = await res.json();
        setTrainingData(data);
      }
    } catch (err) {
      console.error("Failed to load training", err);
    }
  };

  useEffect(() => {
    loadStats();
    loadEmployees();
    loadSimulations();
    loadInteractions();
  }, []);

  useEffect(() => {
    if (currentEmployeeId) {
      loadTraining(currentEmployeeId);
    }
  }, [currentEmployeeId]);

  // Handle Employee Action on Simulation
  const handleInteraction = async (action) => {
    if (!selectedSim || !currentEmployeeId) return;
    try {
      const res = await fetch("/api/employee/interact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: currentEmployeeId,
          simulation_id: selectedSim.id,
          action: action
        })
      });
      if (res.ok) {
        const data = await res.json();
        setFeedbackAlert(data.feedback);
        loadStats();
        loadEmployees();
        loadInteractions();
        loadTraining(currentEmployeeId);
      }
    } catch (err) {
      console.error("Error logging interaction", err);
    }
  };

  // Run Scikit-Learn Classifier
  const handleTestML = async () => {
    if (!newSim.body_text && !newSim.subject) return;
    setIsAnalyzingML(true);
    try {
      const text = `${newSim.subject} ${newSim.body_text}`;
      const res = await fetch("/api/ml/predict-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        const data = await res.json();
        setMlResult(data);
      }
    } catch (err) {
      console.error("ML prediction error", err);
    } finally {
      setIsAnalyzingML(false);
    }
  };

  // Create New Simulation
  const handleCreateSimulation = async (e) => {
    e.preventDefault();
    if (!newSim.title || !newSim.subject || !newSim.body_text) return;

    try {
      const res = await fetch("/api/simulations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newSim)
      });
      if (res.ok) {
        const created = await res.json();
        setNewSim({
          title: "",
          sender: "",
          subject: "",
          body_text: "",
          simulated_url: "https://safe-training-domain.local/demo",
          difficulty: "Medium",
          is_suspicious: true,
          red_flags: "Urgency, External Link"
        });
        setMlResult(null);
        loadSimulations();
        loadStats();
        alert("New simulation successfully deployed to employee inboxes!");
      }
    } catch (err) {
      console.error("Error creating simulation", err);
    }
  };

  // Submit Training Quiz
  const handleQuizSubmit = async (e) => {
    e.preventDefault();
    const answersArray = [
      quizAnswers[0] !== undefined ? quizAnswers[0] : -1,
      quizAnswers[1] !== undefined ? quizAnswers[1] : -1,
      quizAnswers[2] !== undefined ? quizAnswers[2] : -1,
      quizAnswers[3] !== undefined ? quizAnswers[3] : -1,
    ];

    try {
      const res = await fetch("/api/training/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: currentEmployeeId,
          answers: answersArray
        })
      });
      if (res.ok) {
        const data = await res.json();
        setQuizFeedback(data);
        loadStats();
        loadEmployees();
        loadTraining(currentEmployeeId);
      }
    } catch (err) {
      console.error("Error submitting quiz", err);
    }
  };

  const activeEmployee = employees.find(e => e.id === Number(currentEmployeeId)) || { name: "Employee" };

  return (
    <div>
      {/* Top Navigation */}
      <nav className="navbar">
        <div className="nav-brand">
          🛡️ CYBER SHIELD
          <span className="tagline">Phishing Simulation & Awareness</span>
        </div>
        <div className="nav-links">
          <button 
            className={`nav-btn ${currentView === "home" ? "active" : ""}`}
            onClick={() => setCurrentView("home")}
          >
            Home
          </button>
          <button 
            className={`nav-btn ${currentView === "admin" ? "active" : ""}`}
            onClick={() => setCurrentView("admin")}
          >
            Admin Dashboard
          </button>
          <button 
            className={`nav-btn ${currentView === "employee" ? "active" : ""}`}
            onClick={() => setCurrentView("employee")}
          >
            Employee Inbox
          </button>
          <button 
            className={`nav-btn ${currentView === "training" ? "active" : ""}`}
            onClick={() => setCurrentView("training")}
          >
            Awareness Training
          </button>
        </div>
        <div className="nav-user-control">
          <span>Active Role:</span>
          <select 
            value={currentEmployeeId} 
            onChange={(e) => setCurrentEmployeeId(Number(e.target.value))}
          >
            {employees.map(emp => (
              <option key={emp.id} value={emp.id}>
                {emp.name} ({emp.role} - {emp.department})
              </option>
            ))}
          </select>
        </div>
      </nav>

      <main className="container">
        {/* Dynamic Global Feedback Banner */}
        {feedbackAlert && (
          <div className={`alert-banner alert-${feedbackAlert.type}`}>
            <div>
              <strong>{feedbackAlert.title}</strong>
              <p style={{ marginTop: "0.25rem", fontSize: "0.88rem" }}>{feedbackAlert.message}</p>
            </div>
            <button 
              className="btn btn-secondary" 
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }}
              onClick={() => setFeedbackAlert(null)}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* VIEW 1: HOME PAGE */}
        {currentView === "home" && (
          <div>
            <section className="hero-section">
              <h1 className="hero-title">CYBER SHIELD</h1>
              <div className="hero-subtitle">Automated Phishing Simulation & Awareness Trainer</div>
              <p className="hero-description">
                Empower your organization with safe, internal simulated phishing exercises and automated awareness training. 
                Evaluate resilience, educate employees on email red flags, and measure security awareness scores in real time.
              </p>
              <div className="hero-actions">
                <button className="btn btn-primary" onClick={() => setCurrentView("employee")}>
                  Open Employee Inbox 📥
                </button>
                <button className="btn btn-secondary" onClick={() => setCurrentView("admin")}>
                  Access Admin Dashboard 📊
                </button>
                <button className="btn btn-secondary" onClick={() => setCurrentView("training")}>
                  View Awareness Training 🛡️
                </button>
              </div>
            </section>

            <div className="home-grid">
              <div className="feature-card">
                <div className="feature-icon">📬</div>
                <h3 className="feature-title">Controlled Safe Simulations</h3>
                <p className="feature-text">
                  Deliver safe educational simulations directly into employee mock inboxes. Zero external leaks and zero credential harvesting.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🧠</div>
                <h3 className="feature-title">Python Rule-Based Learning</h3>
                <p className="feature-text">
                  Automatically calculate risk scores and tailor educational modules based on specific mistakes such as clicking unverified links.
                </p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🤖</div>
                <h3 className="feature-title">Scikit-Learn Ready</h3>
                <p className="feature-text">
                  Built-in TF-IDF and Logistic Regression email classifier to assist administrators in evaluating simulation difficulty and indicators.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: ADMIN PAGE */}
        {currentView === "admin" && (
          <div>
            {/* KPI Cards */}
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-label">Total Employees</span>
                <span className="stat-value">{stats.total_employees}</span>
                <span className="stat-note">Enrolled in awareness</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Total Simulations</span>
                <span className="stat-value">{stats.total_simulations}</span>
                <span className="stat-note">Active simulation templates</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Links Clicked</span>
                <span className="stat-value" style={{ color: "#dc2626" }}>{stats.total_clicks}</span>
                <span className="stat-note">Vulnerable interactions recorded</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Emails Reported</span>
                <span className="stat-value" style={{ color: "#16a34a" }}>{stats.total_reported}</span>
                <span className="stat-note">Proactively flagged by staff</span>
              </div>
            </div>

            {/* Simulation Deployment & ML Evaluation Card */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Deploy New Phishing Simulation</h2>
                <span className="badge badge-blue">Admin Control</span>
              </div>
              <form onSubmit={handleCreateSimulation}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div className="form-group">
                    <label className="form-label">Simulation Title</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. IT Security Update Simulation"
                      value={newSim.title}
                      onChange={e => setNewSim({...newSim, title: e.target.value})}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Sender Email Address</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. support@internal-system-check.net"
                      value={newSim.sender}
                      onChange={e => setNewSim({...newSim, sender: e.target.value})}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Email Subject</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    placeholder="e.g. [SIMULATION] Urgent: Confirm your workstation credentials"
                    value={newSim.subject}
                    onChange={e => setNewSim({...newSim, subject: e.target.value})}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email Body Content</label>
                  <textarea 
                    className="form-control" 
                    rows="4"
                    placeholder="Enter the simulated email text to test employee vigilance..."
                    value={newSim.body_text}
                    onChange={e => setNewSim({...newSim, body_text: e.target.value})}
                    required
                  ></textarea>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
                  <div className="form-group">
                    <label className="form-label">Difficulty Level</label>
                    <select 
                      className="form-control"
                      value={newSim.difficulty}
                      onChange={e => setNewSim({...newSim, difficulty: e.target.value})}
                    >
                      <option value="Easy">Easy (Obvious Red Flags)</option>
                      <option value="Medium">Medium (Subtle Urgency)</option>
                      <option value="Hard">Hard (Targeted Spoofing)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Red Flags Description</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. Lookalike sender, urgent tone"
                      value={newSim.red_flags}
                      onChange={e => setNewSim({...newSim, red_flags: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Safe Training URL</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      value={newSim.simulated_url}
                      onChange={e => setNewSim({...newSim, simulated_url: e.target.value})}
                    />
                  </div>
                </div>

                {/* Scikit-Learn ML Inspection Preview */}
                <div style={{ marginTop: "0.5rem", marginBottom: "1.25rem", display: "flex", gap: "1rem", alignItems: "center" }}>
                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={handleTestML}
                    disabled={isAnalyzingML}
                  >
                    {isAnalyzingML ? "Analyzing with Scikit-learn..." : "🔬 Test with Scikit-Learn Classifier"}
                  </button>
                  {mlResult && (
                    <div style={{ fontSize: "0.85rem" }}>
                      <strong>ML Prediction: </strong> 
                      <span className={`badge ${mlResult.is_phishing ? 'badge-red' : 'badge-green'}`}>
                        {mlResult.prediction_label} ({mlResult.risk_probability}% Risk)
                      </span>
                    </div>
                  )}
                </div>

                <button type="submit" className="btn btn-primary">
                  Deploy Simulation to All Inboxes
                </button>
              </form>
            </div>

            {/* Employee Awareness & Simulation Results Table */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Employee Awareness Performance</h2>
                <span className="badge badge-green">Live SQLite Database</span>
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Department</th>
                      <th>Simulations</th>
                      <th>Links Clicked</th>
                      <th>Reported</th>
                      <th>Awareness Score</th>
                      <th>Risk Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employees.map(emp => {
                      let riskBadge = <span className="badge badge-green">Low Risk</span>;
                      if (emp.awareness_score < 60) {
                        riskBadge = <span className="badge badge-red">High Risk</span>;
                      } else if (emp.awareness_score < 85) {
                        riskBadge = <span className="badge badge-yellow">Medium Risk</span>;
                      }
                      return (
                        <tr key={emp.id}>
                          <td><strong>{emp.name}</strong><br/><span style={{fontSize: "0.78rem", color: "#64748b"}}>{emp.email}</span></td>
                          <td>{emp.department}</td>
                          <td>{emp.simulations_received}</td>
                          <td style={{ color: emp.links_clicked > 0 ? "#dc2626" : "inherit", fontWeight: "600" }}>{emp.links_clicked}</td>
                          <td style={{ color: "#16a34a", fontWeight: "600" }}>{emp.emails_reported}</td>
                          <td><strong>{emp.awareness_score}%</strong></td>
                          <td>{riskBadge}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Real-time Interaction Log Table */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Recent Simulation Interactions Log</h2>
              </div>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Employee</th>
                      <th>Simulation Subject</th>
                      <th>Action Taken</th>
                    </tr>
                  </thead>
                  <tbody>
                    {interactions.length === 0 ? (
                      <tr><td colSpan="4" style={{textAlign: "center", color: "#64748b"}}>No simulation interactions recorded yet.</td></tr>
                    ) : (
                      interactions.map(item => (
                        <tr key={item.id}>
                          <td>{item.timestamp}</td>
                          <td>{item.employee_name}</td>
                          <td>{item.simulation_subject}</td>
                          <td>
                            {item.action === "clicked_link" && <span className="badge badge-red">Clicked Link</span>}
                            {item.action === "reported" && <span className="badge badge-green">Reported Email</span>}
                            {item.action === "opened" && <span className="badge badge-blue">Opened</span>}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: EMPLOYEE PAGE (SIMULATED INBOX) */}
        {currentView === "employee" && (
          <div>
            <div style={{ marginBottom: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "1.4rem", fontWeight: "700" }}>Simulated Internal Inbox</h2>
                <p style={{ fontSize: "0.88rem", color: "#64748b" }}>
                  Logged in as: <strong>{activeEmployee.name}</strong> ({activeEmployee.department}) | Current Awareness Score: <strong>{activeEmployee.awareness_score}%</strong>
                </p>
              </div>
              <button className="btn btn-secondary" onClick={() => setCurrentView("training")}>
                View My Awareness Training 🛡️
              </button>
            </div>

            <div className="inbox-layout">
              {/* Inbox Sidebar */}
              <div className="inbox-sidebar">
                <div className="inbox-sidebar-header">
                  Simulated Messages ({simulations.length})
                </div>
                <ul className="inbox-email-list">
                  {simulations.map(sim => (
                    <li 
                      key={sim.id}
                      className={`inbox-email-item ${selectedSim && selectedSim.id === sim.id ? "active" : ""}`}
                      onClick={() => setSelectedSim(sim)}
                    >
                      <div className="email-item-sender">{sim.sender}</div>
                      <div className="email-item-subject">{sim.subject}</div>
                      <div className="email-item-snippet">{sim.body_text}</div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Email Reader Pane */}
              <div className="inbox-reader">
                {selectedSim ? (
                  <div>
                    <div className="reader-header">
                      <h3 className="reader-subject">{selectedSim.subject}</h3>
                      <div className="reader-meta-row">
                        <div className="reader-sender">
                          From: <span>{selectedSim.sender}</span>
                        </div>
                        <div>
                          <span className="badge badge-blue">Difficulty: {selectedSim.difficulty}</span>
                        </div>
                      </div>
                    </div>

                    <div className="reader-body">
                      {selectedSim.body_text}
                    </div>

                    {selectedSim.simulated_url && (
                      <div className="reader-link-box">
                        <strong>Simulated Embedded Link: </strong>
                        <a 
                          href="#simulate" 
                          onClick={(e) => { e.preventDefault(); handleInteraction("clicked_link"); }}
                          style={{ color: "#2563eb", textDecoration: "underline" }}
                        >
                          {selectedSim.simulated_url}
                        </a>
                      </div>
                    )}

                    <div className="reader-actions">
                      <button 
                        className="btn btn-danger" 
                        onClick={() => handleInteraction("clicked_link")}
                      >
                        ⚠️ Click Simulated Link (Test Interaction)
                      </button>
                      <button 
                        className="btn btn-success" 
                        onClick={() => handleInteraction("reported")}
                      >
                        🛡️ Report Email as Phishing
                      </button>
                      <button 
                        className="btn btn-secondary" 
                        onClick={() => handleInteraction("opened")}
                      >
                        Mark as Reviewed
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: "center", padding: "4rem 1rem", color: "#64748b" }}>
                    Select a simulated email from the list to review it.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* VIEW 4: AWARENESS TRAINING & QUIZ */}
        {currentView === "training" && (
          <div>
            <div style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontSize: "1.4rem", fontWeight: "700" }}>Phishing Awareness Training Center</h2>
              <p style={{ fontSize: "0.88rem", color: "#64748b" }}>
                Personalized lessons for <strong>{activeEmployee.name}</strong> based on interaction history. Current Score: <strong>{activeEmployee.awareness_score}%</strong>
              </p>
            </div>

            {/* Phishing Warning Signs & Tailored Lessons */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Assigned Training Modules</h3>
                <span className="badge badge-blue">Python Rule Engine</span>
              </div>

              {trainingData && trainingData.lessons.map(lesson => (
                <div key={lesson.id} className="lesson-card">
                  <div className="lesson-title">{lesson.title}</div>
                  <div className="lesson-summary">{lesson.summary}</div>
                  <ul className="lesson-list">
                    {lesson.details.map((point, idx) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Interactive Awareness Quiz */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Phishing Awareness Quick Quiz</h3>
                <span className="badge badge-green">Knowledge Check</span>
              </div>

              {quizFeedback && (
                <div className="alert-banner alert-info" style={{ marginBottom: "1.5rem" }}>
                  <div>
                    <strong>{quizFeedback.message}</strong>
                    <p style={{ fontSize: "0.85rem", marginTop: "0.2rem" }}>
                      Your updated awareness score is now: <strong>{quizFeedback.updated_awareness_score}%</strong>
                    </p>
                  </div>
                </div>
              )}

              <form onSubmit={handleQuizSubmit}>
                <div className="quiz-question-block">
                  <div className="quiz-question-title">
                    1. You receive an urgent email from "HR Benefits" asking you to immediately verify your direct deposit password on an external site. What should you do?
                  </div>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q0" 
                      checked={quizAnswers[0] === 0} 
                      onChange={() => setQuizAnswers({...quizAnswers, 0: 0})} 
                    />
                    Immediately click the link and re-enter your password to prevent payroll delays.
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q0" 
                      checked={quizAnswers[0] === 1} 
                      onChange={() => setQuizAnswers({...quizAnswers, 0: 1})} 
                    />
                    Report the email as suspicious and verify directly with HR via official company channels. (Correct)
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q0" 
                      checked={quizAnswers[0] === 2} 
                      onChange={() => setQuizAnswers({...quizAnswers, 0: 2})} 
                    />
                    Forward the email to all colleagues in your department.
                  </label>
                </div>

                <div className="quiz-question-block">
                  <div className="quiz-question-title">
                    2. When inspecting a hyperlink in an email, which technique helps reveal the true destination?
                  </div>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q1" 
                      checked={quizAnswers[1] === 0} 
                      onChange={() => setQuizAnswers({...quizAnswers, 1: 0})} 
                    />
                    Click the link as fast as possible to see where it redirects.
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q1" 
                      checked={quizAnswers[1] === 1} 
                      onChange={() => setQuizAnswers({...quizAnswers, 1: 1})} 
                    />
                    Only trust the text displayed in the email body.
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q1" 
                      checked={quizAnswers[1] === 2} 
                      onChange={() => setQuizAnswers({...quizAnswers, 1: 2})} 
                    />
                    Hover your mouse over the link to preview the actual destination URL. (Correct)
                  </label>
                </div>

                <div className="quiz-question-block">
                  <div className="quiz-question-title">
                    3. Which of the following is the most common red flag of a phishing attempt?
                  </div>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q2" 
                      checked={quizAnswers[2] === 0} 
                      onChange={() => setQuizAnswers({...quizAnswers, 2: 0})} 
                    />
                    Extreme urgency, fear tactics, or threats of account suspension. (Correct)
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q2" 
                      checked={quizAnswers[2] === 1} 
                      onChange={() => setQuizAnswers({...quizAnswers, 2: 1})} 
                    />
                    An invitation to a recurring team meeting from your manager's verified address.
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q2" 
                      checked={quizAnswers[2] === 2} 
                      onChange={() => setQuizAnswers({...quizAnswers, 2: 2})} 
                    />
                    A weekly company newsletter sent through internal mailing lists.
                  </label>
                </div>

                <div className="quiz-question-block">
                  <div className="quiz-question-title">
                    4. If you accidentally click a simulated phishing link during a training drill, what is the best immediate response?
                  </div>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q3" 
                      checked={quizAnswers[3] === 0} 
                      onChange={() => setQuizAnswers({...quizAnswers, 3: 0})} 
                    />
                    Shut down your computer and do not tell anyone.
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q3" 
                      checked={quizAnswers[3] === 1} 
                      onChange={() => setQuizAnswers({...quizAnswers, 3: 1})} 
                    />
                    Review the training feedback, learn the red flags, and report suspicious messages promptly. (Correct)
                  </label>
                  <label className="quiz-option">
                    <input 
                      type="radio" 
                      name="q3" 
                      checked={quizAnswers[3] === 2} 
                      onChange={() => setQuizAnswers({...quizAnswers, 3: 2})} 
                    />
                    Enter fictitious credentials into the website form.
                  </label>
                </div>

                <button type="submit" className="btn btn-primary">
                  Submit Quiz & Update Awareness Score
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// Render into DOM
const rootElement = document.getElementById("root");
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
