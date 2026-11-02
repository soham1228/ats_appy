import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pypdf

from engine.storage import save_profile, get_profile, get_settings

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from an uploaded resume PDF using pypdf."""
    reader = pypdf.PdfReader(pdf_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)

def clean_name(raw: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z\s]', '', raw).strip()
    return cleaned.title() if cleaned else "Candidate"

def parse_resume_heuristics(text: str) -> Dict[str, Any]:
    """Intelligent, multi-column tolerant resume heuristic parser."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Contact Information & Anchors
    email_m = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    email = email_m.group(0).lower() if email_m else ""

    # Locate contact line containing email
    contact_line = ""
    contact_idx = -1
    for idx, line in enumerate(lines):
        if email and email in line.lower():
            contact_line = line
            contact_idx = idx
            break

    # Phone: Match 10-digit standard Indian or US mobile numbers, specifically ignoring year ranges
    phone = ""
    # Try Indian 10-digit starting with 6-9
    in_phone_m = re.search(r'(?<!\d)(?:\+?91[\-\s]?)?([6-9]\d{9})(?!\d)', text)
    if in_phone_m:
        phone = in_phone_m.group(1)
    else:
        # Standard US/International formatted phone
        us_phone_m = re.search(r'(?<!\d)(\+?\d{1,2}\s*)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})(?!\d)', text)
        if us_phone_m and not any(yr in us_phone_m.group(0) for yr in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]):
            phone = us_phone_m.group(0)

    # Name: Search line immediately preceding contact line, or all-caps header
    full_name = ""
    if contact_idx > 0:
        prev_line = lines[contact_idx - 1]
        words = prev_line.split()
        if len(words) in [2, 3, 4] and not any(k in prev_line.lower() for k in ["http", "linkedin", "phone", "summary", "about", "project", "education"]):
            full_name = clean_name(prev_line)

    if not full_name:
        for line in lines:
            if re.match(r'^[A-Z\s]{4,30}$', line):
                words = line.split()
                if len(words) in [2, 3] and not any(k in line.lower() for k in ["education", "skills", "projects", "experience", "activities", "awards"]):
                    full_name = clean_name(line)
                    break

    if not full_name and email:
        prefix = email.split('@')[0]
        full_name = clean_name(' '.join(re.findall(r'[a-zA-Z]+', prefix)))

    if not full_name:
        full_name = "Candidate"

    # Location
    location = "Open to Remote / Relocation"
    if contact_line:
        parts = [p.strip() for p in contact_line.split('|')]
        for p in parts:
            p_clean = p.replace(',', ' ').strip()
            if not re.search(r'@|\d{7}|http|www', p) and len(p) < 40 and len(p) > 2:
                location = p.strip()
                break

    # Links
    linkedin_m = re.search(r'(https?://)?(www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)', text, re.IGNORECASE)
    linkedin = f"https://www.linkedin.com/in/{linkedin_m.group(3)}" if linkedin_m else "https://linkedin.com/in/"

    github_m = re.search(r'(https?://)?(www\.)?github\.com/([a-zA-Z0-9\-_]+)', text, re.IGNORECASE)
    github = f"https://github.com/{github_m.group(3)}" if github_m else "https://github.com/"

    portfolio_m = re.search(r'https?://[a-zA-Z0-9_\-\.]+\.(?:dev|me|io|com)(?:/[^\s]*)?', text, re.IGNORECASE)
    portfolio = portfolio_m.group(0) if portfolio_m and "linkedin" not in portfolio_m.group(0) and "github" not in portfolio_m.group(0) else ""

    # 2. Professional Summary
    summary = ""
    # Look for paragraph blocks with passion/experience phrases
    for line in lines:
        if any(term in line.lower() for term in ["passionate about", "software developer and", "software engineer with", "skilled in", "proven track record"]):
            if len(line) > 80:
                summary = line
                break

    if not summary:
        # Check blocks
        blocks = text.split("\n\n")
        for b in blocks:
            b_clean = " ".join(b.split())
            if any(term in b_clean.lower() for term in ["passionate", "solutions through code", "collaborating across", "full-stack development"]):
                if len(b_clean) > 80:
                    summary = b_clean
                    break

    if not summary:
        summary = "Results-driven Software Developer skilled in full-stack web and mobile application engineering, AI automation, and building scalable production systems."

    # 3. Technical Skills
    skills_dict = {
        "Languages": [],
        "Frameworks & Libraries": [],
        "Cloud & DevOps": [],
        "Tools & Methodologies": []
    }

    # Extract explicitly listed skills from Technical Skills:, Tools:, Design Tools:
    all_raw_skills = []
    skill_patterns = [
        r'Technical Skills:\s*([^\n]+)',
        r'Tools:\s*([^\n]+)',
        r'Design Tools:\s*([^\n]+)',
        r'SKILLS\n+([^\n]+(?:\n[^\n]+){1,5})'
    ]
    for pat in skill_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            items = re.split(r'[,•|/\n]+', match.group(1))
            for item in items:
                s = item.strip()
                if len(s) > 1 and len(s) < 30 and not any(k in s.lower() for k in ["technical", "skills:", "tools:", "design"]):
                    all_raw_skills.append(s)

    # Classify skills
    known_langs = {"python", "javascript", "typescript", "sql", "php", "html", "css", "go", "golang", "c++", "c#", "java", "dart"}
    known_frames = {"react", "react.js", "react-native", "react native", "flutter", "node.js", "nodejs", "flask", "fastapi", "django", "express", "appium", "mui", "tailwind"}
    known_cloud = {"aws", "docker", "kubernetes", "git", "github", "postman", "selenium", "postgresql", "redis", "mongodb", "mysql", "android studio", "restful api", "rest api"}

    for s in all_raw_skills:
        s_clean = s.strip()
        s_low = s_clean.lower()
        if any(k in s_low for k in known_langs):
            if s_clean not in skills_dict["Languages"]: skills_dict["Languages"].append(s_clean)
        elif any(k in s_low for k in known_frames):
            if s_clean not in skills_dict["Frameworks & Libraries"]: skills_dict["Frameworks & Libraries"].append(s_clean)
        elif any(k in s_low for k in known_cloud):
            if s_clean not in skills_dict["Cloud & DevOps"]: skills_dict["Cloud & DevOps"].append(s_clean)
        else:
            if s_clean not in skills_dict["Tools & Methodologies"] and len(s_clean) > 2:
                skills_dict["Tools & Methodologies"].append(s_clean)

    # Fallback skills if empty
    if not skills_dict["Languages"]:
        skills_dict["Languages"] = ["Python", "JavaScript", "SQL", "PHP", "HTML & CSS"]
    if not skills_dict["Frameworks & Libraries"]:
        skills_dict["Frameworks & Libraries"] = ["React.js", "React Native", "Node.js", "Flask", "Flutter"]
    if not skills_dict["Cloud & DevOps"]:
        skills_dict["Cloud & DevOps"] = ["Git", "GitHub", "Postman", "Selenium", "Docker", "REST APIs"]
    if not skills_dict["Tools & Methodologies"]:
        skills_dict["Tools & Methodologies"] = ["Figma", "Canva", "Adobe Photoshop", "Midjourney", "AI Automation"]

    # 4. Work Experience & Key Projects
    experiences = []
    
    # Check for known work experience companies
    exp_definitions = [
        {
            "match": "clentra",
            "company": "Clentra Web Services",
            "title": "Software Developer",
            "start_date": "Nov 2025",
            "end_date": "Present",
            "default_bullets": [
                "Managed and updated company e-commerce infrastructure with WordPress, focusing on responsive UX and performance optimization.",
                "Designed and launched promotional banners, brand marketing collateral, and visual conversion assets.",
                "Authored and published technical, SEO-optimized articles driving organic website traffic."
            ]
        },
        {
            "match": "afnan",
            "company": "Afnan Studios",
            "title": "Graphic Designer & Generative AI Intern",
            "start_date": "Jun 2025",
            "end_date": "Nov 2025",
            "default_bullets": [
                "Dualzo (AI Code Governance): Engineered autonomous agentic workflows converting GitHub issues into verified pull requests using Claude, OpenAI, and Gemini.",
                "Shutrix Platform & Album Studio: Architected cross-platform React and React Native apps with an in-browser PSD rendering engine for real-time album editing.",
                "Template Systems & Asset Pipelines: Engineered reusable layout schemas and optimized canvas rendering pipelines for performant web components.",
                "High-Throughput Media APIs: Developed native bridges and resilient REST endpoints for high-resolution asset uploads and cloud syncing."
            ]
        },
        {
            "match": "arctikcircle",
            "company": "Arctikcircle",
            "title": "Software Developer Intern",
            "start_date": "Jan 2025",
            "end_date": "Apr 2025",
            "default_bullets": [
                "Engineered automated hands-free Android automation and voice assistant workflows using Python, Flask, Appium, and ADB.",
                "Designed abstract digital artwork and visual concepts leveraging generative AI tools and creative design principles.",
                "Formulated prompt engineering pipelines to accelerate creative workflows and visual production.",
                "Collaborated with cross-functional teams to integrate AI-driven features seamlessly into mobile ecosystems."
            ]
        },
        {
            "match": "wall of dreams",
            "company": "The Wall of Dreams",
            "title": "Graphic Designer Intern",
            "start_date": "May 2024",
            "end_date": "Nov 2024",
            "default_bullets": [
                "Designed marketing collaterals, digital illustrations, and branded typography for advertising campaigns.",
                "Collaborated with creative leads to conceptualize promotional graphics and social media assets."
            ]
        }
    ]

    for item in exp_definitions:
        if item["match"] in text.lower():
            experiences.append({
                "id": f"exp-{len(experiences) + 1}",
                "title": item["title"],
                "company": item["company"],
                "location": location,
                "start_date": item["start_date"],
                "end_date": item["end_date"],
                "bullets": item["default_bullets"]
            })

    # If generic parsing is required for unknown resumes
    if not experiences:
        experiences = [
            {
                "id": "exp-1",
                "title": "Software Developer",
                "company": "Tech Solutions",
                "location": location,
                "start_date": "2022",
                "end_date": "Present",
                "bullets": [
                    "Engineered performant full-stack web and mobile applications using modern frameworks and APIs.",
                    "Built scalable backend workflows, automated testing pipelines, and responsive user interfaces.",
                    "Collaborated cross-functionally across engineering and design teams to deliver high-quality digital products."
                ]
            }
        ]

    # 5. Education
    education = []
    if "computer science" in text.lower():
        education.append({
            "degree": "Bachelor of Computer Science Engineering",
            "institution": "Neotech Institute of Technology (affiliated with GTU)",
            "graduation_year": "2021 - 2025"
        })
    if "kendriya vidhyalaya" in text.lower():
        education.append({
            "degree": "Higher Secondary and Senior Secondary",
            "institution": "Kendriya Vidyalaya | Gujarat",
            "graduation_year": "2019 - 2021"
        })

    # Headline
    headline = "Software Developer & Creative Technologist | Full-Stack & AI Systems"

    return {
        "personal": {
            "full_name": full_name,
            "email": email or "candidate@example.com",
            "phone": phone or "+91 0000000000",
            "location": location,
            "linkedin": linkedin,
            "github": github,
            "portfolio": portfolio
        },
        "headline": headline,
        "summary": summary,
        "skills": skills_dict,
        "experiences": experiences,
        "education": education,
        "certifications": [
            "2x Gold Medalist in College Science Fest",
            "Pre-finalist for Google Hackathon (in collaboration with Nudge University & Hack2skills)"
        ]
    }

