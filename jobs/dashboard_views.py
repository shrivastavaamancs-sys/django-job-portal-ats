from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .matcher import extract_text_from_file, score_resume_against_jd, tokenize
from .models import CandidateProfile, JobDescription, validate_resume_file


def _parse_non_negative_float(raw_value: str, field_label: str, errors: list[str], default: float = 0.0) -> float:
    cleaned = (raw_value or "").strip()
    if not cleaned:
        return default
    try:
        val = float(cleaned)
        if val < 0:
            errors.append(f"{field_label} negative nahi ho sakta.")
            return default
        return val
    except ValueError:
        errors.append(f"{field_label} valid number mein dalein (jaise 0, 1.5, 3).")
        return default


def _validate_and_extract_resume(resume_file, errors: list[str]) -> str:
    if not resume_file:
        return ""
    try:
        validate_resume_file(resume_file)
        resume_file.seek(0)
        text = extract_text_from_file(resume_file)
        resume_file.seek(0)
        return text or ""
    except ValidationError as exc:
        errors.extend(exc.messages)
    except Exception as exc:
        errors.append(f"Resume parse error: {exc}")
    return ""


def jd_fill_view(request):
    """Page 1: Job Description create aur list karne ka page."""
    errors = []
    success_message = ""
    saved_jds = JobDescription.objects.all()

    form_data = {
        "title": "",
        "company_name": "",
        "min_experience": "0",
        "required_skills": "",
        "description": "",
    }

    if request.method == "POST":
        form_data = {
            "title": request.POST.get("title", "").strip(),
            "company_name": request.POST.get("company_name", "").strip(),
            "min_experience": request.POST.get("min_experience", "0").strip(),
            "required_skills": request.POST.get("required_skills", "").strip(),
            "description": request.POST.get("description", "").strip(),
        }

        if not form_data["title"]:
            errors.append("Job Title zaroori hai.")
        if not form_data["description"]:
            errors.append("Job Description (JD) enter karein.")

        min_exp = _parse_non_negative_float(form_data["min_experience"], "Minimum experience", errors, default=0.0)

        if not errors:
            jd_obj = JobDescription.objects.create(
                title=form_data["title"],
                company_name=form_data["company_name"],
                min_experience=min_exp,
                required_skills=form_data["required_skills"],
                description=form_data["description"],
            )
            success_message = f"JD '{jd_obj.title}' save ho gayi hai."
            saved_jds = JobDescription.objects.all()
            form_data = {
                "title": "",
                "company_name": "",
                "min_experience": "0",
                "required_skills": "",
                "description": "",
            }

    return render(
        request,
        "jobs/jd_form.html",
        {
            "form_data": form_data,
            "errors": errors,
            "success_message": success_message,
            "saved_jds": saved_jds,
            "active_page": "jd",
        },
    )


def jd_edit_view(request, pk):
    """Job Description Update (Edit) view."""
    jd_obj = get_object_or_404(JobDescription, pk=pk)
    errors = []

    form_data = {
        "title": jd_obj.title,
        "company_name": jd_obj.company_name,
        "min_experience": str(jd_obj.min_experience),
        "required_skills": jd_obj.required_skills,
        "description": jd_obj.description,
    }

    if request.method == "POST":
        form_data = {
            "title": request.POST.get("title", "").strip(),
            "company_name": request.POST.get("company_name", "").strip(),
            "min_experience": request.POST.get("min_experience", "0").strip(),
            "required_skills": request.POST.get("required_skills", "").strip(),
            "description": request.POST.get("description", "").strip(),
        }

        if not form_data["title"]:
            errors.append("Job Title zaroori hai.")
        if not form_data["description"]:
            errors.append("Job Description (JD) enter karein.")

        min_exp = _parse_non_negative_float(form_data["min_experience"], "Minimum experience", errors, default=0.0)

        if not errors:
            jd_obj.title = form_data["title"]
            jd_obj.company_name = form_data["company_name"]
            jd_obj.min_experience = min_exp
            jd_obj.required_skills = form_data["required_skills"]
            jd_obj.description = form_data["description"]
            jd_obj.save()
            return redirect("jd-form")

    return render(
        request,
        "jobs/jd_edit.html",
        {
            "jd_obj": jd_obj,
            "form_data": form_data,
            "errors": errors,
            "active_page": "jd",
        },
    )


