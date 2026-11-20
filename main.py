import os
import random
from datetime import datetime
from typing import List, Optional, Dict
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
    action = Column(String, nullable=False)  # opened, clicked_link, reported, marked_safe
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

# --- Dynamic Cybersecurity Question Bank ---
QUESTION_BANK = [
    {
        "id": 1,
        "question": "You receive an urgent email from 'HR Payroll' asking you to immediately verify your direct deposit password on an external website. What is the safest response?",
        "options": [
            "Quickly enter your credentials before the payroll cycle closes.",
            "Report the email through official security channels and contact HR via a known internal number.",
            "Reply to the email asking the sender to confirm their identity.",
            "Forward the link to your team members to check if they received it."
        ],
        "correct": 1,
        "explanation": "Attackers exploit urgency to bypass critical thinking. Always report suspicious messages and verify with HR out-of-band."
    },
    {
        "id": 2,
        "question": "When inspecting an email hyperlink, which technique reveals its authentic destination without putting your machine at risk?",
        "options": [
            "Click the link inside an incognito or private browsing window.",
            "Copy and paste the URL into a web search engine.",
            "Hover your mouse cursor over the link to preview the target address in your browser/email footer.",
            "Trust the hyperlink if the anchor text reads 'https://secure-login.com'."
        ],
        "correct": 2,
        "explanation": "Hovering previews the underlying destination URL. Displayed link text can easily be spoofed to look legitimate."
    },
    {
        "id": 3,
        "question": "Which of the following sender email domains is an example of 'typosquatting' designed to impersonate Microsoft?",
        "options": [
            "support@micros0ft-support.com",
            "notifications@microsoft.com",
            "security@azure.microsoft.com",
            "account-update@office.com"
        ],
        "correct": 0,
        "explanation": "'micros0ft-support.com' uses the number '0' instead of the letter 'o' and an unauthorized domain to deceive recipients."
    },
    {
        "id": 4,
        "question": "You receive repeated Multi-Factor Authentication (MFA) push notifications on your phone that you did not initiate, followed by a message claiming to be IT asking you to 'Accept once to stop the alerts'. What is happening?",
        "options": [
            "Routine server synchronization that is safe to approve.",
            "An MFA Fatigue (Push Bombing) attack attempting to trick you into authorizing an attacker's login.",
            "A hardware glitch on your mobile device.",
            "An automatic password reset scheduled by your domain controller."
        ],
        "correct": 1,
        "explanation": "MFA fatigue attacks spam push requests hoping the victim approves out of frustration. Always deny unexpected prompts and alert Security."
    },
    {
        "id": 5,
        "question": "An email arrives from your company CEO with the subject 'Confidential: Need urgent favor', asking you to purchase electronic gift cards for a client presentation. How should you proceed?",
        "options": [
            "Purchase the gift cards immediately because the CEO holds organizational authority.",
            "Call or message the executive through an approved internal directory channel before taking any action.",
            "Reply with your personal credit card receipt asking for reimbursement.",
            "Forward the email to the accounting department for immediate wire processing."
        ],
        "correct": 1,
        "explanation": "Business Email Compromise (BEC) and executive impersonation commonly request gift cards or urgent transfers that cannot be reversed."
    },
    {
        "id": 6,
        "question": "An unexpected email arrives containing an attachment named 'Q4_Client_Bonus_Report.pdf.exe'. What does this double extension indicate?",
        "options": [
            "It is a high-resolution PDF document formatted for Windows workstations.",
            "It is an executable binary masquerading as a harmless PDF document to conceal malware.",
            "It is an encrypted archive that requires double-clicking to decrypt.",
            "It is an Adobe Acrobat plugin update."
        ],
        "correct": 1,
        "explanation": "Attackers hide executable extensions (.exe, .scr, .vbs) behind document names (.pdf.exe) hoping victims assume it is a regular document."
    },
    {
        "id": 7,
        "question": "You find a flyer in the breakroom with a QR code labeled 'Scan to join the employee wellness raffle'. What threat does this potentially pose?",
        "options": [
            "QR Phishing (Quishing), which can redirect mobile devices to malicious credential-harvesting websites.",
            "No risk, as QR codes can only open safe text files.",
            "A firewall configuration warning.",
            "An encrypted digital signature check."
        ],
        "correct": 0,
        "explanation": "QR codes obscure target URLs from human inspection, making Quishing a growing vector for credential theft on mobile devices."
    },
    {
        "id": 8,
        "question": "An email from 'internal-comms@cybershield.corp' announces the upcoming company picnic, lists the park address, and contains no links or attachments. What type of communication is this?",
        "options": [
            "A high-threat phishing lure requiring immediate quarantine.",
            "A legitimate routine internal email that does not require reporting as malicious.",
            "A distributed denial of service beacon.",
            "A credential harvesting simulation."
        ],
        "correct": 1,
        "explanation": "Reporting harmless internal messages as phishing creates false alarms. Distinguishing safe business emails from threats is essential."
    },
    {
        "id": 9,
        "question": "You receive a browser popup or email asserting: 'Your computer has 7 viruses! Call 1-800-MICROSOFT immediately to clean your hard drive.' What is this tactic known as?",
        "options": [
            "Authorized remote telemetry.",
            "Tech support scareware designed to trick victims into granting remote access to their systems.",
            "An authentic Windows Defender operational notice.",
            "A corporate patch management notification."
        ],
        "correct": 1,
        "explanation": "Scareware fabricates dramatic system warnings to panic users into calling fraudulent help desks or installing remote control tools."
    },
    {
        "id": 10,
        "question": "If you inadvertently click a simulated phishing link in an internal training drill, what is the best constructive next step?",
        "options": [
            "Delete your email profile to avoid detection.",
            "Carefully review the training feedback, note the red flags present, and complete the refresher module.",
            "Ignore all future emails from the IT department.",
            "Share your password with coworkers to verify if their accounts work."
        ],
        "correct": 1,
        "explanation": "Simulations are safe learning opportunities. Understanding the indicators prepares employees to spot real attacks in the wild."
    }
]

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
                Employee(name="Alex Rivera", email="alex.rivera@cybershield.corp", department="Finance", role="Employee", awareness_score=85.0, simulations_received=4, links_clicked=1, emails_reported=2),
                Employee(name="Samantha Chen", email="samantha.chen@cybershield.corp", department="Human Resources", role="Employee", awareness_score=95.0, simulations_received=4, links_clicked=0, emails_reported=3),
                Employee(name="Marcus Taylor", email="marcus.taylor@cybershield.corp", department="IT Operations", role="Employee", awareness_score=70.0, simulations_received=4, links_clicked=2, emails_reported=1),
                Employee(name="Elena Rostova", email="elena.rostova@cybershield.corp", department="Security Administration", role="Admin", awareness_score=100.0, simulations_received=0, links_clicked=0, emails_reported=0)
            ]
            db.add_all(demo_employees)
            db.commit()

        existing_subjects = [s.subject for s in db.query(Simulation).all()]
        samples = [
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
                title="Simulated Routine All-Hands Meeting Invitation",
                sender="internal-comms@cybershield.corp",
                subject="Quarterly All-Hands Meeting - Next Thursday 2:00 PM",
                body_text="Hi Team,\n\nPlease find the invitation for our upcoming Quarterly All-Hands briefing. We will review our departmental milestones and celebrate key wins. No external action or credentials needed.",
                simulated_url="",
                difficulty="Easy",
                is_suspicious=False,
                red_flags="None (Legitimate internal announcement)"
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
                title="Simulated Routine IT Maintenance Notice",
                sender="it-support@cybershield.corp",
                subject="Scheduled Network Infrastructure Maintenance - Saturday 11:00 PM",
                body_text="Dear Employees,\n\nPlease be advised that our internal network switches will undergo routine maintenance this Saturday between 11:00 PM and 1:00 AM. No action is required on your part. Systems will resume normal operations on Sunday morning.",
                simulated_url="",
                difficulty="Easy",
                is_suspicious=False,
                red_flags="None (Legitimate internal IT maintenance notice)"
            )
        ]
        for item in samples:
            if item.subject not in existing_subjects:
                db.add(item)
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
    action: str

