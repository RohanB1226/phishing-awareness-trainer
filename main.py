import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Scikit-learn minimal TF-IDF & Logistic Regression integration
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# --- Database Setup (SQLite persistence) ---
DB_FILE = "database.db"
DATABASE_URL = f"sqlite:///./{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String, default="General")
    role = Column(String, default="Employee")
    awareness_score = Column(Float, default=100.0)
    simulations_received = Column(Integer, default=0)
    links_clicked = Column(Integer, default=0)
    emails_reported = Column(Integer, default=0)

class Simulation(Base):
    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body_text = Column(String, nullable=False)
    simulated_url = Column(String, default="https://safe-training-domain.local/verify")
    difficulty = Column(String, default="Medium")
    is_suspicious = Column(Boolean, default=True)
    red_flags = Column(String, default="Urgency, Unverified Link")
    created_at = Column(DateTime, default=datetime.utcnow)

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    simulation_id = Column(Integer, ForeignKey("simulations.id"))
    action = Column(String, nullable=False)  # opened, clicked_link, reported
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, default="")

class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- Minimal Scikit-Learn Classifier ---
def init_ml_pipeline():
    sample_texts = [
        "Urgent action required: verify your login details immediately or account will be suspended.",
        "Security alert: unauthorized login attempt detected. Click here to confirm credentials.",
        "Claim your prize voucher immediately! Submit details to receive reward.",
        "Payroll notice: update your direct deposit banking information within 24 hours.",
        "Invoice payment overdue. Open the attached file right away to avoid penalty.",
        "Team meeting tomorrow at 10 AM in Conference Room B. Please review the agenda.",
        "Project status update: the Q3 roadmap has been shared on the internal drive.",
        "Monthly company newsletter: celebrating new hires and team accomplishments.",
        "Weekly engineering sync notes and sprint planning documentation.",
        "Reminder: scheduled office network maintenance this Saturday evening."
    ]
    labels = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    
    pipe = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', lowercase=True)),
        ('clf', LogisticRegression())
    ])
    pipe.fit(sample_texts, labels)
    return pipe

ml_classifier = init_ml_pipeline()

# --- Seed Initial Safe Simulation Data ---
def seed_database():
    db = SessionLocal()
    try:
        if db.query(Employee).count() == 0:
            demo_employees = [
                Employee(name="Alex Rivera", email="alex.rivera@cybershield.corp", department="Finance", role="Employee", awareness_score=85.0, simulations_received=3, links_clicked=1, emails_reported=2),
                Employee(name="Samantha Chen", email="samantha.chen@cybershield.corp", department="Human Resources", role="Employee", awareness_score=95.0, simulations_received=3, links_clicked=0, emails_reported=3),
                Employee(name="Marcus Taylor", email="marcus.taylor@cybershield.corp", department="IT Operations", role="Employee", awareness_score=70.0, simulations_received=4, links_clicked=2, emails_reported=1),
                Employee(name="Elena Rostova", email="elena.rostova@cybershield.corp", department="Security Administration", role="Admin", awareness_score=100.0, simulations_received=0, links_clicked=0, emails_reported=0)
            ]
            db.add_all(demo_employees)
            db.commit()

        if db.query(Simulation).count() == 0:
            demo_simulations = [
                Simulation(
                    title="Simulated Urgent Account Verification",
                    sender="security-notify@corporate-alert-services.biz",
                    subject="[SIMULATION] Urgent: Action required on your corporate profile",
                    body_text="Hello, we noticed abnormal activity on your workstation profile. Please verify your login session immediately by clicking the link below to avoid service interruption.\n\nSimulated Training URL: https://safe-training-domain.local/profile-check",
                    simulated_url="https://safe-training-domain.local/profile-check",
                    difficulty="Medium",
                    is_suspicious=True,
                    red_flags="Artificial Urgency, Lookalike Sender Domain, Ambiguous Call to Action"
                ),
                Simulation(
                    title="Simulated Unexpected Delivery Notice",
                    sender="tracking@express-parcels-center.com",
                    subject="[SIMULATION] Delivery exception: Confirm destination address",
                    body_text="Your package shipment could not be delivered to the reception desk. Check your delivery status and reconfirm address details at our portal.\n\nSimulated Training URL: https://safe-training-domain.local/delivery-update",
                    simulated_url="https://safe-training-domain.local/delivery-update",
                    difficulty="Easy",
                    is_suspicious=True,
                    red_flags="Unexpected Logistics Notification, External Link, Generic Salutation"
                ),
                Simulation(
                    title="Simulated Routine All-Hands Meeting Invitation",
                    sender="internal-comms@cybershield.corp",
                    subject="Quarterly All-Hands Meeting - Next Thursday 2:00 PM",
                    body_text="Hi Team,\n\nPlease find the invitation for our upcoming Quarterly All-Hands briefing. We will review our departmental milestones and celebrate key wins. No external action or credentials needed.",
                    simulated_url="",
                    difficulty="Easy",
                    is_suspicious=False,
                    red_flags="None (Legitimate internal announcement)"
                )
            ]
            db.add_all(demo_simulations)
            db.commit()
    finally:
        db.close()

