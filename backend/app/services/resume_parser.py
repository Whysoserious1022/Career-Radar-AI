import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.skill_extractor import extract_skills_from_text

class ResumeParser:
    """
    Production-grade resume document parser supporting PDF, DOCX, and TXT formats.
    Extracts structured sections, contacts, education, timeline, and technical skills.
    """

    @classmethod
    def extract_text_from_file(cls, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == ".txt":
            return cls._read_txt(file_path)
        elif ext == ".docx":
            return cls._read_docx(file_path)
        elif ext == ".pdf":
            return cls._read_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: .pdf, .docx, .txt")

    @classmethod
    def _read_txt(cls, file_path: str) -> str:
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")

    @classmethod
    def _read_docx(cls, file_path: str) -> str:
        """
        Extracts text from DOCX using zipfile and xml parsing from python standard library,
        ensuring zero external binary dependencies.
        """
        try:
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                # Word document text tags are in namespace http://schemas.openxmlformats.org/wordprocessingml/2006/main
                namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for p in tree.iterfind(".//w:p", namespaces):
                    texts = [node.text for node in p.iterfind(".//w:t", namespaces) if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return "\n".join(paragraphs)
        except Exception as e:
            # Fallback text reading
            with open(file_path, "rb") as f:
                raw = f.read()
                # Extract ASCII/printable strings
                matches = re.findall(rb"[\x20-\x7E\t\n\r]{4,}", raw)
                return "\n".join(m.decode("ascii", errors="ignore") for m in matches)

    @classmethod
    def _read_pdf(cls, file_path: str) -> str:
        """
        Reads PDF text. Tries pypdf if installed; otherwise utilizes pure Python stream parser.
        """
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            if pages_text:
                return "\n".join(pages_text)
        except ImportError:
            pass
        except Exception:
            pass

        # Robust Standard-Library Fallback: Parse text blocks from uncompressed / standard PDF streams
        text_lines = []
        with open(file_path, "rb") as f:
            content = f.read()
            # Match BT ... ET blocks or string objects ( ... )
            stream_matches = re.findall(rb"stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
            import zlib
            for sm in stream_matches:
                try:
                    decompressed = zlib.decompress(sm)
                    # Find text in parenthesis inside Tj or TJ commands
                    tj_matches = re.findall(rb"\((.*?)\)\s*T[jJ]", decompressed)
                    for tm in tj_matches:
                        text_lines.append(tm.decode("utf-8", errors="ignore"))
                except Exception:
                    pass
        if text_lines:
            return " ".join(text_lines)
        
        # Last-resort printable sequence extraction
        matches = re.findall(rb"[\x20-\x7E\t\n\r]{4,}", content)
        return "\n".join(m.decode("ascii", errors="ignore") for m in matches)

    @classmethod
    def parse_resume(cls, file_path: str) -> Dict[str, Any]:
        """
        Executes full structured parsing pipeline on resume.
        """
        raw_text = cls.extract_text_from_file(file_path)
        
        # Extract Contact
        contact = cls._extract_contact(raw_text)
        
        # Extract Skills
        skills, categorized_skills = extract_skills_from_text(raw_text)
        
        # Extract Education
        education = cls._extract_education(raw_text)
        
        # Extract Experience & Years
        experience, years_of_exp = cls._extract_experience(raw_text)
        
        # Extract Projects
        projects = cls._extract_projects(raw_text)
        
        # Extract Certifications
        certifications = cls._extract_certifications(raw_text)

        # Estimate confidence
        confidence = 0.5
        if contact.get("email"):
            confidence += 0.15
        if skills:
            confidence += 0.15
        if education:
            confidence += 0.1
        if experience:
            confidence += 0.1
        confidence = min(1.0, confidence)

        return {
            "contact": contact,
            "skills": skills,
            "categorized_skills": categorized_skills,
            "experience_years": years_of_exp,
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "parsed_confidence": round(confidence, 2)
        }

    @classmethod
    def _extract_contact(cls, text: str) -> Dict[str, Any]:
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+", text, re.IGNORECASE)

        return {
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "linkedin": linkedin_match.group(0) if linkedin_match else None,
            "github": github_match.group(0) if github_match else None,
        }

    @classmethod
    def _extract_education(cls, text: str) -> List[Dict[str, Any]]:
        education = []
        edu_keywords = ["Bachelor", "Master", "B.Tech", "B.E.", "M.Tech", "M.S.", "Ph.D.", "B.S.", "Computer Science", "Information Technology"]
        year_matches = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
        
        lines = text.split("\n")
        for i, line in enumerate(lines):
            for kw in edu_keywords:
                if kw.lower() in line.lower():
                    # Look for degree and year
                    years_in_line = re.findall(r"\b(20\d{2}|19\d{2})\b", line)
                    grad_year = int(years_in_line[-1]) if years_in_line else None
                    if not grad_year and i + 1 < len(lines):
                        next_years = re.findall(r"\b(20\d{2}|19\d{2})\b", lines[i+1])
                        if next_years:
                            grad_year = int(next_years[-1])
                    
                    education.append({
                        "degree": line.strip()[:100],
                        "graduation_year": grad_year,
                        "text": line.strip()
                    })
                    break
        return education[:3]

    @classmethod
    def _extract_experience(cls, text: str) -> (List[Dict[str, Any]], float):
        experience = []
        # Find year ranges like 2020 - 2023, 2021 - Present, Jan 2021 to Present
        date_pattern = r"\b(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(20\d{2}|Present|Current|Now)\b"
        matches = list(re.finditer(date_pattern, text, re.IGNORECASE))
        
        total_months = 0
        current_year = datetime.now().year

        for match in matches:
            start_yr = int(match.group(1))
            end_val = match.group(2).lower()
            if end_val in ["present", "current", "now"]:
                end_yr = current_year
            else:
                end_yr = int(end_val)
            
            diff_years = max(0, end_yr - start_yr)
            total_months += diff_years * 12
            
            # Find context line
            start_pos = max(0, match.start() - 100)
            end_pos = min(len(text), match.end() + 100)
            snippet = text[start_pos:end_pos].replace("\n", " ").strip()
            
            experience.append({
                "duration": f"{start_yr} - {match.group(2)}",
                "years": diff_years,
                "context": snippet[:200]
            })

        calculated_years = round(total_months / 12.0, 1) if total_months > 0 else 0.0
        return experience, calculated_years

    @classmethod
    def _extract_projects(cls, text: str) -> List[Dict[str, Any]]:
        projects = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        in_project_section = False
        
        for i, line in enumerate(lines):
            if re.search(r"^(?:personal\s+)?projects?\b", line, re.IGNORECASE):
                in_project_section = True
                continue
            if in_project_section:
                if re.search(r"^(?:education|experience|skills|certifications|awards)\b", line, re.IGNORECASE):
                    break
                if len(line) > 10 and not line.startswith("http"):
                    # Check if line looks like a project header
                    projects.append({
                        "name": line[:80],
                        "description": lines[i+1][:200] if i + 1 < len(lines) else ""
                    })
                    if len(projects) >= 5:
                        break
        return projects

    @classmethod
    def _extract_certifications(cls, text: str) -> List[str]:
        certs = []
        cert_kws = ["AWS Certified", "CKA", "Azure Certified", "GCP Professional", "Coursera", "DeepLearning.AI", "Scrum Master", "PMP"]
        for kw in cert_kws:
            if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
                certs.append(kw)
        return certs
