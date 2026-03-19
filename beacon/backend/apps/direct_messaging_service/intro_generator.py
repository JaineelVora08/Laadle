import json
from google import genai
from google.genai import types
from django.conf import settings


class IntroMessageGenerator:
    """
    Generates an LLM-powered introductory message from a student to a senior mentor.
    Uses Gemini 2.0 Flash.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate(self, student, query=None, domain_name: str = "") -> str:
        """
        Builds context from student profile + optional query and asks Gemini to write
        a polite introductory message.

        Args:
            student: auth_service.User instance (student)
            query:   query_orchestrator.Query instance (optional — None for mentor search connects)
            domain_name: human-readable domain name (optional)

        Returns:
            str — the generated intro message
        """
        # Gather student profile fields safely
        bio = ""
        domains = []
        try:
            profile = student.extended_profile
            bio = profile.bio or ""
            domains = profile.domains_of_interest or []
        except Exception:
            pass

        domains_str = ", ".join(domains) if domains else "not specified"

        # Build query context if available
        if query:
            query_context = f"""QUERY CONTEXT:
- Domain: {domain_name or "not specified"}
- Question: {query.content}"""
        else:
            query_context = f"""CONNECTION CONTEXT:
- Domain of interest: {domain_name or "not specified"}
- The student found this senior in mentor search and wants to connect for guidance."""

        prompt = f"""You are BEACON, a mentorship platform assistant. Write a brief, polite introductory
message from a student to a senior mentor. The message should introduce the student,
mention their background and what they are working on, and explain why they want to connect.
Keep it under 120 words and maintain a professional yet friendly tone.

STUDENT INFORMATION:
- Name: {student.name}
- Current Level: {student.current_level or "not specified"}
- Bio: {bio or "not provided"}
- Domains of Interest: {domains_str}

{query_context}

Respond with ONLY the introductory message text — no JSON, no labels, just the message."""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=200,
                ),
            )
            return response.text.strip()
        except Exception as exc:
            # Fallback: plain text intro if LLM fails
            return (
                f"Hi, I'm {student.name} (level: {student.current_level or 'N/A'}). "
                f"I'm interested in {domain_name or 'connecting with you'} "
                f"and would love to learn from your experience. Looking forward to connecting!"
            )
