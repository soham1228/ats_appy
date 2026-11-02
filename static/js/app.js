// CareerCopilot Frontend State
const state = {
  currentTab: 'studio',
  activeJob: null, // { title, company, jd_text, url, tailored_pdf, app_id }
  profile: null,
  qaBank: null,
  applications: [],
  logsCount: 0,
  ws: null
};

// Sample High-Demand Job Description for 1-Click Testing
const SAMPLE_JD = `Senior Software Engineer - Full Stack & Distributed Systems
Company: CloudNexus AI
Location: San Francisco, CA / Remote

About the Role:
We are looking for a Senior Software Engineer with strong expertise in Python, FastAPI, React, and AWS to architect high-performance distributed microservices. You will collaborate with cross-functional teams to build resilient backend APIs, optimize PostgreSQL database performance, and deploy containerized services using Docker and Kubernetes.

Requirements:
• 4+ years of professional software engineering experience.
• Proficiency in Python and modern frameworks (FastAPI, Django, or Flask).
• Experience building modern web applications with React or TypeScript.
• Hands-on experience with AWS (EC2, S3, RDS, Lambda) and Docker/Kubernetes.
• Strong knowledge of relational databases (PostgreSQL) and distributed caching with Redis.
• Familiarity with CI/CD automation (GitHub Actions) and Test-Driven Development (TDD).
• Excellent communication skills and passion for mentorship.`;

// DOM Elements
const elements = {
  navItems: document.querySelectorAll('.nav-item'),
  tabPanes: document.querySelectorAll('.tab-pane'),
  sectionTitle: document.getElementById('sectionTitle'),
  sectionDesc: document.getElementById('sectionDesc'),
  terminalWindow: document.getElementById('terminalWindow'),
  logCount: document.getElementById('logCount'),
  btnToggleConsole: document.getElementById('btnToggleConsole'),
  consoleCard: document.getElementById('consoleCard'),
  btnClearLogs: document.getElementById('btnClearLogs'),
  
  // Studio Inputs
  jobUrlInput: document.getElementById('jobUrlInput'),
  btnScrapeUrl: document.getElementById('btnScrapeUrl'),
  roleTitleInput: document.getElementById('roleTitleInput'),
  companyInput: document.getElementById('companyInput'),
  jdTextInput: document.getElementById('jdTextInput'),
  btnLoadSampleJD: document.getElementById('btnLoadSampleJD'),
  btnAnalyzeOnly: document.getElementById('btnAnalyzeOnly'),
  btnTailorAndGenerate: document.getElementById('btnTailorAndGenerate'),

  // ATS Output Elements
  atsStatusBadge: document.getElementById('atsStatusBadge'),
  initialScoreVal: document.getElementById('initialScoreVal'),
  optimizedScoreVal: document.getElementById('optimizedScoreVal'),
  matchedKwCount: document.getElementById('matchedKwCount'),
  matchedKwTags: document.getElementById('matchedKwTags'),
  missingKwCount: document.getElementById('missingKwCount'),
  missingKwTags: document.getElementById('missingKwTags'),

  // Bot Controls
  btnLaunchSupervised: document.getElementById('btnLaunchSupervised'),
  btnConfirmSubmit: document.getElementById('btnConfirmSubmit'),
  btnCloseBrowser: document.getElementById('btnCloseBrowser'),
  activeJobIndicator: document.getElementById('activeJobIndicator'),
  activeJobNotice: document.getElementById('activeJobNotice'),
  botGlobalStatus: document.getElementById('botGlobalStatus'),

  // ATS Previewer Elements
  docName: document.getElementById('docName'),
  docContact: document.getElementById('docContact'),
  docSummary: document.getElementById('docSummary'),
  docSkills: document.getElementById('docSkills'),
  docExperiences: document.getElementById('docExperiences'),
  docEducation: document.getElementById('docEducation'),
  docCertifications: document.getElementById('docCertifications'),
  btnDownloadPdf: document.getElementById('btnDownloadPdf'),
  topLatestPdfLink: document.getElementById('topLatestPdfLink'),
  coverLetterText: document.getElementById('coverLetterText'),
  btnCopyCoverLetter: document.getElementById('btnCopyCoverLetter'),
  subtabBtns: document.querySelectorAll('.subtab-btn'),
  resumeView: document.getElementById('resumeView'),
  coverLetterView: document.getElementById('coverLetterView'),

  // Profile Form
  btnSaveProfile: document.getElementById('btnSaveProfile'),
  profFullName: document.getElementById('profFullName'),
  profEmail: document.getElementById('profEmail'),
  profPhone: document.getElementById('profPhone'),
  profLocation: document.getElementById('profLocation'),
  profLinkedin: document.getElementById('profLinkedin'),
  profGithub: document.getElementById('profGithub'),
  profHeadline: document.getElementById('profHeadline'),
  profSummary: document.getElementById('profSummary'),
  profileSkillsContainer: document.getElementById('profileSkillsContainer'),
  profileExperiencesContainer: document.getElementById('profileExperiencesContainer'),

  // QA Bank
  btnSaveQABank: document.getElementById('btnSaveQABank'),
  qaWorkAuth: document.getElementById('qaWorkAuth'),
  qaSponsorship: document.getElementById('qaSponsorship'),
  qaNotice: document.getElementById('qaNotice'),
  qaYearsExp: document.getElementById('qaYearsExp'),
  qaSalary: document.getElementById('qaSalary'),
  qaRelocate: document.getElementById('qaRelocate'),
  skillsYearsGrid: document.getElementById('skillsYearsGrid'),

  // Tracker
  trackerCountBadge: document.getElementById('trackerCountBadge'),
  applicationsTbody: document.getElementById('applicationsTbody'),

  // Resume upload & LinkedIn import
  resumeDropzone: document.getElementById('resumeDropzone'),
  resumeFileInput: document.getElementById('resumeFileInput'),
  btnBrowseResume: document.getElementById('btnBrowseResume'),
  resumeFileSelectedName: document.getElementById('resumeFileSelectedName'),
  linkedinImportUrl: document.getElementById('linkedinImportUrl'),
  btnImportLinkedin: document.getElementById('btnImportLinkedin'),
  pasteResumeTextInput: document.getElementById('pasteResumeTextInput'),
  btnParsePastedText: document.getElementById('btnParsePastedText'),

  // Platform and engine indicators
  detectedPlatformBadge: document.getElementById('detectedPlatformBadge'),
  activeEngineLabel: document.getElementById('activeEngineLabel'),
  btnSwitchEngine: document.getElementById('btnSwitchEngine'),

  // AI & Accounts Settings
  aiProviderSelect: document.getElementById('aiProviderSelect'),
  aiApiKeyGroup: document.getElementById('aiApiKeyGroup'),
  aiApiKeyInput: document.getElementById('aiApiKeyInput'),
  btnToggleApiKey: document.getElementById('btnToggleApiKey'),
  aiModelGroup: document.getElementById('aiModelGroup'),
  aiModelInput: document.getElementById('aiModelInput'),
  ollamaUrlGroup: document.getElementById('ollamaUrlGroup'),
  ollamaUrlInput: document.getElementById('ollamaUrlInput'),
  btnSaveAISettings: document.getElementById('btnSaveAISettings')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupWebSocket();
  setupEventListeners();
  await loadProfile();
  await loadQABank();
  await loadApplications();
  await loadSettings();
});