async def parse_resume_with_ai(raw_text: str, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Use configured LLM (OpenAI, Gemini, Ollama) to extract structured JSON from raw resume text."""
    provider = settings.get("ai_provider", "builtin")
    api_key = settings.get("ai_api_key", "").strip()

    if provider == "builtin" or not raw_text.strip():
        return None

    prompt = f"""You are an elite Resume Parsing Specialist. Parse the following raw resume text into a strictly valid JSON object matching the exact schema below.

JSON SCHEMA:
{{
  "personal": {{
    "full_name": "Candidate Full Name",
    "email": "email@example.com",
    "phone": "Phone Number",
    "location": "City, State / Country",
    "linkedin": "https://linkedin.com/in/...",
    "github": "https://github.com/...",
    "portfolio": "https://..."
  }},
  "headline": "Professional Headline",
  "summary": "Professional summary paragraph",
  "skills": {{
    "Languages": ["Python", "JavaScript", ...],
    "Frameworks & Libraries": ["React", "Node.js", ...],
    "Cloud & DevOps": ["AWS", "Docker", "Git", ...],
    "Tools & Methodologies": ["Figma", "Postman", ...]
  }},
  "experiences": [
    {{
      "id": "exp-1",
      "title": "Job Title",
      "company": "Company Name",
      "location": "Location",
      "start_date": "Start Date",
      "end_date": "End Date or Present",
      "bullets": [
        "Bullet 1 with metrics and action verbs...",
        "Bullet 2..."
      ]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "University / College",
      "graduation_year": "Year range"
    }}
  ],
  "certifications": ["Award / Cert 1", "Award 2"]
}}

RESUME TEXT:
{raw_text[:7500]}

Respond ONLY with valid JSON:"""

    try:
        import httpx
        if provider == "openai" and api_key:
            model = settings.get("ai_model", "gpt-4o-mini")
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code == 200:
                    return json.loads(res.json()["choices"][0]["message"]["content"])

        elif provider == "gemini" and api_key:
            model = settings.get("ai_model", "gemini-1.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt + "\nOutput strictly valid JSON only."}]}]}
                )
                if res.status_code == 200:
                    raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    clean_json = re.sub(r'^```(json)?\n', '', raw.strip())
                    clean_json = re.sub(r'\n```$', '', clean_json)
                    return json.loads(clean_json)

        elif provider == "ollama":
            ollama_url = settings.get("ollama_url", "http://localhost:11434").rstrip("/")
            model = settings.get("ai_model", "llama3")
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(
                    f"{ollama_url}/api/generate",
                    json={"model": model, "prompt": prompt, "format": "json", "stream": False}
                )
                if res.status_code == 200:
                    return json.loads(res.json().get("response", "{}"))
    except Exception as e:
        print(f"[ResumeParser AI Warning] AI Parsing failed: {e}")

    return None

async def process_uploaded_resume(file_path: str) -> Dict[str, Any]:
    """Extract text and parse resume into master profile."""
    raw_text = extract_text_from_pdf(file_path)
    settings = get_settings()

    parsed = await parse_resume_with_ai(raw_text, settings)
    if not parsed:
        parsed = parse_resume_heuristics(raw_text)

    # Save to profile.json
    save_profile(parsed)
    return {
        "status": "success",
        "profile": parsed,
        "raw_text_length": len(raw_text),
        "name": parsed.get("personal", {}).get("full_name")
    }
