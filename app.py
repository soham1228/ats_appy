import os
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.storage import (
    get_profile, save_profile,
    get_qa_bank, save_qa_bank,
    get_applications, save_applications, add_application,
    get_settings, save_settings,
    RESUMES_DIR, DATA_DIR
)
from engine.ats_optimizer import (
    extract_keywords_from_jd,
    analyze_ats_match,
    tailor_resume,
    tailor_resume_pipeline
)
from engine.resume_parser import process_uploaded_resume, parse_resume_heuristics, parse_resume_with_ai
from engine.pdf_generator import generate_ats_pdf
from engine.bot_runner import bot_instance

app = FastAPI(title="CareerCopilot - ATS Optimizer & Supervised Job Application Suite")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory log buffer & WebSocket manager
connected_clients: List[WebSocket] = []
recent_logs: List[Dict[str, str]] = []

def broadcast_log(message: str, level: str = "info"):
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    recent_logs.append(entry)
    if len(recent_logs) > 300:
        recent_logs.pop(0)

    # Broadcast to all live websockets asynchronously
    for ws in list(connected_clients):
        try:
            asyncio.create_task(ws.send_json(entry))
        except Exception:
            pass

# Connect bot logs to our live broadcaster
bot_instance.log_callback = broadcast_log

# Request Models
class JDAnalysisRequest(BaseModel):
    jd_text: str
    role_title: Optional[str] = ""
    company: Optional[str] = ""

class TailorRequest(BaseModel):
    jd_text: str
    role_title: Optional[str] = ""
    company: Optional[str] = ""
    job_url: Optional[str] = ""

class ScrapeRequest(BaseModel):
    url: str

class BotApplyRequest(BaseModel):
    job_url: str
    tailored_pdf_path: str
    job_id: Optional[str] = None

class LinkedInImportRequest(BaseModel):
    profile_url: str

class PlatformLoginRequest(BaseModel):
    platform: str

# --- API Endpoints ---

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    
    upload_path = DATA_DIR / "uploaded_resume.pdf"
    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)
    
    broadcast_log(f"Received resume PDF upload: '{file.filename}'. Extracting candidate profile...", "info")
    res = await process_uploaded_resume(str(upload_path))
    broadcast_log(f"Profile updated successfully for '{res.get('name', 'Candidate')}'.", "success")
    return res

class ResumeTextRequest(BaseModel):
    text: str