def jd_delete_view(request, pk):
    """Job Description Delete view."""
    jd_obj = get_object_or_404(JobDescription, pk=pk)
    if request.method == "POST":
        jd_obj.delete()
        return redirect("jd-form")
    return render(
        request,
        "jobs/confirm_delete.html",
        {
            "object_title": f"Job Description: {jd_obj.title}",
            "cancel_url": "/jd/",
            "active_page": "jd",
        },
    )


def candidate_upload_view(request):
    """Page 2: Candidate create aur list page."""
    errors = []
    success_message = ""
    recent_candidates = CandidateProfile.objects.all()

    form_data = {
        "name": "",
        "email": "",
        "phone": "",
        "skills": "",
        "experience": "",
        "qualification": "",
    }

    if request.method == "POST":
        form_data = {
            "name": request.POST.get("name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "skills": request.POST.get("skills", "").strip(),
            "experience": request.POST.get("experience", "").strip(),
            "qualification": request.POST.get("qualification", "").strip(),
        }

        if not form_data["name"]:
            errors.append("Candidate ka Name zaroori hai.")
        if not form_data["email"]:
            errors.append("Candidate ka Email zaroori hai.")
        if not form_data["phone"]:
            errors.append("Contact Number zaroori hai.")
        if not form_data["skills"]:
            errors.append("Skills enter karein.")
        if not form_data["qualification"]:
            errors.append("Qualification enter karein.")

        exp_val = _parse_non_negative_float(form_data["experience"], "Experience", errors, default=0.0)

        resume_file = request.FILES.get("resume")
        extracted_text = _validate_and_extract_resume(resume_file, errors)

        if not errors:
            create_kwargs = {
                "full_name": form_data["name"],
                "email": form_data["email"],
                "phone": form_data["phone"],
                "qualification": form_data["qualification"],
                "experience_years": exp_val,
                "skills": form_data["skills"],
                "resume": resume_file,
            }
            if hasattr(CandidateProfile, "resume_text"):
                create_kwargs["resume_text"] = extracted_text

            candidate = CandidateProfile.objects.create(**create_kwargs)
            success_message = f"{candidate.full_name} ki profile aur resume save ho gaye hain."
            recent_candidates = CandidateProfile.objects.all()
            form_data = {k: "" for k in form_data}

    return render(
        request,
        "jobs/candidate_upload.html",
        {
            "form_data": form_data,
            "errors": errors,
            "success_message": success_message,
            "recent_candidates": recent_candidates,
            "active_page": "upload",
        },
    )


def candidate_edit_view(request, pk):
    """Candidate Profile Update (Edit) view."""
    candidate = get_object_or_404(CandidateProfile, pk=pk)
    errors = []

    form_data = {
        "name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.skills,
        "experience": str(candidate.experience_years),
        "qualification": candidate.qualification,
    }

    if request.method == "POST":
        form_data = {
            "name": request.POST.get("name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "skills": request.POST.get("skills", "").strip(),
            "experience": request.POST.get("experience", "").strip(),
            "qualification": request.POST.get("qualification", "").strip(),
        }

        if not form_data["name"]:
            errors.append("Candidate ka Name zaroori hai.")
        if not form_data["email"]:
            errors.append("Candidate ka Email zaroori hai.")
        if not form_data["phone"]:
            errors.append("Contact Number zaroori hai.")
        if not form_data["skills"]:
            errors.append("Skills enter karein.")
        if not form_data["qualification"]:
            errors.append("Qualification enter karein.")

        exp_val = _parse_non_negative_float(form_data["experience"], "Experience", errors, default=0.0)

        resume_file = request.FILES.get("resume")
        extracted_text = _validate_and_extract_resume(resume_file, errors) if resume_file else ""

        if not errors:
            candidate.full_name = form_data["name"]
            candidate.email = form_data["email"]
            candidate.phone = form_data["phone"]
            candidate.skills = form_data["skills"]
            candidate.experience_years = exp_val
            candidate.qualification = form_data["qualification"]
            if resume_file:
                if candidate.resume:
                    candidate.resume.delete(save=False)
                candidate.resume = resume_file
                if hasattr(candidate, "resume_text"):
                    candidate.resume_text = extracted_text
            candidate.save()
            return redirect("candidate-upload")

    return render(
        request,
        "jobs/candidate_edit.html",
        {
            "candidate": candidate,
            "form_data": form_data,
            "errors": errors,
            "active_page": "upload",
        },
    )


def candidate_delete_view(request, pk):
    """Candidate Profile Delete view."""
    candidate = get_object_or_404(CandidateProfile, pk=pk)
    if request.method == "POST":
        if candidate.resume:
            candidate.resume.delete(save=False)
        candidate.delete()
        return redirect("candidate-upload")
    return render(
        request,
        "jobs/confirm_delete.html",
        {
            "object_title": f"Candidate: {candidate.full_name} ({candidate.email})",
            "cancel_url": "/upload-resume/",
            "active_page": "upload",
        },
    )


def result_filter_view(request):
    """Page 3: Skills aur experience ke base par candidates filter/rank karne ka page."""
    jds = JobDescription.objects.all()
    selected_jd_id = request.GET.get("jd_id", "") or request.POST.get("jd_id", "")

    skills_query = (
        request.GET.get("skills", "").strip()
        if request.method == "GET"
        else request.POST.get("skills", "").strip()
    )
    min_exp_raw = (
        request.GET.get("min_experience", "0").strip()
        if request.method == "GET"
        else request.POST.get("min_experience", "0").strip()
    )

    try:
        min_exp = float(min_exp_raw) if min_exp_raw != "" else 0.0
        if min_exp < 0:
            min_exp = 0.0
    except ValueError:
        min_exp = 0.0

    selected_jd = jds.filter(id=selected_jd_id).first() if selected_jd_id else None
    effective_skill_source = skills_query
    if not effective_skill_source and selected_jd:
        effective_skill_source = selected_jd.required_skills or selected_jd.description
        if min_exp == 0.0 and selected_jd.min_experience:
            min_exp = float(selected_jd.min_experience)

    required_tokens = tokenize(effective_skill_source)
    candidates = CandidateProfile.objects.filter(experience_years__gte=min_exp)

    filtered_results = []
    for cand in candidates:
        cand_text = f"{cand.skills} {cand.qualification}"
        cached_text = getattr(cand, "resume_text", "") or ""
        if cached_text.strip():
            cand_text = f"{cand_text}\n{cached_text}"
        elif cand.resume:
            try:
                with cand.resume.open("rb") as f:
                    parsed_resume = extract_text_from_file(f)
                if parsed_resume and parsed_resume.strip():
                    cand_text = f"{cand_text}\n{parsed_resume}"
            except Exception:
                pass

        if required_tokens:
            analysis = score_resume_against_jd(cand_text, effective_skill_source)
            matched = analysis["matched_keywords"]
            missing = analysis["missing_keywords"]
            score = analysis["score"]
            if not matched:
                continue
        else:
            cand_tokens = sorted(tokenize(cand.skills))
            matched = cand_tokens
            missing = []
            score = 100.0 if cand_tokens else 0.0

        filtered_results.append(
            {
                "candidate": cand,
                "score": score,
                "matched_keywords": matched,
                "missing_keywords": missing,
                "resume_url": cand.resume.url if cand.resume else "",
                "resume_name": cand.resume.name.split("/")[-1] if cand.resume else "No Resume",
            }
        )

    filtered_results.sort(
        key=lambda item: (item["score"], float(item["candidate"].experience_years)),
        reverse=True,
    )

    return render(
        request,
        "jobs/result_filter.html",
        {
            "jds": jds,
            "selected_jd_id": str(selected_jd_id),
            "skills_query": skills_query,
            "min_experience": min_exp,
            "results": filtered_results,
            "active_page": "filter",
        },
    )


def home_redirect_view(request):
    return redirect("result-filter")