import os
import json
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESUMES_DIR = DATA_DIR / "generated_resumes"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RESUMES_DIR.mkdir(parents=True, exist_ok=True)

PROFILE_FILE = DATA_DIR / "profile.json"
QA_FILE = DATA_DIR / "qa_bank.json"
APPLICATIONS_FILE = DATA_DIR / "applications.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_PROFILE = {
    "personal": {
        "full_name": "Alex Mercer",
        "email": "alex.mercer.dev@example.com",
        "phone": "+1 (555) 234-5678",
        "location": "San Francisco, CA (Open to Remote)",
        "linkedin": "https://linkedin.com/in/alex-mercer",
        "github": "https://github.com/alex-mercer",
        "portfolio": "https://alexmercer.dev"
    },
    "headline": "Senior Full-Stack & Python Software Engineer | Cloud & AI Systems",
    "summary": "Results-driven Software Engineer with 5+ years of experience building scalable distributed systems, high-performance web applications, and AI-enabled automation workflows. Proven track record of improving system latency by 40% and deploying enterprise-grade microservices.",
    "skills": {
        "Languages": ["Python", "JavaScript", "TypeScript", "SQL", "Go", "HTML5", "CSS3"],
        "Frameworks & Libraries": ["FastAPI", "React", "Node.js", "Django", "Flask", "Tailwind CSS"],
        "Cloud & DevOps": ["AWS (EC2, S3, Lambda)", "Docker", "Kubernetes", "CI/CD Pipelines", "Terraform", "PostgreSQL", "Redis"],
        "Tools & Methodologies": ["Git", "REST APIs", "GraphQL", "Agile/Scrum", "Microservices Architecture", "System Design", "TDD"]
    },
    "experiences": [
        {
            "id": "exp-1",
            "title": "Senior Software Engineer",
            "company": "CloudScale Technologies",
            "location": "San Francisco, CA (Remote)",
            "start_date": "Jan 2022",
            "end_date": "Present",
            "bullets": [
                "Architected and deployed high-throughput microservices using Python, FastAPI, and PostgreSQL, supporting 2M+ daily active requests with 99.98% uptime.",
                "Engineered automated data ingestion and real-time processing pipelines reducing end-to-end data latency by 45%.",
                "Spearheaded containerization strategy using Docker and Kubernetes on AWS (EKS, S3), reducing infrastructure costs by 28%.",
                "Mentored a cross-functional team of 6 engineers on clean code, automated testing, and CI/CD best practices."
            ]
        },
        {
            "id": "exp-2",
            "title": "Software Engineer",
            "company": "Nexus Interactive",
            "location": "Austin, TX",
            "start_date": "Jun 2019",
            "end_date": "Dec 2021",
            "bullets": [
                "Built and maintained responsive full-stack web applications utilizing React, Node.js, Python, and Redis for distributed caching.",
                "Designed and implemented RESTful APIs and webhook integrations for enterprise payment and analytics systems.",
                "Optimized relational database queries and indexing strategies in PostgreSQL, accelerating query response times by 35%.",
                "Collaborated with product and UX teams to translate business requirements into resilient technical architectures."
            ]
        }
    ],
    "education": [
        {
            "id": "edu-1",
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University of California, Berkeley",
            "graduation_year": "2019",
            "gpa": "3.8/4.0",
            "honors": "Dean's Honor List"
        }
    ],
    "certifications": [
        "AWS Certified Solutions Architect – Associate",
        "Certified Kubernetes Administrator (CKA)"
    ],
    "projects": [
        {
            "id": "proj-1",
            "name": "AutoApply & ATS Matcher",
            "tech": "Python, FastAPI, Playwright, ReportLab",
            "description": "Built an intelligent job application bot with dynamic ATS keyword optimization and automated supervised form submission."
        },
        {
            "id": "proj-2",
            "name": "Distributed Task Orchestrator",
            "tech": "Python, Redis, Docker, Celery",
            "description": "Engineered an asynchronous task queue processing 50,000+ jobs/hour with automatic retries and dead-letter queues."
        }
    ]
}

DEFAULT_QA_BANK = {
    "work_authorization": "Yes, authorized to work in target location",
    "visa_sponsorship_needed": "No",
    "notice_period": "2 weeks",
    "years_of_experience": "5+",
    "current_salary": "Negotiable",
    "expected_salary": "$140,000 - $165,000",
    "willing_to_relocate": "Open for discussion / Remote preferred",
    "skills_years": {
        "Python": "5",
        "FastAPI": "4",
        "React": "4",
        "JavaScript": "5",
        "AWS": "4",
        "Docker": "4",
        "PostgreSQL": "5",
        "SQL": "5",
        "Git": "5"
    },
    "custom_answers": {
        "Are you legally authorized to work in the country where this job is located?": "Yes",
        "Will you now or in the future require sponsorship for employment visa status?": "No",
        "Have you previously worked for our company?": "No",
        "How did you hear about this opportunity?": "LinkedIn Job Board",
        "What is your highest level of education completed?": "Bachelor's Degree"
    }
}

DEFAULT_SETTINGS = {
    "supervised_mode": True,
    "browser_type": "chromium",
    "headless": False,
    "stealth_delays": True,
    "typing_delay_ms": 75,
    "action_delay_seconds": 1.5,
    "daily_application_limit": 25,
    "ats_threshold_score": 75,
    "ai_provider": "builtin", # "builtin" | "openai" | "gemini" | "ollama"
    "ai_api_key": "",
    "ai_model": "gpt-4o-mini",
    "ollama_url": "http://localhost:11434",
    "connected_platforms": {
        "linkedin": {"enabled": True, "status": "Ready"},
        "indeed": {"enabled": True, "status": "Ready"},
        "greenhouse": {"enabled": True, "status": "Ready"},
        "lever": {"enabled": True, "status": "Ready"},
        "wellfound": {"enabled": True, "status": "Ready"},
        "workday": {"enabled": True, "status": "Ready"}
    }
}

def load_json(filepath: Path, default_data: Any) -> Any:
    if not filepath.exists():
        save_json(filepath, default_data)
        return default_data
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_data

def save_json(filepath: Path, data: Any):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_profile() -> Dict[str, Any]:
    return load_json(PROFILE_FILE, DEFAULT_PROFILE)

def save_profile(data: Dict[str, Any]):
    save_json(PROFILE_FILE, data)

def get_qa_bank() -> Dict[str, Any]:
    return load_json(QA_FILE, DEFAULT_QA_BANK)

def save_qa_bank(data: Dict[str, Any]):
    save_json(QA_FILE, data)

def get_applications() -> List[Dict[str, Any]]:
    return load_json(APPLICATIONS_FILE, [])

def save_applications(apps: List[Dict[str, Any]]):
    save_json(APPLICATIONS_FILE, apps)

def add_application(app: Dict[str, Any]):
    apps = get_applications()
    # Check if exists by id
    apps = [a for a in apps if a.get("id") != app.get("id")]
    apps.insert(0, app)
    save_applications(apps)

def get_settings() -> Dict[str, Any]:
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)

def save_settings(data: Dict[str, Any]):
    save_json(SETTINGS_FILE, data)