// Navigation Handling
function setupNavigation() {
  const titles = {
    studio: { title: 'Auto-Apply Studio', desc: 'Paste job descriptions, maximize ATS keyword match, and auto-fill applications safely.' },
    preview: { title: 'ATS CV & Cover Letter', desc: 'Live preview of your ATS-optimized machine-readable resume and tailored cover letter.' },
    profile: { title: 'Master Profile', desc: 'Your comprehensive career source of truth, experiences, and technical competencies.' },
    qabank: { title: 'Screening QA Bank', desc: 'Pre-configured answers for common ATS screening, salary, and eligibility questions.' },
    tracker: { title: 'Applications Tracker', desc: 'Track applied roles, customized resume variations, and match scores.' },
    accounts: { title: 'AI Engine & Connected Accounts', desc: 'Configure AI models for resume rewriting and manage one-time persistent logins for job boards.' }
  };

  elements.navItems.forEach(item => {
    item.addEventListener('click', () => {
      const tab = item.getAttribute('data-tab');
      elements.navItems.forEach(n => n.classList.remove('active'));
      elements.tabPanes.forEach(p => p.classList.remove('active'));

      item.classList.add('active');
      const pane = document.getElementById(`tab-${tab}`);
      if (pane) pane.classList.add('active');

      if (titles[tab]) {
        elements.sectionTitle.textContent = titles[tab].title;
        elements.sectionDesc.textContent = titles[tab].desc;
      }
      state.currentTab = tab;
    });
  });

  // Preview Subtabs (Resume vs Cover letter)
  elements.subtabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.subtabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const sub = btn.getAttribute('data-subtab');
      if (sub === 'resumeView') {
        elements.resumeView.classList.remove('hidden');
        elements.coverLetterView.classList.add('hidden');
      } else {
        elements.resumeView.classList.add('hidden');
        elements.coverLetterView.classList.remove('hidden');
      }
    });
  });
}

// WebSocket Setup for Real-Time Bot Logs
function setupWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

  try {
    state.ws = new WebSocket(wsUrl);
    state.ws.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        appendLog(log.message, log.level || 'info', log.timestamp);
      } catch (e) {
        appendLog(event.data, 'info');
      }
    };
    state.ws.onclose = () => {
      setTimeout(setupWebSocket, 4000);
    };
  } catch (err) {
    console.warn("WebSocket fallback:", err);
  }
}

