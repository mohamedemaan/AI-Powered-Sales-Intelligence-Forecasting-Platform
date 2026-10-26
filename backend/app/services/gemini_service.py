import os
import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_sales_business_context(db: Session, sku: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts live sales summary from the database to ground Gemini responses in empirical data.
    """
    try:
        from app.models.data import RawSalesData
        clean_sku = (sku or "").strip()
        is_all = clean_sku.upper() in ["ALL", "GLOBAL", "TOTAL", "", "ALL PRODUCTS", "ALL SKUS"]
        
        query = db.query(RawSalesData)
        if not is_all:
            query = query.filter(RawSalesData.sku == clean_sku)

        total_records = query.count()
        if total_records == 0:
            return {
                "total_records": 0,
                "total_revenue": 0.0,
                "active_skus": 0,
                "recent_samples": "No transactions ingested yet."
            }

        total_rev_query = db.query(
            func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0)))
        )
        if not is_all:
            total_rev_query = total_rev_query.filter(RawSalesData.sku == clean_sku)
        revenue_val = float(total_rev_query.scalar() or 0.0)

        active_skus = db.query(func.count(func.distinct(RawSalesData.sku))).scalar() or 0

        # Distinct orders
        has_orders = query.filter(RawSalesData.order_id != None).first() is not None
        if has_orders:
            orders_val = query.with_entities(func.count(func.distinct(RawSalesData.order_id))).scalar() or 0
        else:
            orders_val = total_records

        # Profit & Margin
        has_profit = query.filter(RawSalesData.profit != None).first() is not None
        profit_val = float(query.with_entities(func.sum(RawSalesData.profit)).scalar() or 0.0) if has_profit else None
        margin_pct = round((profit_val / revenue_val) * 100, 2) if (profit_val is not None and revenue_val > 0) else None

        # Sample recent 5 records for ground truth
        recent_rows = query.order_by(RawSalesData.id.desc()).limit(5).all()
        samples = []
        for r in recent_rows:
            p_name = getattr(r, 'product_name', r.sku) or r.sku
            samples.append(f"Product: {p_name} (SKU: {r.sku}), Units: {r.units_sold}, Price: ${r.price or 0:.2f}, Date: {r.date}")
        recent_samples = "\n".join(samples) if samples else "N/A"

        return {
            "total_records": total_records,
            "total_revenue": revenue_val,
            "distinct_orders": orders_val,
            "total_profit": profit_val,
            "profit_margin_pct": margin_pct,
            "active_skus": active_skus,
            "recent_samples": recent_samples
        }
    except Exception as e:
        logger.warning(f"Could not load sales context from DB: {e}")
        return {
            "total_records": 0,
            "total_revenue": 0.0,
            "active_skus": 0,
            "recent_samples": "Baseline environment"
        }

def query_sales_gemini(query: str, db: Session, sku: Optional[str] = None) -> Dict[str, Any]:
    """
    Queries Google Gemini API with grounded sales metrics.
    Supports current Gemini models (gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro).
    """
    api_key = (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()

    # 1. Check if API key is missing or default placeholder
    if not api_key or "your_" in api_key.lower() or api_key == "YOUR_GEMINI_API_KEY":
        return {
            "answer": "Google Gemini API Key is not yet configured. Please paste your valid API key from Google AI Studio into 'backend/.env' (as GEMINI_API_KEY=AIzaSy...) and restart the backend.",
            "evidence": {
                "status": "Configuration Required",
                "env_variable": "GEMINI_API_KEY",
                "file_location": "backend/.env or project root .env",
                "get_key_url": "https://aistudio.google.com/app/apikey"
            },
            "recommendation": "Step 1: Go to https://aistudio.google.com/app/apikey and create a free API key (starts with 'AIzaSy'). Step 2: Open backend/.env. Step 3: Paste GEMINI_API_KEY=AIzaSy... Step 4: Restart your backend."
        }

    # 2. Key format advisory: Official Google AI Studio keys start with 'AIzaSy'
    if not api_key.startswith("AIzaSy"):
        logger.warning(f"GEMINI_API_KEY does not start with standard 'AIzaSy' prefix (starts with '{api_key[:6]}...'). Testing against Google API...")

    # 3. Fetch live business context from database
    context = get_sales_business_context(db, sku)

    prompt = f"""
You are the Enterprise Sales Intelligence AI Consultant powered by Google Gemini.
The user is asking a question about their business sales, trends, or forecasting data.

GROUNDED BUSINESS DATA CONTEXT:
- Total Transactions Ingested: {context['total_records']}
- Total Tracked Revenue: ${context['total_revenue']:,.2f}
- Distinct Orders: {context.get('distinct_orders', 'N/A')}
- Total Profit: {f"${context['total_profit']:,.2f}" if context.get('total_profit') is not None else 'N/A (Profit omitted from dataset)'}
- Operating Profit Margin: {f"{context['profit_margin_pct']}%" if context.get('profit_margin_pct') is not None else 'N/A'}
- Active SKUs in System: {context['active_skus']}
- Specific Filtered Target: {sku or 'All Products (Global Aggregate)'}
- Recent Transaction Snapshots:
{context['recent_samples']}

USER QUESTION:
"{query}"

Analyze the question carefully. Ground your response in the provided sales data context and commercial sales analytics principles.
You MUST respond STRICTLY in valid JSON matching this schema:
{{
  "answer": "<A comprehensive, professional analytical response addressing the user's question>",
  "evidence": {{
    "<Data Metric / Observation 1>": "<specific observation or statistic>",
    "<Data Metric / Observation 2>": "<specific observation or statistic>"
  }},
  "recommendation": "<Direct, actionable, high-impact business advice for sales and inventory managers>"
}}
"""

    # List of active, supported models (gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro)
    models_to_try = [
        settings.GEMINI_MODEL,
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    seen = set()
    models = [m for m in models_to_try if m and m not in ["gemini-pro", "gemini-2.5-flash"] and not (m in seen or seen.add(m))]

    last_error = None

    # 1. Attempt official google-genai SDK first
    try:
        from google import genai
        from google.genai import types
        sdk_available = True
    except ImportError:
        sdk_available = False

    if sdk_available:
        for model_name in models:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=1024,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    raw_text = response.text.strip()
                    clean_text = raw_text
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()

                    try:
                        parsed = json.loads(clean_text)
                        if isinstance(parsed, dict) and "answer" in parsed:
                            parsed["model"] = model_name
                            return parsed
                    except Exception:
                        return {
                            "answer": raw_text,
                            "evidence": {"model_used": model_name, "raw_response": "Processed successfully via SDK"},
                            "recommendation": "Review current sales trends in the dashboard charts.",
                            "model": model_name
                        }
            except Exception as e:
                err_str = str(e)
                if "API_KEY_INVALID" in err_str or "API key not valid" in err_str or "401" in err_str or "403" in err_str:
                    key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
                    return {
                        "answer": "Google Gemini API authentication failed: The API key in backend/.env is invalid or expired.",
                        "evidence": {
                            "configured_key": key_preview,
                            "key_format_note": "Google AI Studio API keys typically start with 'AIzaSy...'"
                        },
                        "recommendation": "1. Go to https://aistudio.google.com/app/apikey\n2. Click 'Create API key'\n3. Copy the key (starts with 'AIzaSy...')\n4. Paste it in backend/.env as: GEMINI_API_KEY=AIzaSy...\n5. Restart your backend server."
                    }
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    return {
                        "answer": "Gemini API rate limit or quota exceeded (HTTP 429).",
                        "evidence": {"error": err_str},
                        "recommendation": "Wait a few moments before sending another request, or check your rate limits in Google AI Studio."
                    }
                last_error = f"SDK {model_name}: {err_str}"
                continue

    # 2. Resilient fallback via httpx if SDK encounters environmental issues
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json"
            }
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                
                # If model doesn't support responseMimeType: application/json, retry without it
                if resp.status_code == 400 and "responseMimeType" in resp.text:
                    payload["generationConfig"].pop("responseMimeType", None)
                    resp = client.post(url, json=payload, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            raw_text = parts[0]["text"].strip()
                            clean_text = raw_text
                            if clean_text.startswith("```json"):
                                clean_text = clean_text[7:]
                            elif clean_text.startswith("```"):
                                clean_text = clean_text[3:]
                            if clean_text.endswith("```"):
                                clean_text = clean_text[:-3]
                            clean_text = clean_text.strip()

                            try:
                                parsed = json.loads(clean_text)
                                if isinstance(parsed, dict) and "answer" in parsed:
                                    parsed["model"] = model_name
                                    return parsed
                            except Exception:
                                return {
                                    "answer": raw_text,
                                    "evidence": {"model_used": model_name, "raw_response": "Processed successfully"},
                                    "recommendation": "Review current sales trends in the dashboard charts.",
                                    "model": model_name
                                }

                # Handle Invalid API Key immediately (Google returns 400 INVALID_ARGUMENT or 401/403)
                if resp.status_code in (401, 403) or (resp.status_code == 400 and ("API_KEY_INVALID" in resp.text or "API key not valid" in resp.text or "INVALID_ARGUMENT" in resp.text and "key" in resp.text.lower())):
                    key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
                    return {
                        "answer": "Google Gemini API authentication failed: The API key in backend/.env is invalid or expired.",
                        "evidence": {
                            "status_code": resp.status_code,
                            "configured_key": key_preview,
                            "key_format_note": "Google AI Studio API keys typically start with 'AIzaSy...'"
                        },
                        "recommendation": "1. Go to https://aistudio.google.com/app/apikey\n2. Click 'Create API key'\n3. Copy the key (starts with 'AIzaSy...')\n4. Paste it in backend/.env as: GEMINI_API_KEY=AIzaSy...\n5. Restart your backend server."
                    }
                elif resp.status_code == 429:
                    return {
                        "answer": "Gemini API rate limit or quota exceeded (HTTP 429).",
                        "evidence": {"error": resp.text},
                        "recommendation": "Wait a few moments before sending another request, or check your rate limits in Google AI Studio."
                    }
                else:
                    last_error = f"Model {model_name} returned HTTP {resp.status_code}: {resp.text}"

        except Exception as e:
            last_error = str(e)
            continue

    # If all models failed
    key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
    return {
        "answer": f"Unable to reach Google Gemini API. Details: {last_error or 'Network connection failed'}",
        "evidence": {
            "key_configured": key_preview,
            "models_attempted": models,
            "error_detail": str(last_error)
        },
        "recommendation": "Verify internet connectivity and make sure your GEMINI_API_KEY in backend/.env is generated from https://aistudio.google.com/app/apikey."
    }