class QuizSubmit(BaseModel):
    employee_id: int
    answers: Dict[int, int]  # { question_id: selected_option_index }

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
        simulated_url=sim.simulated_url if sim.is_suspicious else "",
        difficulty=sim.difficulty,
        is_suspicious=sim.is_suspicious,
        red_flags=sim.red_flags if sim.is_suspicious else "None (Legitimate internal communication)"
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
            "is_suspicious": sim.is_suspicious if sim else True,
            "action": item.action,
            "timestamp": item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return result

@app.post("/api/admin/reset")
def reset_all_data(db: Session = Depends(get_db)):
    db.query(Interaction).delete()
    db.query(QuizSubmission).delete()
    db.query(Simulation).delete()
    db.query(Employee).delete()
    db.commit()
    seed_database()
    return {
        "status": "success",
        "message": "All employee scores, interaction logs, quiz records, and simulation templates have been reset to factory defaults!"
    }

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
            "title": "Simulation Alert: You clicked a simulated phishing link!",
            "message": "In a real scenario, clicking this unverified link could compromise credentials. Red flags: " + sim.red_flags
        }
    elif interaction_in.action == "reported":
        if sim.is_suspicious:
            emp.emails_reported += 1
            emp.awareness_score = min(100.0, round(emp.awareness_score + 10.0, 1))
            feedback = {
                "type": "success",
                "title": "Excellent Vigilance! You successfully reported a phishing simulation.",
                "message": "Reporting suspicious emails protects the entire company. Indicators spotted: " + sim.red_flags
            }
        else:
            emp.awareness_score = max(10.0, round(emp.awareness_score - 5.0, 1))
            feedback = {
                "type": "info",
                "title": "False Alarm: This was a Legitimate Business Email",
                "message": f"This message from '{sim.sender}' is a genuine internal communication. Inspect the sender domain and content carefully to avoid reporting safe messages."
            }
    elif interaction_in.action == "marked_safe":
        if not sim.is_suspicious:
            emp.awareness_score = min(100.0, round(emp.awareness_score + 5.0, 1))
            feedback = {
                "type": "success",
                "title": "Correct Recognition! Email Verified as Safe",
                "message": "Great job recognizing a legitimate corporate announcement. No malicious indicators found."
            }
        else:
            emp.awareness_score = max(10.0, round(emp.awareness_score - 15.0, 1))
            feedback = {
                "type": "warning",
                "title": "Missed Threat: This email was actually a Phishing Simulation!",
                "message": "You classified a phishing simulation as safe. Warning signs present: " + sim.red_flags
            }
    else:
        feedback = {
            "type": "info",
            "title": "Email Opened",
            "message": "Always inspect the sender address, tone, and links before taking action."
        }

    db.commit()
    db.refresh(emp)

    return {
        "status": "recorded",
        "employee_score": emp.awareness_score,
        "feedback": feedback
    }