function appendLog(message, level = 'info', timestamp = null) {
  state.logsCount++;
  elements.logCount.textContent = state.logsCount;

  const timeStr = timestamp || new Date().toTimeString().split(' ')[0];
  const line = document.createElement('div');
  line.className = `term-line ${level}`;
  line.innerHTML = `<span class="t-time">[${timeStr}]</span> ${escapeHtml(message)}`;
  elements.terminalWindow.appendChild(line);
  elements.terminalWindow.scrollTop = elements.terminalWindow.scrollHeight;

  // React to status changes in logs
  if (message.includes('FINAL REVIEW SCREEN REACHED') || message.includes('SUPERVISED MODE')) {
    elements.botGlobalStatus.textContent = 'Supervised Bot: PAUSED FOR REVIEW';
    elements.btnConfirmSubmit.classList.remove('hidden');
    elements.btnCloseBrowser.classList.remove('hidden');
    elements.activeJobNotice.textContent = 'Form filled! Inspect browser window, then click "Confirm & Submit" below.';
  } else if (message.includes('successfully submitted')) {
    elements.botGlobalStatus.textContent = 'Supervised Bot: SUBMITTED!';
    elements.btnConfirmSubmit.classList.add('hidden');
    loadApplications();
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Event Listeners
function setupEventListeners() {
  // Load Sample JD
  elements.btnLoadSampleJD.addEventListener('click', () => {
    elements.jdTextInput.value = SAMPLE_JD;
    elements.roleTitleInput.value = 'Senior Software Engineer';
    elements.companyInput.value = 'CloudNexus AI';
    elements.jobUrlInput.value = 'https://www.linkedin.com/jobs/view/sample-cloudnexus';
    appendLog('Loaded sample high-tech job description for testing.', 'info');
  });

  // Scrape JD from URL
  elements.btnScrapeUrl.addEventListener('click', async () => {
    const url = elements.jobUrlInput.value.trim();
    if (!url) {
      alert('Please enter a job URL first.');
      return;
    }
    elements.btnScrapeUrl.disabled = true;
    elements.btnScrapeUrl.textContent = 'Fetching...';
    appendLog(`Extracting job details from: ${url}`, 'info');

    try {
      const res = await fetch('/api/scrape-job-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();
      if (res.ok) {
        if (data.title) elements.roleTitleInput.value = data.title;
        if (data.company) elements.companyInput.value = data.company;
        if (data.description) elements.jdTextInput.value = data.description;
        appendLog(`Successfully extracted job details for '${data.title || 'Role'}'.`, 'success');
      } else {
        alert(data.detail || 'Could not scrape URL automatically. You can paste the description directly.');
      }
    } catch (err) {
      appendLog(`Scrape error: ${err.message}`, 'error');
    } finally {
      elements.btnScrapeUrl.disabled = false;
      elements.btnScrapeUrl.textContent = 'Fetch JD';
    }
  });

  // Check ATS Score Only
  elements.btnAnalyzeOnly.addEventListener('click', async () => {
    const jdText = elements.jdTextInput.value.trim();
    if (!jdText) {
      alert('Please enter or paste a job description.');
      return;
    }
    appendLog('Running ATS keyword match analysis...', 'info');
    elements.btnAnalyzeOnly.disabled = true;

    try {
      const res = await fetch('/api/analyze-jd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jd_text: jdText,
          role_title: elements.roleTitleInput.value.trim(),
          company: elements.companyInput.value.trim()
        })
      });
      const data = await res.json();
      if (res.ok) {
        renderATSAnalysis(data.ats_match);
      }
    } catch (err) {
      appendLog(`Analysis error: ${err.message}`, 'error');
    } finally {
      elements.btnAnalyzeOnly.disabled = false;
    }
  });

  // Optimize & Generate Tailored ATS Resume
  elements.btnTailorAndGenerate.addEventListener('click', async () => {
    const jdText = elements.jdTextInput.value.trim();
    if (!jdText) {
      alert('Please enter or paste a job description.');
      return;
    }

    elements.btnTailorAndGenerate.disabled = true;
    elements.btnTailorAndGenerate.innerHTML = '<span>⏳</span> Tailoring ATS Resume...';
    appendLog('Starting ATS optimization: Re-ranking skills and weaving keywords into achievements...', 'info');

    try {
      const res = await fetch('/api/tailor-resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jd_text: jdText,
          role_title: elements.roleTitleInput.value.trim(),
          company: elements.companyInput.value.trim(),
          job_url: elements.jobUrlInput.value.trim()
        })
      });
      const data = await res.json();
      if (res.ok) {
        renderATSAnalysis(data.initial_match, data.optimized_match);
        renderDocumentPreview(data.tailored_profile, data.cover_letter, data.pdf_download_url);
        
        // Save active job state
        state.activeJob = {
          title: elements.roleTitleInput.value.trim() || data.target_title,
          company: elements.companyInput.value.trim() || 'Target Company',
          url: elements.jobUrlInput.value.trim() || 'https://www.linkedin.com/jobs',
          pdf_path: data.pdf_path,
          app_id: data.app_id,
          download_url: data.pdf_download_url
        };

        // Enable Supervised Bot Trigger
        elements.btnLaunchSupervised.disabled = false;
        elements.activeJobNotice.textContent = `Ready to apply for '${state.activeJob.title}' with ATS score of ${data.optimized_match.score}%.`;
        elements.topLatestPdfLink.href = data.pdf_download_url;
        elements.topLatestPdfLink.classList.remove('hidden');

        appendLog(`Tailored ATS resume generated successfully (${data.pdf_filename})! Ready for Supervised Apply.`, 'success');
        loadApplications();
      } else {
        alert(data.detail || 'Error generating tailored resume.');
      }
    } catch (err) {
      appendLog(`Tailoring failed: ${err.message}`, 'error');
    } finally {
      elements.btnTailorAndGenerate.disabled = false;
      elements.btnTailorAndGenerate.innerHTML = '<span>✨</span> Optimize & Generate ATS CV';
    }
  });

  // Launch Supervised Bot
  elements.btnLaunchSupervised.addEventListener('click', async () => {
    if (!state.activeJob || !state.activeJob.pdf_path) {
      alert('Please tailor an ATS resume first.');
      return;
    }

    const jobUrl = elements.jobUrlInput.value.trim() || state.activeJob.url;
    appendLog(`[BOT TRIGGER] Launching supervised application runner for URL: ${jobUrl}`, 'info');
    elements.btnLaunchSupervised.disabled = true;
    elements.botGlobalStatus.textContent = 'Supervised Bot: RUNNING';

    try {
      const res = await fetch('/api/bot/launch-supervised', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_url: jobUrl,
          tailored_pdf_path: state.activeJob.pdf_path,
          job_id: state.activeJob.app_id
        })
      });
      const data = await res.json();
      if (res.ok) {
        appendLog('Browser opened! Watching form interaction in real-time.', 'info');
      }
    } catch (err) {
      appendLog(`Bot launch error: ${err.message}`, 'error');
      elements.btnLaunchSupervised.disabled = false;
    }
  });

  // Confirm & Submit
  elements.btnConfirmSubmit.addEventListener('click', async () => {
    elements.btnConfirmSubmit.disabled = true;
    appendLog('Sending confirmation to submit application...', 'info');
    try {
      const res = await fetch('/api/bot/confirm-submit', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'submitted') {
        appendLog('Application submitted!', 'success');
        elements.btnConfirmSubmit.classList.add('hidden');
      }
    } catch (err) {
      appendLog(`Confirmation error: ${err.message}`, 'error');
    } finally {
      elements.btnConfirmSubmit.disabled = false;
    }
  });

  // Close Browser
  elements.btnCloseBrowser.addEventListener('click', async () => {
    await fetch('/api/bot/close', { method: 'POST' });
    elements.btnCloseBrowser.classList.add('hidden');
    elements.btnConfirmSubmit.classList.add('hidden');
    elements.btnLaunchSupervised.disabled = false;
    elements.botGlobalStatus.textContent = 'Supervised Bot: Ready';
    appendLog('Browser session closed.', 'info');
  });

  // Copy Cover Letter
  elements.btnCopyCoverLetter.addEventListener('click', () => {
    elements.coverLetterText.select();
    document.execCommand('copy');
    elements.btnCopyCoverLetter.textContent = 'Copied!';
    setTimeout(() => { elements.btnCopyCoverLetter.textContent = '📋 Copy Text'; }, 2000);
  });

  // Toggle Console
  elements.btnToggleConsole.addEventListener('click', () => {
    elements.consoleCard.scrollIntoView({ behavior: 'smooth' });
  });

  // Clear Logs
  elements.btnClearLogs.addEventListener('click', () => {
    elements.terminalWindow.innerHTML = '';
    state.logsCount = 0;
    elements.logCount.textContent = '0';
  });

  // Save Profile
  elements.btnSaveProfile.addEventListener('click', saveProfileData);

  // Save QA Bank
  elements.btnSaveQABank.addEventListener('click', saveQABankData);

  // Resume PDF File Input Change
  if (elements.resumeFileInput) {
    elements.resumeFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleResumeUpload(e.target.files[0]);
      }
    });
  }

  // Resume Dropzone Drag & Drop
  if (elements.resumeDropzone) {
    ['dragenter', 'dragover'].forEach(evt => {
      elements.resumeDropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.resumeDropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'dragend'].forEach(evt => {
      elements.resumeDropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.resumeDropzone.classList.remove('dragover');
      });
    });

    elements.resumeDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.resumeDropzone.classList.remove('dragover');
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleResumeUpload(e.dataTransfer.files[0]);
      }
    });

    // Prevent accidental window navigation when dragging files
    window.addEventListener('dragover', (e) => e.preventDefault());
    window.addEventListener('drop', (e) => e.preventDefault());
  }

  // LinkedIn Profile Import
  if (elements.btnImportLinkedin) {
    elements.btnImportLinkedin.addEventListener('click', handleLinkedInImport);
  }

  // Parse Pasted Resume Text
  if (elements.btnParsePastedText && elements.pasteResumeTextInput) {
    elements.btnParsePastedText.addEventListener('click', handleParsePastedText);
  }

  // Platform auto-detect on URL input
  if (elements.jobUrlInput) {
    elements.jobUrlInput.addEventListener('input', updatePlatformBadge);
  }

  // Switch Engine shortcut link
  if (elements.btnSwitchEngine) {
    elements.btnSwitchEngine.addEventListener('click', (e) => {
      e.preventDefault();
      const accountsTab = document.querySelector('[data-tab="accounts"]');
      if (accountsTab) accountsTab.click();
    });
  }

  // AI Provider Selection UI toggle
  if (elements.aiProviderSelect) {
    elements.aiProviderSelect.addEventListener('change', updateAISettingsUI);
  }

  // Save AI Settings
  if (elements.btnSaveAISettings) {
    elements.btnSaveAISettings.addEventListener('click', saveAISettings);
  }

  // Toggle API Key visibility
  if (elements.btnToggleApiKey) {
    elements.btnToggleApiKey.addEventListener('click', () => {
      const type = elements.aiApiKeyInput.type === 'password' ? 'text' : 'password';
      elements.aiApiKeyInput.type = type;
      elements.btnToggleApiKey.textContent = type === 'password' ? '👁️' : '🙈';
    });
  }

  // Connected Platform Login buttons
  document.querySelectorAll('.btnPlatformLogin').forEach(btn => {
    btn.addEventListener('click', () => {
      const platform = btn.getAttribute('data-platform');
      if (platform) handlePlatformLogin(platform);
    });
  });
}