@app.post("/api/parse-resume-text")
async def parse_resume_text_endpoint(req: ResumeTextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty.")
    
    broadcast_log("Parsing provided resume text into structured profile...", "info")
    settings = get_settings()
    parsed = await parse_resume_with_ai(req.text, settings)
    if not parsed:
        parsed = parse_resume_heuristics(req.text)
    
    save_profile(parsed)
    name = parsed.get("personal", {}).get("full_name", "Candidate")
    broadcast_log(f"Successfully parsed resume text for '{name}'. Master Profile updated!", "success")
    return {
        "status": "success",
        "profile": parsed,
        "name": name
    }

@app.post("/api/import-linkedin-profile")
async def import_linkedin_profile(req: LinkedInImportRequest):
    if not req.profile_url:
        raise HTTPException(status_code=400, detail="LinkedIn profile URL is required.")
    
    broadcast_log(f"Opening browser to scrape LinkedIn profile: {req.profile_url}", "info")
    res = await bot_instance.scrape_linkedin_profile(req.profile_url)
    if res.get("status") == "success" and res.get("profile"):
        save_profile(res["profile"])
        broadcast_log(f"Successfully imported LinkedIn profile for: {res['profile']['personal'].get('full_name')}", "success")
    else:
        broadcast_log(f"LinkedIn import notice: {res.get('message', 'Please log in')}", "warn")
    return res

@app.post("/api/platform/login")
async def platform_login(req: PlatformLoginRequest):
    broadcast_log(f"Opening browser for {req.platform.title()} authentication...", "info")
    return await bot_instance.launch_platform_login(req.platform)

@app.get("/api/profile")
def get_user_profile():
    return get_profile()

@app.post("/api/profile")
def update_user_profile(profile: Dict[str, Any]):
    save_profile(profile)
    broadcast_log("Master profile updated successfully.", "success")
    return {"status": "success", "profile": profile}

@app.get("/api/qa-bank")
def get_user_qa_bank():
    return get_qa_bank()

@app.post("/api/qa-bank")
def update_user_qa_bank(qa: Dict[str, Any]):
    save_qa_bank(qa)
    broadcast_log("Screening QA Bank updated.", "success")
    return {"status": "success", "qa_bank": qa}

@app.get("/api/applications")
def list_applications():
    return get_applications()

@app.get("/api/settings")
def get_app_settings():
    return get_settings()

@app.post("/api/settings")
def update_app_settings(settings: Dict[str, Any]):
    save_settings(settings)
    return {"status": "success", "settings": settings}

@app.post("/api/analyze-jd")
def analyze_job_description(req: JDAnalysisRequest):
    if not req.jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")
    
    profile = get_profile()
    jd_analysis = extract_keywords_from_jd(req.jd_text)
    ats_match = analyze_ats_match(profile, jd_analysis)
    
    broadcast_log(f"Analyzed JD: {len(jd_analysis['technical_skills'])} tech skills identified. Initial ATS Match: {ats_match['score']}%", "info")
    return {
        "jd_analysis": jd_analysis,
        "ats_match": ats_match
    }

@app.post("/api/tailor-resume")
async def tailor_and_generate_resume(req: TailorRequest):
    if not req.jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")
    
    profile = get_profile()
    settings = get_settings()
    engine_name = settings.get("ai_provider", "builtin").title()
    broadcast_log(f"Tailoring resume against JD requirements (Engine: {engine_name})...", "info")
    result = await tailor_resume_pipeline(profile, req.jd_text, req.role_title or "", settings)
    
    # Generate unique filename for PDF
    app_id = str(uuid.uuid4())[:8]
    clean_role = (req.role_title or "Software_Engineer").replace(" ", "_")
    clean_role = "".join(c for c in clean_role if c.isalnum() or c in "_-")
    pdf_filename = f"Resume_{clean_role}_{app_id}.pdf"
    pdf_path = str(RESUMES_DIR / pdf_filename)
    
    # Generate the strict ATS PDF
    generate_ats_pdf(result["tailored_profile"], pdf_path)
    broadcast_log(f"Generated ATS-compliant PDF: {pdf_filename} (Optimized ATS Score: {result['optimized_match']['score']}%)", "success")

    # Record in applications history
    app_record = {
        "id": app_id,
        "title": req.role_title or result["target_title"],
        "company": req.company or "Target Company",
        "job_url": req.job_url or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "initial_score": result["initial_match"]["score"],
        "optimized_score": result["optimized_match"]["score"],
        "pdf_filename": pdf_filename,
        "pdf_path": pdf_path,
        "status": "Ready for Review",
        "cover_letter": result["cover_letter"]
    }
    add_application(app_record)

    return {
        "app_id": app_id,
        "tailored_profile": result["tailored_profile"],
        "initial_match": result["initial_match"],
        "optimized_match": result["optimized_match"],
        "cover_letter": result["cover_letter"],
        "pdf_filename": pdf_filename,
        "pdf_path": pdf_path,
        "pdf_download_url": f"/api/download-resume/{pdf_filename}"
    }

@app.get("/api/download-resume/{filename}")
def download_resume(filename: str):
    file_path = RESUMES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Resume PDF not found.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )

@app.post("/api/scrape-job-url")
async def scrape_job_url(req: ScrapeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required.")
    
    broadcast_log(f"Opening browser to extract JD from URL: {req.url}", "info")
    data = await bot_instance.extract_job_from_url(req.url)
    broadcast_log(f"Extracted job: '{data.get('title')}' at '{data.get('company')}'", "success")
    return data

@app.post("/api/bot/launch-supervised")
async def launch_supervised_bot(req: BotApplyRequest, background_tasks: BackgroundTasks):
    profile = get_profile()
    qa_bank = get_qa_bank()
    
    if not Path(req.tailored_pdf_path).exists():
        raise HTTPException(status_code=400, detail="Tailored PDF file does not exist. Please tailor first.")

    broadcast_log(f"[SUPERVISED BOT] Starting job application for URL: {req.job_url}", "info")
    
    # Run in background so request returns immediately and user watches live browser + websocket
    async def run_bot_task():
        res = await bot_instance.execute_supervised_apply(
            job_url=req.job_url,
            profile=profile,
            qa_bank=qa_bank,
            tailored_resume_path=req.tailored_pdf_path
        )
        if req.job_id:
            apps = get_applications()
            for a in apps:
                if a.get("id") == req.job_id:
                    a["status"] = "Paused for Review" if res.get("status") == "ready_for_review" else "Applied"
            save_applications(apps)

    background_tasks.add_task(run_bot_task)
    return {"status": "started", "message": "Supervised application bot launched. Watching browser..."}

@app.post("/api/bot/confirm-submit")
async def confirm_submit():
    res = await bot_instance.confirm_and_submit()
    return res

@app.post("/api/bot/close")
async def close_bot():
    await bot_instance.close()
    return {"status": "closed"}

# --- WebSocket for Live Logs ---
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Send backlog of recent logs
    for log in recent_logs[-20:]:
        await websocket.send_json(log)
        
    try:
        while True:
            # Keepalive ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# Mount static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
