import json
import re

from openai import OpenAI


class AIService:
    """Use the local Ollama model, with labeled fallbacks."""

    OLLAMA_BASE_URL = "http://localhost:11434/v1"
    OLLAMA_MODEL = "qwen2.5:1.5b"

    @staticmethod
    def _ask_ollama_json(prompt, system_message):
        """Ask Ollama for JSON and return the parsed object."""
        client = OpenAI(
            base_url=AIService.OLLAMA_BASE_URL,
            api_key="ollama",
            timeout=120.0,
            max_retries=0
        )

        response = client.chat.completions.create(
            model=AIService.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600
        )

        text = response.choices[0].message.content or ""
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ValueError("Ollama did not return a JSON object")

        result = json.loads(match.group())

        if not isinstance(result, dict):
            raise ValueError("Ollama response was not a JSON object")

        return result

    @staticmethod
    def analyze_crime(crime_type, description):
        """Analyze a complaint with Ollama; use rules if Ollama fails."""
        prompt = f"""
Analyze this cybercrime report as a preliminary assessment.

Crime type: {crime_type}
Description: {description}

Return only JSON with:
- crime_category: string
- severity_score: Critical, High, Medium, or Low
- confidence_score: integer from 0 to 100
- suggested_actions: list of 4 or 5 short actions
- estimated_resolution_time: a cautious estimate, not a guarantee

Do not claim that the crime is verified or predict the real outcome.
"""

        try:
            analysis = AIService._ask_ollama_json(
                prompt,
                "Analyze cybercrime reports carefully. Return valid JSON only. "
                "Do not claim to verify crimes or predict real-world outcomes."
            )

            required = (
                "crime_category",
                "severity_score",
                "confidence_score",
                "suggested_actions",
                "estimated_resolution_time"
            )
            if any(field not in analysis for field in required):
                raise ValueError("Ollama response is missing required fields")

            try:
                analysis["confidence_score"] = max(
                    0, min(100, int(analysis["confidence_score"]))
                )
            except (TypeError, ValueError):
                analysis["confidence_score"] = 0

            if not isinstance(analysis["suggested_actions"], list):
                raise ValueError("suggested_actions must be a list")

            analysis["analysis_source"] = "Ollama local model"
            return analysis

        except Exception as error:
            print(f"Ollama report analysis failed; using rules: {error}")
            fallback = AIService.get_fallback_analysis(
                crime_type,
                description
            )
            fallback["analysis_source"] = (
                "Rule-based fallback — Ollama unavailable"
            )
            return fallback

    @staticmethod
    def get_fallback_analysis(crime_type, description):
        """Provide a rule-based result when Ollama is unavailable."""
        crime_type = crime_type or "Unknown"
        description = description or ""
        crime_lower = crime_type.lower()

        severity_map = {
            "phishing": "Medium",
            "identity theft": "High",
            "online fraud": "High",
            "ransomware": "Critical",
            "data breach": "High",
            "cyber bullying": "Medium",
            "credit card fraud": "High"
        }

        severity = "Medium"
        for keyword, mapped_severity in severity_map.items():
            if keyword in crime_lower:
                severity = mapped_severity
                break

        urgent_words = [
            "urgent", "emergency", "financial loss",
            "bank", "money", "stolen"
        ]
        description_lower = description.lower()

        if any(word in description_lower for word in urgent_words):
            if severity == "Medium":
                severity = "High"
            elif severity == "High":
                severity = "Critical"

        actions = [
            "Preserve digital evidence, such as screenshots, emails, and logs",
            "Change passwords for affected accounts",
            "Contact your bank if financial information may be compromised",
            "Report the incident to the appropriate cybercrime authority",
            "Monitor affected accounts for suspicious activity"
        ]

        if "phishing" in crime_lower:
            actions.insert(
                0,
                "Do not click suspicious links or open unexpected attachments"
            )
        elif "ransomware" in crime_lower:
            actions.insert(
                0,
                "Disconnect the affected device from the network"
            )

        if severity == "Critical":
            resolution = "3-5 business days (illustrative estimate)"
        elif severity == "High":
            resolution = "7-10 business days (illustrative estimate)"
        else:
            resolution = "10-15 business days (illustrative estimate)"

        return {
            "crime_category": crime_type,
            "severity_score": severity,
            "confidence_score": 75,
            "suggested_actions": actions[:5],
            "estimated_resolution_time": resolution,
            "analysis_source": "Rule-based fallback"
        }

    @staticmethod
    def get_safety_tips(crime_type, description=""):
        """Generate safety tips for the selected crime type."""
        prompt = f"""
Give 4 short, practical safety tips for this reported cybercrime.

Crime type: {crime_type}
Report description: {description}

Return JSON with one field:
- tips: a list of 4 short strings

Do not claim the incident is verified. Do not promise that the tips will
recover money or prevent all harm.
"""

        try:
            result = AIService._ask_ollama_json(
                prompt,
                "Give clear, cautious cyber-safety guidance. Return valid JSON only."
            )

            tips = result.get("tips")
            if not isinstance(tips, list) or not tips:
                raise ValueError("Ollama did not return a tips list")

            return {
                "tips": [str(tip) for tip in tips[:5]],
                "analysis_source": "Ollama local model"
            }

        except Exception as error:
            print(f"Ollama safety tips failed; using rules: {error}")
            fallback = AIService.get_fallback_analysis(
                crime_type,
                description
            )
            return {
                "tips": fallback["suggested_actions"],
                "analysis_source": (
                    "Rule-based fallback — Ollama unavailable"
                )
            }

    @staticmethod
    def get_complaint_insights(complaint):
        """Generate insights for an existing complaint."""
        crime_type = complaint.get("crime_type", "Unknown")
        description = complaint.get("description", "")
        priority = complaint.get("priority", "unknown")
        status = complaint.get("status", "unknown")

        prompt = f"""
Summarize this complaint for the user in simple language.

Crime type: {crime_type}
Description: {description}
Priority recorded by the system: {priority}
Current status: {status}

Return JSON with:
- summary: one short sentence
- risk_factors: list of short strings
- recommendations: list of short strings
- estimated_timeline: short status explanation

Do not claim that the crime is verified or that you know the investigation result.
"""

        try:
            insights = AIService._ask_ollama_json(
                prompt,
                "Give cautious, clear complaint insights. Return valid JSON only."
            )
            insights["analysis_source"] = "Ollama local model"
            return insights

        except Exception as error:
            print(f"Ollama complaint insights failed; using rules: {error}")

            risks = []
            recommendations = []

            if priority in ["high", "critical"]:
                risks.append("The system marks this complaint as high priority.")

            if "financial" in description.lower():
                risks.append("The description mentions possible financial impact.")

            if status == "pending":
                recommendations.append("The complaint is awaiting initial review.")
            elif status == "under_review":
                recommendations.append("The complaint is currently under review.")
            elif status == "investigating":
                recommendations.append("An investigation is in progress.")

            return {
                "summary": f"This is a {priority} priority {crime_type} complaint.",
                "risk_factors": risks,
                "recommendations": recommendations,
                "estimated_timeline": "Check the complaint status for updates.",
                "analysis_source": "Rule-based fallback — Ollama unavailable"
            }

    @staticmethod
    def analyze_trends(trends_data):
        """Summarize historical complaint counts; this is not forecasting."""
        if not trends_data:
            return {
                "overall_trend": "Not enough data",
                "most_common_crime": "Not enough data",
                "monthly_data": {"labels": [], "values": []}
            }

        crime_counts = {}
        monthly_counts = {}

        for item in trends_data:
            crime_type = item.get("crime_type", "Unknown")
            count = int(item.get("count", 1) or 0)
            month = item.get("month", "Unknown")

            crime_counts[crime_type] = crime_counts.get(crime_type, 0) + count
            monthly_counts[month] = monthly_counts.get(month, 0) + count

        most_common = (
            max(crime_counts.items(), key=lambda item: item[1])[0]
            if crime_counts else "Unknown"
        )

        months = sorted(monthly_counts)
        trend = "Stable"

        if len(months) >= 2:
            midpoint = len(months) // 2
            first_half = sum(monthly_counts[m] for m in months[:midpoint])
            second_half = sum(monthly_counts[m] for m in months[midpoint:])

            if second_half > first_half:
                trend = "Increasing"
            elif second_half < first_half:
                trend = "Decreasing"

        return {
            "overall_trend": trend,
            "most_common_crime": most_common,
            "monthly_data": {
                "labels": months,
                "values": [monthly_counts[m] for m in months]
            }
        }

    @staticmethod
    def get_predictions(trends_data=None):
        """
        Generate a changing summary of observed complaint trends.
        This is not a validated future-crime forecast.
        """
        trends_data = trends_data or []
        observed = AIService.analyze_trends(trends_data)

        prompt = f"""
Summarize these observed complaint statistics for a dashboard.

Statistics: {json.dumps(observed)}

Return JSON with:
- high_risk_areas: short summary based only on these statistics
- expected_increase: explain the observed direction; do not invent percentages
- recommendation: one practical recommendation
- emerging_threats: list of up to 3 cautious observations

If there is too little data, say so. Do not present this as a validated
prediction of future crimes.
"""

        try:
            result = AIService._ask_ollama_json(
                prompt,
                "Summarize the supplied data only. Never invent counts or "
                "percentages. Return valid JSON only."
            )

            result["analysis_source"] = "Ollama local model"
            result["is_simulated"] = True
            result["notice"] = (
                "AI-generated summary of observed complaint data, "
                "not a validated future forecast."
            )
            return result

        except Exception as error:
            print(f"Ollama dashboard summary failed; using data summary: {error}")

            return {
                "high_risk_areas": observed["most_common_crime"],
                "expected_increase": (
                    f"Observed historical trend: {observed['overall_trend']}. "
                    "This is not a future forecast."
                ),
                "recommendation": (
                    "Use the observed complaint counts as a guide and seek "
                    "expert review."
                ),
                "emerging_threats": (
                    [observed["most_common_crime"]]
                    if observed["most_common_crime"] != "Not enough data"
                    else []
                ),
                "analysis_source": "Database trend summary",
                "is_simulated": True,
                "notice": (
                    "This summarizes observed data; it is not a validated "
                    "future forecast."
                )
            }