// Render ATS Match Breakdown
function renderATSAnalysis(initialMatch, optimizedMatch = null) {
  elements.initialScoreVal.textContent = `${initialMatch.score}%`;
  
  if (optimizedMatch) {
    elements.optimizedScoreVal.textContent = `${optimizedMatch.score}%`;
    elements.atsStatusBadge.textContent = `Optimized (+${optimizedMatch.score - initialMatch.score}%)`;
    elements.atsStatusBadge.className = 'badge badge-accent';
  } else {
    elements.optimizedScoreVal.textContent = '--%';
    elements.atsStatusBadge.textContent = 'Analyzed';
    elements.atsStatusBadge.className = 'badge badge-info';
  }

  // Matched Tags
  elements.matchedKwCount.textContent = initialMatch.matched_count;
  elements.matchedKwTags.innerHTML = '';
  if (initialMatch.matched_keywords && initialMatch.matched_keywords.length > 0) {
    initialMatch.matched_keywords.forEach(kw => {
      const tag = document.createElement('span');
      tag.className = 'tag match';
      tag.textContent = `${kw.keyword} (${kw.importance}x)`;
      elements.matchedKwTags.appendChild(tag);
    });
  } else {
    elements.matchedKwTags.innerHTML = '<span class="placeholder-text">None detected yet.</span>';
  }

  // Missing Tags
  elements.missingKwCount.textContent = initialMatch.missing_count;
  elements.missingKwTags.innerHTML = '';
  if (initialMatch.missing_keywords && initialMatch.missing_keywords.length > 0) {
    initialMatch.missing_keywords.forEach(kw => {
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = `${kw.keyword} (${kw.importance}x)`;
      elements.missingKwTags.appendChild(tag);
    });
  } else {
    elements.missingKwTags.innerHTML = '<span class="placeholder-text">Great match! No critical keywords missing.</span>';
  }
}

