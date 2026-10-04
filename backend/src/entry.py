from workers import Response, WorkerEntrypoint
import json
import re


def json_response(data, status=200, headers=None):
    base_headers = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
    if headers:
        base_headers.update(headers)
    return Response.json(data, status=status, headers=base_headers)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        origin = request.headers.get("Origin", "")
        allowed_origin = getattr(self.env, "ALLOWED_ORIGIN", "")
        cors = {"Vary": "Origin"}
        if allowed_origin and origin == allowed_origin:
            cors["Access-Control-Allow-Origin"] = allowed_origin
            cors["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            cors["Access-Control-Allow-Headers"] = "Content-Type"
            cors["Access-Control-Max-Age"] = "86400"

        method = request.method.upper()
        path = request.url.split("?", 1)[0].rstrip("/") or "/"

        if method == "OPTIONS":
            if not allowed_origin or origin != allowed_origin:
                return json_response({"error": "Origin not allowed"}, status=403, headers=cors)
            return Response.new("", status=204, headers=cors)

        if path == "/api/health" and method == "GET":
            try:
                await self.env.DB.prepare("SELECT 1 AS ok").first()
                return json_response({"ok": True, "database": "connected"}, headers=cors)
            except Exception:
                return json_response({"ok": False, "error": "Database is not available"}, status=500, headers=cors)

        if path == "/api/contact" and method == "POST":
            if not allowed_origin or origin != allowed_origin:
                return json_response({"error": "Origin not allowed"}, status=403, headers=cors)
            try:
                payload = await request.json()
            except Exception:
                return json_response({"error": "Invalid JSON body"}, status=400, headers=cors)

            if not isinstance(payload, dict):
                return json_response({"error": "Invalid form submission"}, status=400, headers=cors)
            # Honeypot field: bots often fill hidden fields. Return a generic success.
            if str(payload.get("website", "")).strip():
                return json_response({"ok": True, "message": "Enquiry received"}, headers=cors)

            name = str(payload.get("name", "")).strip()
            email = str(payload.get("email", "")).strip().lower()
            phone = str(payload.get("phone", "")).strip()
            enquiry_type = str(payload.get("enquiry_type", "")).strip()
            subject = str(payload.get("subject", "")).strip()
            message = str(payload.get("message", "")).strip()

            if not name or len(name) > 100:
                return json_response({"error": "Enter a name of up to 100 characters."}, status=400, headers=cors)
            if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                return json_response({"error": "Enter a valid email address."}, status=400, headers=cors)
            if len(phone) > 30:
                return json_response({"error": "Phone number is too long."}, status=400, headers=cors)
            if enquiry_type not in ("Candidate", "Employer", "Other"):
                return json_response({"error": "Select Candidate, Employer or Other."}, status=400, headers=cors)
            if not subject or len(subject) > 160:
                return json_response({"error": "Enter a subject of up to 160 characters."}, status=400, headers=cors)
            if len(message) < 10 or len(message) > 4000:
                return json_response({"error": "Message must be between 10 and 4000 characters."}, status=400, headers=cors)

            try:
                await self.env.DB.prepare(
                    "INSERT INTO enquiries (name, email, phone, enquiry_type, subject, message, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))"
                ).bind(name, email, phone, enquiry_type, subject, message).run()
                return json_response({"ok": True, "message": "Thank you. Your enquiry has been received."}, status=201, headers=cors)
            except Exception:
                return json_response({"error": "We could not save your enquiry. Please try again later."}, status=500, headers=cors)

        if path.startswith("/api/"):
            return json_response({"error": "Not found"}, status=404, headers=cors)
        return json_response({"service": "Active Hire Solutions Test API", "endpoints": ["GET /api/health", "POST /api/contact"]}, headers=cors)
