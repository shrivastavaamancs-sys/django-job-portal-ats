import io
import re
import zipfile

from django.core.files.storage import default_storage
from docx import Document
from pypdf import PdfReader

STOP_WORDS = {
    "and", "or", "the", "a", "an", "to", "of", "in", "for", "with", "on",
    "at", "by", "from", "as", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "will", "would", "should", "can", "could", "this",
    "that", "we", "you", "our", "your", "must", "good", "strong", "years",
    "year", "experience", "looking", "role", "work", "working", "knowledge",
    "ability", "skills", "skill", "using", "based", "required",
}


def _extract_from_bytes(raw_bytes: bytes, file_name: str) -> str:
    name = (file_name or "").lower()
    stream = io.BytesIO(raw_bytes)

    if name.endswith(".pdf"):
        reader = PdfReader(stream)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages_text)

    if name.endswith(".docx"):
        if not zipfile.is_zipfile(stream):
            raise ValueError(
                "Invalid .docx file (File is not a zip file). "
                "Kripya actual MS Word/LibreOffice se saved .docx ya .pdf upload karein."
            )
        stream.seek(0)
        doc = Document(stream)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        return "\n".join(paragraphs)

    raise ValueError("Unsupported file format. Sirf .pdf ya .docx use karein.")


def extract_text_from_file(uploaded_file) -> str:
    """Uploaded file ya FileField se plain text nikaalta hai (.pdf ya .docx)."""
    if uploaded_file is None:
        return ""

    name = getattr(uploaded_file, "name", "") or ""
    raw_bytes = uploaded_file.read()
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)

    if not raw_bytes:
        return ""

    return _extract_from_bytes(raw_bytes, name)


def _extract_from_storage(file_name: str) -> str:
    if not file_name or not default_storage.exists(file_name):
        return ""
    with default_storage.open(file_name, "rb") as f:
        raw_bytes = f.read()
    if not raw_bytes:
        return ""
    return _extract_from_bytes(raw_bytes, file_name)


def tokenize(text: str) -> set[str]:
    cleaned = (text or "").lower().replace("c++", "cplusplus").replace("c#", "csharp")
    raw_tokens = re.findall(r"[a-z0-9.+#-]{2,}", cleaned)
    result = set()
    for raw in raw_tokens:
        token = raw.strip(".-")
        if len(token) >= 2 and token not in STOP_WORDS:
            result.add(token)
    return result


def score_resume_against_jd(resume_text: str, jd_text: str) -> dict:
    clean_resume = resume_text or ""
    jd_keywords = tokenize(jd_text or "")
    resume_tokens = tokenize(clean_resume)

    if not jd_keywords:
        return {
            "score": 0.0,
            "matched_keywords": [],
            "missing_keywords": [],
            "char_count": len(clean_resume.strip()),
        }

    matched = sorted(jd_keywords.intersection(resume_tokens))
    missing = sorted(jd_keywords - resume_tokens)
    score = round((len(matched) / len(jd_keywords)) * 100, 1)

    return {
        "score": score,
        "matched_keywords": matched[:20],
        "missing_keywords": missing[:15],
        "char_count": len(clean_resume.strip()),
    }


def match_saved_resumes_against_jd(jd_text: str, min_score: float = 0.0) -> list[dict]:
    """
    CandidateProfile aur Application mein saved sabhi resumes ko JD ke against
    score aur filter karta hai.
    """
    from .models import Application, CandidateProfile

    matched_candidates = []
    seen_keys = set()

    # 1. CandidateProfile records check karein
    profiles = CandidateProfile.objects.exclude(resume="").exclude(resume__isnull=True)
    for profile in profiles:
        if not profile.resume:
            continue
        try:
            cached_text = (getattr(profile, "resume_text", "") or "").strip()
            resume_text = cached_text or _extract_from_storage(profile.resume.name)
            if not resume_text.strip():
                continue

            combined_text = f"{profile.skills} {profile.qualification}\n{resume_text}"
            analysis = score_resume_against_jd(combined_text, jd_text)

            if analysis["score"] >= min_score:
                key = f"profile-{profile.id}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    matched_candidates.append({
                        "source": "Candidate Profile",
                        "candidate_name": profile.full_name,
                        "email": profile.email,
                        "phone": profile.phone,
                        "filename": profile.resume.name.split("/")[-1],
                        "file_url": profile.resume.url,
                        "score": analysis["score"],
                        "matched_keywords": analysis["matched_keywords"],
                        "missing_keywords": analysis["missing_keywords"],
                    })
        except Exception:
            continue

    # 2. Job Application records check karein
    applications = (
        Application.objects.select_related("candidate", "job")
        .exclude(resume="")
        .exclude(resume__isnull=True)
    )
    for app in applications:
        if not app.resume:
            continue
        try:
            resume_text = _extract_from_storage(app.resume.name)
            if not resume_text.strip():
                continue

            analysis = score_resume_against_jd(resume_text, jd_text)

            if analysis["score"] >= min_score:
                key = f"app-{app.id}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidate_display = (
                        getattr(app.candidate, "full_name", None)
                        or getattr(app.candidate, "username", None)
                        or app.candidate.email
                    )
                    matched_candidates.append({
                        "source": f"Applied: {app.job.title}",
                        "candidate_name": candidate_display,
                        "email": app.candidate.email,
                        "phone": getattr(app.candidate, "phone", "-") or "-",
                        "filename": app.resume.name.split("/")[-1],
                        "file_url": app.resume.url,
                        "score": analysis["score"],
                        "matched_keywords": analysis["matched_keywords"],
                        "missing_keywords": analysis["missing_keywords"],
                    })
        except Exception:
            continue

    matched_candidates.sort(key=lambda item: item["score"], reverse=True)
    return matched_candidates