// Render Clean ATS Document Preview
function renderDocumentPreview(profile, coverLetter, downloadUrl) {
  const p = profile.personal || {};
  elements.docName.textContent = p.full_name || 'Candidate';
  elements.docContact.textContent = [p.email, p.phone, p.location, p.linkedin, p.github].filter(Boolean).join(' | ');
  elements.docSummary.textContent = profile.summary || '';

  // Skills
  let skillsHtml = '';
  for (const [cat, list] of Object.entries(profile.skills || {})) {
    if (list && list.length > 0) {
      skillsHtml += `<p style="margin-bottom: 4px;"><b>${cat}:</b> ${list.join(', ')}</p>`;
    }
  }
  elements.docSkills.innerHTML = skillsHtml;

  // Experiences
  let expHtml = '';
  (profile.experiences || []).forEach(exp => {
    expHtml += `
      <div class="ats-experience-item">
        <div class="ats-exp-header">
          <span class="ats-exp-title">${exp.title} | ${exp.company}</span>
          <span class="ats-exp-meta">${exp.location || ''} (${exp.start_date} – ${exp.end_date})</span>
        </div>
        <ul class="ats-bullets">
          ${(exp.bullets || []).map(b => `<li>${b}</li>`).join('')}
        </ul>
      </div>
    `;
  });
  elements.docExperiences.innerHTML = expHtml;

  // Education
  let eduHtml = '';
  (profile.education || []).forEach(edu => {
    eduHtml += `
      <div class="ats-exp-header" style="margin-bottom: 4px;">
        <span class="ats-exp-title">${edu.degree} – ${edu.institution}</span>
        <span class="ats-exp-meta">${edu.graduation_year} ${edu.gpa ? `| GPA: ${edu.gpa}` : ''}</span>
      </div>
    `;
  });
  elements.docEducation.innerHTML = eduHtml;

  // Certifications
  if (profile.certifications && profile.certifications.length > 0) {
    elements.docCertifications.innerHTML = `<p>• ${profile.certifications.join(' • ')}</p>`;
  }

  // Cover Letter
  elements.coverLetterText.value = coverLetter || '';

  // Download Link
  elements.btnDownloadPdf.href = downloadUrl;
}