# --- Dynamic & Randomized Quiz Endpoints ---
@app.get("/api/training/quiz-questions")
def get_random_quiz_questions(count: int = 4):
    sample_size = min(count, len(QUESTION_BANK))
    selected = random.sample(QUESTION_BANK, sample_size)
    # Return questions without the correct index to avoid client inspection
    public_questions = []
    for q in selected:
        public_questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"]
        })
    return public_questions

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

    score = 0
    total = len(submission.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    bank_map = {q["id"]: q for q in QUESTION_BANK}
    review_details = []

    for qid, user_ans in submission.answers.items():
        q_item = bank_map.get(int(qid))
        if q_item:
            is_correct = (user_ans == q_item["correct"])
            if is_correct:
                score += 1
            review_details.append({
                "id": q_item["id"],
                "question": q_item["question"],
                "user_answer": q_item["options"][user_ans] if 0 <= user_ans < len(q_item["options"]) else "None",
                "correct_answer": q_item["options"][q_item["correct"]],
                "is_correct": is_correct,
                "explanation": q_item["explanation"]
            })

    quiz_rec = QuizSubmission(employee_id=emp.id, score=score, total=total)
    db.add(quiz_rec)

    # Calculate bonus proportionally
    bonus = round((score / total) * 15.0, 1)
    emp.awareness_score = min(100.0, round(emp.awareness_score + bonus, 1))
    db.commit()

    return {
        "score": score,
        "total": total,
        "updated_awareness_score": emp.awareness_score,
        "message": f"Quiz Completed! You scored {score} out of {total}.",
        "reviews": review_details
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
