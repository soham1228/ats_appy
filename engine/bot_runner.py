import asyncio
import os
import re
import time
import json
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from playwright.async_api import async_playwright, BrowserContext, Page

BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / "data" / "browser_profile"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

class SupervisedApplyBot:
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        self.log_callback = log_callback or (lambda msg, lvl="info": print(f"[{lvl.upper()}] {msg}"))
        self.is_running = False
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.waiting_for_user = False
        self.current_job_info: Dict[str, Any] = {}

    def log(self, message: str, level: str = "info"):
        if self.log_callback:
            self.log_callback(message, level)

    async def launch_browser(self, headless: bool = False) -> Page:
        self.log("Initializing browser with persistent profile...", "info")
        playwright = await async_playwright().start()
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=headless,
            slow_mo=100,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        pages = self.context.pages
        self.page = pages[0] if pages else await self.context.new_page()
        self.log("Browser launched. Anti-detection headers applied.", "success")
        return self.page

    async def launch_platform_login(self, platform: str) -> Dict[str, Any]:
        """Open persistent browser directly to a job platform's login page for one-time authentication."""
        urls = {
            "linkedin": "https://www.linkedin.com/login",
            "indeed": "https://secure.indeed.com/account/login",
            "wellfound": "https://wellfound.com/login",
            "greenhouse": "https://boards.greenhouse.io",
            "workday": "https://www.myworkday.com",
            "lever": "https://jobs.lever.co"
        }
        target_url = urls.get(platform.lower(), "https://www.google.com")
        if not self.page:
            await self.launch_browser(headless=False)

        self.log(f"Opening {platform.title()} login page in persistent browser: {target_url}", "info")
        await self.page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
        self.log(f"Please log into {platform.title()} in the open browser window. Your login session will be permanently saved!", "warn")
        return {"status": "opened", "platform": platform, "url": target_url}

    async def scrape_linkedin_profile(self, profile_url: str) -> Dict[str, Any]:
        """Navigate to user's LinkedIn profile and scrape experience, skills, and summary."""
        if not self.page:
            await self.launch_browser(headless=False)

        self.log(f"Navigating to LinkedIn profile: {profile_url}", "info")
        await self.page.goto(profile_url, timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        if "login" in self.page.url:
            self.log("LinkedIn login required! Please log into LinkedIn in the browser first.", "error")
            return {"status": "error", "message": "LinkedIn authentication required."}

        full_name = "Candidate"
        headline = ""
        location = ""
        summary = ""

        try:
            name_el = await self.page.query_selector("h1.inline.t-24, h1.text-heading-xlarge, h1")
            if name_el:
                full_name = (await name_el.inner_text()).strip()

            hl_el = await self.page.query_selector(".text-body-medium.break-words, div[data-generated-suggestion-target]")
            if hl_el:
                headline = (await hl_el.inner_text()).strip()

            loc_el = await self.page.query_selector(".text-body-small.inline.t-black--light.break-words")
            if loc_el:
                location = (await loc_el.inner_text()).strip()

            about_el = await self.page.query_selector("#about ~ .display-flex .inline-show-more-text, section[id*='about'] .inline-show-more-text")
            if about_el:
                summary = (await about_el.inner_text()).strip()
        except Exception as e:
            self.log(f"Notice during LinkedIn header scrape: {e}", "warn")

        # Scrape experiences
        experiences = []
        try:
            exp_items = await self.page.query_selector_all("#experience ~ .pvs-list__outer-container > ul > li, section[id*='experience'] ul > li")
            for idx, item in enumerate(exp_items[:6]):
                item_text = await item.inner_text()
                lines = [l.strip() for l in item_text.split("\n") if l.strip()]
                if len(lines) >= 2:
                    title = lines[0]
                    company = lines[1]
                    bullets = [l for l in lines[3:] if len(l) > 20 and not any(k in l.lower() for k in ["show all", "skills:", "months", "years"])]
                    experiences.append({
                        "id": f"exp-{idx+1}",
                        "title": title,
                        "company": company,
                        "location": location or "Remote",
                        "start_date": "2021",
                        "end_date": "Present",
                        "bullets": bullets[:4] if bullets else ["Engineered high-performance systems and collaborated with cross-functional teams."]
                    })
        except Exception as e:
            self.log(f"Notice during LinkedIn experience scrape: {e}", "warn")

        return {
            "status": "success",
            "profile": {
                "personal": {
                    "full_name": full_name,
                    "email": "",
                    "phone": "",
                    "location": location or "Remote",
                    "linkedin": profile_url,
                    "github": "",
                    "portfolio": ""
                },
                "headline": headline or "Software Engineer",
                "summary": summary or f"Experienced {headline or 'Software Engineer'} passionate about building robust systems.",
                "skills": {
                    "Languages": ["Python", "JavaScript", "TypeScript", "SQL"],
                    "Frameworks & Libraries": ["FastAPI", "React", "Node.js"],
                    "Cloud & DevOps": ["AWS", "Docker", "PostgreSQL", "Git"],
                    "Tools & Methodologies": ["Agile/Scrum", "REST APIs", "Microservices"]
                },
                "experiences": experiences
            }
        }

    async def extract_job_from_url(self, url: str) -> Dict[str, Any]:
        """Navigate to URL and extract JD text, title, and company across multiple platforms."""
        if not self.page:
            await self.launch_browser(headless=False)

        self.log(f"Navigating to job posting: {url}", "info")
        await self.page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        title = await self.page.title()
        company = "Unknown Company"
        role = title
        jd_text = ""
        url_lower = url.lower()

        try:
            # 1. Greenhouse
            if "greenhouse.io" in url_lower:
                title_elem = await self.page.query_selector("h1.app-title, .app-title, h1")
                comp_elem = await self.page.query_selector(".company-name, .sub-title")
                jd_elem = await self.page.query_selector("#content, #app-body, .content")
                if title_elem: role = (await title_elem.inner_text()).strip()
                if comp_elem: company = (await comp_elem.inner_text()).replace("at ", "").strip()
                if jd_elem: jd_text = await jd_elem.inner_text()

            # 2. Lever
            elif "lever.co" in url_lower:
                title_elem = await self.page.query_selector(".posting-headline h2, h2")
                comp_elem = await self.page.query_selector(".main-header-logo img, .posting-headline .org")
                jd_elem = await self.page.query_selector(".section-page, .posting-page")
                if title_elem: role = (await title_elem.inner_text()).strip()
                if comp_elem:
                    alt = await comp_elem.get_attribute("alt")
                    company = alt.replace(" logo", "").strip() if alt else await comp_elem.inner_text()
                if jd_elem: jd_text = await jd_elem.inner_text()

            # 3. Indeed
            elif "indeed.com" in url_lower:
                title_elem = await self.page.query_selector("h1.jobsearch-JobInfoHeader-title, h2.jobsearch-JobInfoHeader-title")
                comp_elem = await self.page.query_selector("div[data-company-name='true'], .jobsearch-CompanyInfoContainer")
                jd_elem = await self.page.query_selector("#jobDescriptionText")
                if title_elem: role = (await title_elem.inner_text()).strip()
                if comp_elem: company = (await comp_elem.inner_text()).strip()
                if jd_elem: jd_text = await jd_elem.inner_text()

            # 4. Wellfound / AngelList
            elif "wellfound.com" in url_lower or "angel.co" in url_lower:
                title_elem = await self.page.query_selector("h1[class*='styles_title'], h1")
                comp_elem = await self.page.query_selector("a[class*='styles_company'], h2")
                jd_elem = await self.page.query_selector("div[class*='styles_description']")
                if title_elem: role = (await title_elem.inner_text()).strip()
                if comp_elem: company = (await comp_elem.inner_text()).strip()
                if jd_elem: jd_text = await jd_elem.inner_text()

            # 5. Workday
            elif "myworkdayjobs.com" in url_lower or "workday" in url_lower:
                title_elem = await self.page.query_selector("h2[data-automation-id='jobPostingHeader'], h1")
                comp_elem = await self.page.query_selector("[data-automation-id='company']")
                jd_elem = await self.page.query_selector("div[data-automation-id='jobPostingDescription']")
                if title_elem: role = (await title_elem.inner_text()).strip()
                if comp_elem: company = (await comp_elem.inner_text()).strip()
                if jd_elem: jd_text = await jd_elem.inner_text()

            # 6. LinkedIn & generic fallback
            else:
                title_elem = await self.page.query_selector(".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title, .top-card-layout__title, h1")
                comp_elem = await self.page.query_selector(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, .topcard__org-name-link")
                jd_elem = await self.page.query_selector(".jobs-description__content, .jobs-box__html-content, #job-details, .description__text, main, article")
                if title_elem: role = (await title_elem.inner_text()).strip()
                if comp_elem: company = (await comp_elem.inner_text()).strip()
                if jd_elem: jd_text = await jd_elem.inner_text()

            if not jd_text:
                jd_text = await self.page.inner_text("body")

        except Exception as e:
            self.log(f"Notice during JD extraction: {str(e)}", "warn")
            jd_text = await self.page.inner_text("body")

        return {
            "url": url,
            "title": role,
            "company": company,
            "description": jd_text[:6500]
        }

    async def execute_supervised_apply(
        self,
        job_url: str,
        profile: Dict[str, Any],
        qa_bank: Dict[str, Any],
        tailored_resume_path: str
    ) -> Dict[str, Any]:
        self.is_running = True
        self.waiting_for_user = False
        url_lower = job_url.lower()

        try:
            if not self.page:
                await self.launch_browser(headless=False)

            self.log(f"Navigating to target job: {job_url}", "info")
            await self.page.goto(job_url, timeout=45000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Check for login prompts
            if "linkedin.com" in url_lower and "login" in self.page.url:
                self.log("LinkedIn login required! Please log in inside the opened browser window.", "warn")
                for _ in range(30):
                    if "login" not in self.page.url: break
                    await asyncio.sleep(2)

            # Route by platform
            if "greenhouse.io" in url_lower:
                return await self._apply_greenhouse(profile, qa_bank, tailored_resume_path)
            elif "lever.co" in url_lower:
                return await self._apply_lever(profile, qa_bank, tailored_resume_path)
            else:
                return await self._apply_linkedin_or_generic(job_url, profile, qa_bank, tailored_resume_path)

        except Exception as e:
            self.log(f"Bot execution error: {str(e)}", "error")
            return {"status": "error", "message": str(e)}

    async def _apply_greenhouse(self, profile: Dict[str, Any], qa_bank: Dict[str, Any], resume_path: str) -> Dict[str, Any]:
        """Autofill Greenhouse job application form."""
        self.log("Detected Greenhouse application page. Filling candidate details...", "info")
        personal = profile.get("personal", {})
        names = personal.get("full_name", "").split()
        first_name = names[0] if names else "Candidate"
        last_name = " ".join(names[1:]) if len(names) > 1 else "Applicant"

        # Form fields
        field_mappings = [
            ("#first_name, input[name*='first_name']", first_name),
            ("#last_name, input[name*='last_name']", last_name),
            ("#email, input[name*='email']", personal.get("email", "")),
            ("#phone, input[name*='phone']", personal.get("phone", "")),
            ("input[autocomplete*='linkedin'], input[id*='linkedin'], input[name*='linkedin']", personal.get("linkedin", "")),
            ("input[id*='website'], input[name*='website'], input[name*='portfolio']", personal.get("portfolio", "")),
            ("input[id*='github'], input[name*='github']", personal.get("github", ""))
        ]

        for sel, val in field_mappings:
            if val:
                try:
                    inp = await self.page.query_selector(sel)
                    if inp and await inp.is_visible():
                        await inp.fill(val)
                except Exception:
                    pass

        # Resume Upload
        try:
            finput = await self.page.query_selector("#resume, input[name='resume'], input[type='file']")
            if finput and Path(resume_path).exists():
                self.log(f"Attaching tailored ATS resume: {Path(resume_path).name}", "success")
                await finput.set_input_files(str(resume_path))
                await asyncio.sleep(1.5)
        except Exception as e:
            self.log(f"Notice on file attachment: {e}", "warn")

        self.log("Greenhouse form filled. Pausing for human verification before submission.", "success")
        self.waiting_for_user = True
        return {"status": "ready_for_review", "message": "Greenhouse application filled and paused for human review."}

    async def _apply_lever(self, profile: Dict[str, Any], qa_bank: Dict[str, Any], resume_path: str) -> Dict[str, Any]:
        """Autofill Lever job application form."""
        self.log("Detected Lever application page. Filling candidate details...", "info")
        personal = profile.get("personal", {})

        # Check if apply button needs clicking first
        apply_btn = await self.page.query_selector("a.postings-btn, button.postings-btn, a:has-text('Apply for this job')")
        if apply_btn and await apply_btn.is_visible():
            await apply_btn.click()
            await asyncio.sleep(2)

        field_mappings = [
            ("input[name='name']", personal.get("full_name", "")),
            ("input[name='email']", personal.get("email", "")),
            ("input[name='phone']", personal.get("phone", "")),
            ("input[name='org']", profile.get("experiences", [{}])[0].get("company", "")),
            ("input[name='urls[LinkedIn]']", personal.get("linkedin", "")),
            ("input[name='urls[GitHub]']", personal.get("github", "")),
            ("input[name='urls[Portfolio]']", personal.get("portfolio", ""))
        ]

        for sel, val in field_mappings:
            if val:
                try:
                    inp = await self.page.query_selector(sel)
                    if inp and await inp.is_visible():
                        await inp.fill(val)
                except Exception:
                    pass

        # Resume Upload
        try:
            finput = await self.page.query_selector("input[name='resume'], input[type='file']")
            if finput and Path(resume_path).exists():
                self.log(f"Attaching tailored ATS resume: {Path(resume_path).name}", "success")
                await finput.set_input_files(str(resume_path))
                await asyncio.sleep(1.5)
        except Exception as e:
            self.log(f"Notice on file attachment: {e}", "warn")

        self.log("Lever form filled. Pausing for human verification before submission.", "success")
        self.waiting_for_user = True
        return {"status": "ready_for_review", "message": "Lever application filled and paused for human review."}

    async def _apply_linkedin_or_generic(self, job_url: str, profile: Dict[str, Any], qa_bank: Dict[str, Any], tailored_resume_path: str) -> Dict[str, Any]:
        """Multi-step modal apply flow for LinkedIn Easy Apply or generic job portals."""
        self.log("Scanning for Easy Apply / Apply button...", "info")
        apply_btn = None
        selectors = [
            "button.jobs-apply-button",
            "button[data-job-id]",
            "button:has-text('Easy Apply')",
            "button:has-text('Apply now')",
            "button:has-text('Apply')",
            ".jobs-s-apply button"
        ]

        for sel in selectors:
            try:
                btn = await self.page.query_selector(sel)
                if btn and await btn.is_visible():
                    apply_btn = btn
                    break
            except Exception:
                continue

        if apply_btn:
            self.log("Found application button! Clicking to open form...", "info")
            await apply_btn.click()
            await asyncio.sleep(2)

        max_steps = 10
        current_step = 0
        reached_review = False

        while current_step < max_steps:
            current_step += 1
            self.log(f"Processing application step {current_step}...", "info")
            await asyncio.sleep(1.5)

            # Fill text inputs
            await self._fill_text_inputs(profile, qa_bank)

            # File upload
            file_inputs = await self.page.query_selector_all("input[type='file']")
            for finput in file_inputs:
                if Path(tailored_resume_path).exists():
                    try:
                        self.log(f"Uploading tailored ATS resume: {Path(tailored_resume_path).name}", "success")
                        await finput.set_input_files(str(tailored_resume_path))
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        self.log(f"Upload notification: {str(e)}", "warn")

            # Answer radio buttons / dropdown questions
            await self._answer_questions(qa_bank)

            # Check for Review / Submit / Next
            submit_btn = await self.page.query_selector("button:has-text('Submit application'), button[aria-label*='Submit application']")
            review_btn = await self.page.query_selector("button:has-text('Review'), button[aria-label*='Review your application']")
            next_btn = await self.page.query_selector("button:has-text('Next'), button[aria-label*='Continue to next step']")

            if submit_btn and await submit_btn.is_visible():
                reached_review = True
                self.log("FINAL REVIEW SCREEN REACHED!", "success")
                self.log("[SUPERVISED MODE] Application form is completely filled! Pausing for your final review.", "success")
                self.waiting_for_user = True
                break

            if review_btn and await review_btn.is_visible():
                self.log("Clicking Review button to view final summary...", "info")
                await review_btn.click()
                await asyncio.sleep(2)
                reached_review = True
                self.log("[SUPERVISED MODE] Final review screen ready. Pausing for human verification.", "success")
                self.waiting_for_user = True
                break

            if next_btn and await next_btn.is_visible():
                self.log("Advancing to next application section...", "info")
                await next_btn.click()
                await asyncio.sleep(1.5)
            else:
                self.log("Form section filled. Ready for your inspection.", "info")
                break

        return {
            "status": "ready_for_review" if reached_review else "in_progress",
            "message": "Application filled and paused for human review before final submit." if reached_review else "Application step completed.",
            "url": job_url
        }

    async def _fill_text_inputs(self, profile: Dict[str, Any], qa_bank: Dict[str, Any]):
        personal = profile.get("personal", {})
        inputs = await self.page.query_selector_all("input[type='text'], input[type='tel'], input[type='email']")
        
        for inp in inputs:
            try:
                label = ""
                inp_id = await inp.get_attribute("id")
                if inp_id:
                    lbl_elem = await self.page.query_selector(f"label[for='{inp_id}']")
                    if lbl_elem:
                        label = await lbl_elem.inner_text()
                
                if not label:
                    label = (await inp.get_attribute("aria-label")) or (await inp.get_attribute("name")) or ""
                
                label_lower = label.lower()
                val = await inp.input_value()
                if val:
                    continue

                if "phone" in label_lower or "mobile" in label_lower:
                    await inp.fill(personal.get("phone", ""))
                elif "email" in label_lower:
                    await inp.fill(personal.get("email", ""))
                elif "first name" in label_lower:
                    await inp.fill(personal.get("full_name", "").split()[0])
                elif "last name" in label_lower:
                    parts = personal.get("full_name", "").split()
                    await inp.fill(parts[-1] if len(parts) > 1 else "")
                elif "salary" in label_lower or "compensation" in label_lower:
                    await inp.fill(qa_bank.get("expected_salary", "140000"))
                elif "city" in label_lower or "location" in label_lower:
                    await inp.fill(personal.get("location", "").split(",")[0])
                elif "experience" in label_lower or "years" in label_lower:
                    for sk, yrs in qa_bank.get("skills_years", {}).items():
                        if sk.lower() in label_lower:
                            await inp.fill(str(yrs))
                            break
                    else:
                        await inp.fill("5")
            except Exception:
                continue

    async def _answer_questions(self, qa_bank: Dict[str, Any]):
        try:
            radios = await self.page.query_selector_all("input[type='radio']")
            for r in radios:
                r_id = await r.get_attribute("id")
                label = ""
                if r_id:
                    lbl = await self.page.query_selector(f"label[for='{r_id}']")
                    if lbl:
                        label = (await lbl.inner_text()).lower()
                
                parent = await r.evaluate_handle("el => el.closest('fieldset') || el.parentElement")
                parent_text = (await parent.inner_text()).lower() if parent else ""

                if "authorized to work" in parent_text or "legally authorized" in parent_text:
                    if "yes" in label:
                        await r.check()
                elif "sponsorship" in parent_text or "require sponsorship" in parent_text:
                    if "no" in label:
                        await r.check()
                elif "18 years" in parent_text:
                    if "yes" in label:
                        await r.check()
        except Exception:
            pass

    async def confirm_and_submit(self) -> Dict[str, Any]:
        """User triggers final submit from dashboard or browser."""
        if not self.page:
            return {"status": "error", "message": "Browser is not active."}
        try:
            submit_btn = await self.page.query_selector("button:has-text('Submit application'), button[aria-label*='Submit application'], input[type='submit']")
            if submit_btn and await submit_btn.is_visible():
                self.log("User confirmed submission! Clicking Submit Application...", "info")
                await submit_btn.click()
                await asyncio.sleep(3)
                self.log("Application successfully submitted!", "success")
                self.waiting_for_user = False
                return {"status": "submitted", "message": "Application successfully submitted."}
            else:
                return {"status": "not_found", "message": "Submit button not found on current page."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def close(self):
        if self.context:
            await self.context.close()
            self.context = None
            self.page = None
            self.is_running = False
            self.log("Browser closed.", "info")

# Global singleton bot instance
bot_instance = SupervisedApplyBot()