// Populate Profile Form and Live Preview
function populateProfileUI(data) {
  if (!data) return;
  state.profile = data;

  const p = data.personal || {};
  if (elements.profFullName) elements.profFullName.value = p.full_name || '';
  if (elements.profEmail) elements.profEmail.value = p.email || '';
  if (elements.profPhone) elements.profPhone.value = p.phone || '';
  if (elements.profLocation) elements.profLocation.value = p.location || '';
  if (elements.profLinkedin) elements.profLinkedin.value = p.linkedin || '';
  if (elements.profGithub) elements.profGithub.value = p.github || '';
  if (elements.profHeadline) elements.profHeadline.value = data.headline || '';
  if (elements.profSummary) elements.profSummary.value = data.summary || '';

  // Skills inputs
  let skillsForm = '';
  for (const [cat, list] of Object.entries(data.skills || {})) {
    skillsForm += `
      <div class="form-group">
        <label>${cat}</label>
        <input type="text" class="profile-skill-input" data-category="${cat}" value="${(list || []).join(', ')}" />
      </div>
    `;
  }
  if (elements.profileSkillsContainer) elements.profileSkillsContainer.innerHTML = skillsForm;

  // Experiences
  let expForm = '';
  (data.experiences || []).forEach((exp, idx) => {
    expForm += `
      <div class="card glass-card mb-3" style="margin-bottom: 14px;">
        <div class="form-row">
          <div class="form-group flex-1">
            <label>Job Title</label>
            <input type="text" class="exp-title" data-idx="${idx}" value="${exp.title || ''}" />
          </div>
          <div class="form-group flex-1">
            <label>Company</label>
            <input type="text" class="exp-company" data-idx="${idx}" value="${exp.company || ''}" />
          </div>
        </div>
        <div class="form-group">
          <label>Bullet Points (One per line)</label>
          <textarea rows="3" class="exp-bullets" data-idx="${idx}">${(exp.bullets || []).join('\n')}</textarea>
        </div>
      </div>
    `;
  });
  if (elements.profileExperiencesContainer) elements.profileExperiencesContainer.innerHTML = expForm;

  // Render document preview with master data
  renderDocumentPreview(data, '', '#');
}

// Load and Populate Master Profile
async function loadProfile() {
  try {
    const res = await fetch('/api/profile');
    const data = await res.json();
    populateProfileUI(data);
  } catch (err) {
    console.error('Error loading profile:', err);
  }
}

async function saveProfileData() {
  const updated = {
    personal: {
      full_name: elements.profFullName.value.trim(),
      email: elements.profEmail.value.trim(),
      phone: elements.profPhone.value.trim(),
      location: elements.profLocation.value.trim(),
      linkedin: elements.profLinkedin.value.trim(),
      github: elements.profGithub.value.trim()
    },
    headline: elements.profHeadline.value.trim(),
    summary: elements.profSummary.value.trim(),
    skills: {},
    experiences: state.profile.experiences || [],
    education: state.profile.education || [],
    certifications: state.profile.certifications || [],
    projects: state.profile.projects || []
  };

  // Extract skills
  document.querySelectorAll('.profile-skill-input').forEach(inp => {
    const cat = inp.getAttribute('data-category');
    updated.skills[cat] = inp.value.split(',').map(s => s.trim()).filter(Boolean);
  });

  // Extract experiences
  const expTitles = document.querySelectorAll('.exp-title');
  const expCompanies = document.querySelectorAll('.exp-company');
  const expBullets = document.querySelectorAll('.exp-bullets');

  expTitles.forEach((inp, idx) => {
    if (updated.experiences[idx]) {
      updated.experiences[idx].title = inp.value.trim();
      updated.experiences[idx].company = expCompanies[idx].value.trim();
      updated.experiences[idx].bullets = expBullets[idx].value.split('\n').map(b => b.trim()).filter(Boolean);
    }
  });

  try {
    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    });
    if (res.ok) {
      state.profile = updated;
      alert('Master profile saved successfully!');
      renderDocumentPreview(updated, '', '#');
    }
  } catch (err) {
    alert('Error saving profile: ' + err.message);
  }
}

// Load and Populate QA Bank
async function loadQABank() {
  try {
    const res = await fetch('/api/qa-bank');
    const data = await res.json();
    state.qaBank = data;

    elements.qaWorkAuth.value = data.work_authorization || 'Yes';
    elements.qaSponsorship.value = data.visa_sponsorship_needed || 'No';
    elements.qaNotice.value = data.notice_period || '2 weeks';
    elements.qaYearsExp.value = data.years_of_experience || '5+';
    elements.qaSalary.value = data.expected_salary || '$140,000';
    elements.qaRelocate.value = data.willing_to_relocate || 'Open / Remote';

    // Skills years grid
    let gridHtml = '';
    for (const [sk, yrs] of Object.entries(data.skills_years || {})) {
      gridHtml += `
        <div class="skills-years-item">
          <span>${sk}</span>
          <input type="text" class="qa-skill-yr" data-skill="${sk}" value="${yrs}" />
        </div>
      `;
    }
    elements.skillsYearsGrid.innerHTML = gridHtml;
  } catch (err) {
    console.error('Error loading QA bank:', err);
  }
}

async function saveQABankData() {
  const updated = {
    work_authorization: elements.qaWorkAuth.value.trim(),
    visa_sponsorship_needed: elements.qaSponsorship.value.trim(),
    notice_period: elements.qaNotice.value.trim(),
    years_of_experience: elements.qaYearsExp.value.trim(),
    expected_salary: elements.qaSalary.value.trim(),
    willing_to_relocate: elements.qaRelocate.value.trim(),
    skills_years: {},
    custom_answers: state.qaBank.custom_answers || {}
  };

  document.querySelectorAll('.qa-skill-yr').forEach(inp => {
    const sk = inp.getAttribute('data-skill');
    updated.skills_years[sk] = inp.value.trim();
  });

  try {
    const res = await fetch('/api/qa-bank', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    });
    if (res.ok) {
      state.qaBank = updated;
      alert('QA Bank saved successfully!');
    }
  } catch (err) {
    alert('Error saving QA Bank: ' + err.message);
  }
}