seed_database()

# --- FastAPI Application ---
app = FastAPI(title="CYBER SHIELD - Automated Phishing Simulation & Awareness Trainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schemas ---
class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str = "General"
    role: str = "Employee"

class SimulationCreate(BaseModel):
    title: str
    sender: str
    subject: str
    body_text: str
    simulated_url: Optional[str] = "https://safe-training-domain.local/demo"
    difficulty: str = "Medium"
    is_suspicious: bool = True
    red_flags: str = "Urgency, External Link"

class InteractionCreate(BaseModel):
    employee_id: int
    simulation_id: int
    action: str  # "opened", "clicked_link", "reported"

class QuizSubmit(BaseModel):
    employee_id: int
    answers: List[int]

class MLPredictRequest(BaseModel):
    text: str

# --- Static Frontend Serving Routes ---
@app.get("/", response_class=HTMLResponse)
def serve_index():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYBER SHIELD - Phishing Simulation & Awareness Trainer</title>
    <link rel="stylesheet" href="/style.css">
    <!-- React & Babel via CDN -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel" src="/App.jsx"></script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.get("/style.css")
def serve_css():
    if os.path.exists("style.css"):
        return FileResponse("style.css", media_type="text/css")
    return HTMLResponse(content="/* style.css pending */", media_type="text/css")

@app.get("/App.jsx")
def serve_app_jsx():
    if os.path.exists("App.jsx"):
        return FileResponse("App.jsx", media_type="text/plain")
    return HTMLResponse(content="// App.jsx pending", media_type="text/plain")

# --- Backend API Endpoints ---
@app.get("/api/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_employees = db.query(Employee).count()
    total_simulations = db.query(Simulation).count()
    total_clicks = db.query(Interaction).filter(Interaction.action == "clicked_link").count()
    total_reports = db.query(Interaction).filter(Interaction.action == "reported").count()
    
    employees = db.query(Employee).all()
    avg_awareness = round(sum(e.awareness_score for e in employees) / total_employees, 1) if total_employees > 0 else 100.0
    
    return {
        "total_employees": total_employees,
        "total_simulations": total_simulations,
        "total_clicks": total_clicks,
        "total_reported": total_reports,
        "average_awareness": avg_awareness
    }

@app.get("/api/employees")
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

@app.post("/api/employees")
def add_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.email == emp.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    new_emp = Employee(
        name=emp.name,
        email=emp.email,
        department=emp.department,
        role=emp.role,
        awareness_score=100.0
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp

@app.get("/api/simulations")
def list_simulations(db: Session = Depends(get_db)):
    return db.query(Simulation).all()

@app.post("/api/simulations")
def create_simulation(sim: SimulationCreate, db: Session = Depends(get_db)):
    new_sim = Simulation(
        title=sim.title,
        sender=sim.sender,
        subject=sim.subject,
        body_text=sim.body_text,
        simulated_url=sim.simulated_url,
        difficulty=sim.difficulty,
        is_suspicious=sim.is_suspicious,
        red_flags=sim.red_flags
    )
    db.add(new_sim)
    
    employees = db.query(Employee).all()
    for e in employees:
        e.simulations_received += 1
        
    db.commit()
    db.refresh(new_sim)
    return new_sim

@app.get("/api/interactions")
def list_interactions(db: Session = Depends(get_db)):
    interactions = db.query(Interaction).order_by(Interaction.timestamp.desc()).limit(20).all()
    result = []
    for item in interactions:
        emp = db.query(Employee).filter(Employee.id == item.employee_id).first()
        sim = db.query(Simulation).filter(Simulation.id == item.simulation_id).first()
        result.append({
            "id": item.id,
            "employee_name": emp.name if emp else "Unknown",
            "employee_email": emp.email if emp else "N/A",
            "simulation_subject": sim.subject if sim else "General",
            "action": item.action,
            "timestamp": item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return result

@app.post("/api/employee/interact")
def record_interaction(interaction_in: InteractionCreate, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == interaction_in.employee_id).first()
    sim = db.query(Simulation).filter(Simulation.id == interaction_in.simulation_id).first()
    if not emp or not sim:
        raise HTTPException(status_code=404, detail="Employee or Simulation not found")

    interaction = Interaction(
        employee_id=emp.id,
        simulation_id=sim.id,
        action=interaction_in.action
    )
    db.add(interaction)

    if interaction_in.action == "clicked_link":
        emp.links_clicked += 1
        emp.awareness_score = max(10.0, round(emp.awareness_score - 20.0, 1))
        feedback = {
            "type": "warning",
            "title": "Simulation Alert: You clicked a simulated training link!",
            "message": "In a real phishing scenario, clicking this link could pose a security hazard. Notice the indicators: " + sim.red_flags
        }
    elif interaction_in.action == "reported":
        emp.emails_reported += 1
        emp.awareness_score = min(100.0, round(emp.awareness_score + 10.0, 1))
        feedback = {
            "type": "success",
            "title": "Excellent Job! You successfully reported this simulation.",
            "message": "Reporting suspicious emails protects the entire organization. Great awareness!"
        }
    else:
        feedback = {
            "type": "info",
            "title": "Email Opened",
            "message": "Always inspect the sender address and links before taking action."
        }

    db.commit()
    db.refresh(emp)

    return {
        "status": "recorded",
        "employee_score": emp.awareness_score,
        "feedback": feedback
    }

@app.get("/api/training/{employee_id}")
def get_employee_training(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    assigned_lessons = []
    
    assigned_lessons.append({
        "id": "intro_signs",
        "title": "Core Phishing Warning Signs",
        "summary": "Learn to inspect email senders, detect lookalike domains, and spot deceptive urgent calls to action.",
        "details": [
            "Always check sender email addresses carefully, not just the display name.",
            "Look for artificial urgency (e.g., 'Within 24 hours', 'Immediate Action').",
            "Hover over links to verify the actual destination URL before clicking.",
            "Never submit passwords or sensitive credentials through unverified forms."
        ]
    })

    if emp.links_clicked > 0:
        assigned_lessons.append({
            "id": "url_inspection",
            "title": "Targeted Module: Safe Link & Hyperlink Inspection",
            "summary": "Because simulated links were clicked in your inbox, review how attackers disguise malicious URLs.",
            "details": [
                "Examine the domain suffix: watch out for extra subdomains like '.biz', '.center', or typosquatting.",
                "Verify with IT or Security teams via an official secondary channel when in doubt.",
                "Use the 'Report Phishing' button rather than testing links manually."
            ]
        })

    if emp.awareness_score < 80:
        assigned_lessons.append({
            "id": "urgency_psychology",
            "title": "Targeted Module: Social Engineering & Urgency Tactics",
            "summary": "Refresher on how social engineering preys on urgency, authority, and fear of consequences.",
            "details": [
                "Attackers impersonate executives, HR representatives, or IT support.",
                "Take a deep breath and pause before reacting to high-pressure requests.",
                "Legitimate organizational administrators will never ask for your private passwords."
            ]
        })

    return {
        "employee_name": emp.name,
        "awareness_score": emp.awareness_score,
        "links_clicked": emp.links_clicked,
        "emails_reported": emp.emails_reported,
        "lessons": assigned_lessons
    }

@app.post("/api/training/quiz")
def submit_quiz(submission: QuizSubmit, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == submission.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    correct_answers = [1, 2, 0, 1]
    score = 0
    total = len(correct_answers)

    for i, ans in enumerate(submission.answers):
        if i < total and ans == correct_answers[i]:
            score += 1

    quiz_rec = QuizSubmission(employee_id=emp.id, score=score, total=total)
    db.add(quiz_rec)

    bonus = round((score / total) * 15.0, 1)
    emp.awareness_score = min(100.0, round(emp.awareness_score + bonus, 1))
    db.commit()

    return {
        "score": score,
        "total": total,
        "updated_awareness_score": emp.awareness_score,
        "message": f"Quiz submitted! You got {score} out of {total} correct."
    }

@app.post("/api/ml/predict-email")
def ml_predict_email(req: MLPredictRequest):
    if not req.text.strip():
        return {"prediction": "Inconclusive", "risk_probability": 0.0, "is_phishing": False}
    
    prob = ml_classifier.predict_proba([req.text])[0][1]
    is_phishing = bool(prob >= 0.5)
    
    return {
        "is_phishing": is_phishing,
        "risk_probability": round(float(prob) * 100, 2),
        "prediction_label": "Potential Phishing Risk" if is_phishing else "Likely Benign Communication",
        "algorithm": "Scikit-Learn (TF-IDF Vectorizer + Logistic Regression)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