// Load Applications History
async function loadApplications() {
  try {
    const res = await fetch('/api/applications');
    const data = await res.json();
    state.applications = data;
    elements.trackerCountBadge.textContent = `${data.length} Applications`;

    if (!data || data.length === 0) {
      elements.applicationsTbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-4">No applications tracked yet. Tailor your first job in the Studio!</td>
        </tr>
      `;
      return;
    }

    let rowsHtml = '';
    data.forEach(app => {
      const statusClass = app.status === 'Applied' ? 'status-applied' : (app.status.includes('Review') || app.status.includes('Paused') ? 'status-paused' : 'status-ready');
      rowsHtml += `
        <tr>
          <td>
            <strong>${escapeHtml(app.title)}</strong><br>
            <span style="font-size: 0.78rem; color: #9CA3AF;">${escapeHtml(app.company)}</span>
          </td>
          <td>${app.created_at || 'Today'}</td>
          <td><span class="badge badge-info">${app.initial_score}%</span></td>
          <td><span class="badge badge-accent" style="color: #34D399;">${app.optimized_score}%</span></td>
          <td><span class="status-pill ${statusClass}">${app.status}</span></td>
          <td>
            <a href="/api/download-resume/${app.pdf_filename}" class="text-btn" target="_blank">📥 ${app.pdf_filename}</a>
          </td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="reapplyJob('${app.id}')">Apply</button>
          </td>
        </tr>
      `;
    });
    elements.applicationsTbody.innerHTML = rowsHtml;
  } catch (err) {
    console.error('Error loading applications:', err);
  }
}

// Re-apply to a previously tailored job
window.reapplyJob = function(appId) {
  const found = state.applications.find(a => a.id === appId);
  if (found) {
    elements.roleTitleInput.value = found.title;
    elements.companyInput.value = found.company;
    if (found.job_url) elements.jobUrlInput.value = found.job_url;
    
    state.activeJob = {
      title: found.title,
      company: found.company,
      url: found.job_url || 'https://www.linkedin.com/jobs',
      pdf_path: found.pdf_path,
      app_id: found.id,
      download_url: `/api/download-resume/${found.pdf_filename}`
    };

    elements.btnLaunchSupervised.disabled = false;
    elements.activeJobNotice.textContent = `Selected '${found.title}' for supervised application.`;
    
    // Switch to studio tab
    document.querySelector('[data-tab="studio"]').click();
  }
};

// --- Profile Importer & AI Platform Handlers ---

// Upload and Parse Resume PDF
async function handleResumeUpload(file) {
  if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
    alert('Please upload a PDF resume file.');
    return;
  }
  elements.resumeFileSelectedName.textContent = `Uploading & parsing: ${file.name}...`;
  appendLog(`Uploading resume PDF: ${file.name}...`, 'info');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload-resume', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      elements.resumeFileSelectedName.textContent = `✓ Loaded: ${file.name}`;
      appendLog(`Successfully extracted resume for '${data.name || 'Candidate'}'. Master Profile updated!`, 'success');
      populateProfileUI(data.profile);
      if (elements.resumeFileInput) elements.resumeFileInput.value = '';
      alert(`Resume parsed successfully for ${data.name || 'Candidate'}! Your Master Profile and preview have been updated.`);
    } else {
      alert(data.detail || 'Failed to parse resume PDF.');
      elements.resumeFileSelectedName.textContent = 'Upload failed';
    }
  } catch (err) {
    appendLog(`Resume upload error: ${err.message}`, 'error');
    elements.resumeFileSelectedName.textContent = 'Upload error';
  }
}

// Scrape & Import LinkedIn Profile
async function handleLinkedInImport() {
  const url = elements.linkedinImportUrl.value.trim();
  if (!url) {
    alert('Please enter your LinkedIn profile URL (e.g. https://www.linkedin.com/in/username)');
    return;
  }
  elements.btnImportLinkedin.disabled = true;
  elements.btnImportLinkedin.textContent = 'Fetching...';
  appendLog(`Connecting to browser to import LinkedIn profile: ${url}`, 'info');

  try {
    const res = await fetch('/api/import-linkedin-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_url: url })
    });
    const data = await res.json();
    if (res.ok && data.status === 'success' && data.profile) {
      populateProfileUI(data.profile);
      appendLog(`Successfully imported LinkedIn profile for ${data.profile.personal?.full_name || 'Candidate'}!`, 'success');
      alert(`LinkedIn profile imported for ${data.profile.personal?.full_name || 'Candidate'}!`);
    } else {
      alert(data.message || 'Could not import LinkedIn profile. Please ensure you are logged into LinkedIn in the browser first via the "AI & Accounts" tab.');
    }
  } catch (err) {
    appendLog(`LinkedIn import error: ${err.message}`, 'error');
  } finally {
    elements.btnImportLinkedin.disabled = false;
    elements.btnImportLinkedin.textContent = 'Fetch Profile';
  }
}

// Parse Directly Pasted Resume or LinkedIn Text
async function handleParsePastedText() {
  const text = elements.pasteResumeTextInput ? elements.pasteResumeTextInput.value.trim() : '';
  if (!text) {
    alert('Please paste some resume or LinkedIn text into the box first.');
    return;
  }
  elements.btnParsePastedText.disabled = true;
  elements.btnParsePastedText.textContent = 'Parsing...';
  appendLog('Parsing pasted resume text into structured profile...', 'info');

  try {
    const res = await fetch('/api/parse-resume-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (res.ok && data.profile) {
      populateProfileUI(data.profile);
      appendLog(`Successfully extracted profile for '${data.name || 'Candidate'}'. Master Profile updated!`, 'success');
      alert(`Resume text parsed successfully for ${data.name || 'Candidate'}! Your Master Profile has been updated.`);
    } else {
      alert(data.detail || 'Could not parse resume text.');
    }
  } catch (err) {
    appendLog(`Parse text error: ${err.message}`, 'error');
  } finally {
    elements.btnParsePastedText.disabled = false;
    elements.btnParsePastedText.textContent = '📋 Parse Pasted Text';
  }
}

// Detect Job Platform from URL
function detectPlatform(url) {
  const u = (url || '').toLowerCase();
  if (u.includes('linkedin.com')) return { name: 'LinkedIn Easy Apply / Posting', icon: '💼' };
  if (u.includes('greenhouse.io')) return { name: 'Greenhouse Board', icon: '🏢' };
  if (u.includes('lever.co')) return { name: 'Lever Direct Apply', icon: '⚙️' };
  if (u.includes('indeed.com')) return { name: 'Indeed Job Portal', icon: '🎯' };
  if (u.includes('wellfound.com') || u.includes('angel.co')) return { name: 'Wellfound Startup Job', icon: '🦄' };
  if (u.includes('myworkdayjobs.com') || u.includes('workday')) return { name: 'Workday Enterprise', icon: '🌐' };
  return { name: 'Auto-Detect Platform', icon: '🌐' };
}

function updatePlatformBadge() {
  const url = elements.jobUrlInput.value.trim();
  const info = detectPlatform(url);
  if (elements.detectedPlatformBadge) {
    elements.detectedPlatformBadge.textContent = `${info.icon} ${info.name}`;
  }
}

// Launch Persistent Browser for One-Time Login
async function handlePlatformLogin(platform) {
  appendLog(`Launching persistent browser to log into ${platform.toUpperCase()}...`, 'info');
  try {
    const res = await fetch('/api/platform/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform })
    });
    const data = await res.json();
    appendLog(`Browser opened for ${platform.toUpperCase()}. Log in to save your credentials and session cookies permanently!`, 'warn');
  } catch (err) {
    appendLog(`Error opening platform login: ${err.message}`, 'error');
  }
}

// Load and Bind AI Settings
async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const settings = await res.json();
    if (settings) {
      if (elements.aiProviderSelect) elements.aiProviderSelect.value = settings.ai_provider || 'builtin';
      if (elements.aiApiKeyInput) elements.aiApiKeyInput.value = settings.ai_api_key || '';
      if (elements.aiModelInput) elements.aiModelInput.value = settings.ai_model || 'gpt-4o-mini';
      if (elements.ollamaUrlInput) elements.ollamaUrlInput.value = settings.ollama_url || 'http://localhost:11434';
      updateAISettingsUI();
    }
  } catch (err) {
    console.warn('Error loading settings:', err);
  }
}

function updateAISettingsUI() {
  if (!elements.aiProviderSelect) return;
  const provider = elements.aiProviderSelect.value;
  if (provider === 'builtin') {
    elements.aiApiKeyGroup.classList.add('hidden');
    elements.aiModelGroup.classList.add('hidden');
    elements.ollamaUrlGroup.classList.add('hidden');
  } else if (provider === 'ollama') {
    elements.aiApiKeyGroup.classList.add('hidden');
    elements.aiModelGroup.classList.remove('hidden');
    elements.ollamaUrlGroup.classList.remove('hidden');
  } else {
    elements.aiApiKeyGroup.classList.remove('hidden');
    elements.aiModelGroup.classList.remove('hidden');
    elements.ollamaUrlGroup.classList.add('hidden');
  }
  updateActiveEngineLabel();
}

function updateActiveEngineLabel() {
  if (!elements.aiProviderSelect || !elements.activeEngineLabel) return;
  const provider = elements.aiProviderSelect.value;
  const labels = {
    builtin: '⚡ Tailoring Engine: Smart Built-in Optimizer',
    openai: `🧠 Tailoring Engine: OpenAI (${elements.aiModelInput?.value || 'GPT-4o-mini'})`,
    gemini: `✨ Tailoring Engine: Google Gemini (${elements.aiModelInput?.value || '1.5 Flash'})`,
    ollama: `🦙 Tailoring Engine: Ollama Local (${elements.aiModelInput?.value || 'Llama 3'})`
  };
  elements.activeEngineLabel.textContent = labels[provider] || labels.builtin;
}

async function saveAISettings() {
  const settings = {
    ai_provider: elements.aiProviderSelect.value,
    ai_api_key: elements.aiApiKeyInput.value.trim(),
    ai_model: elements.aiModelInput.value.trim(),
    ollama_url: elements.ollamaUrlInput.value.trim()
  };

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (res.ok) {
      appendLog(`Saved AI settings (Engine: ${settings.ai_provider.toUpperCase()})`, 'success');
      updateActiveEngineLabel();
      alert('AI & Account settings saved successfully!');
    }
  } catch (err) {
    alert('Error saving settings: ' + err.message);
  }
}

