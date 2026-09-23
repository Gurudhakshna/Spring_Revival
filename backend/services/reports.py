"""Dynamic PDF report generation - Simplified robust version."""
from __future__ import annotations
import time, json
from typing import Dict, Any

def _try_fpdf():
    try:
        from fpdf import FPDF
        return FPDF
    except Exception:
        return None

def _sanitize(t: Any) -> str:
    s = str(t or "")
    return s.encode("latin-1", "replace").decode("latin-1")

def generate_pdf(payload: Dict[str,Any]) -> tuple[bytes, str]:
    FPDF = _try_fpdf()
    spring_id = payload.get("spring_id") or "SPR-001"
    if FPDF is None:
        j = json.dumps({"title": f"JAL-RAKSHA AI - {spring_id}", "payload": payload}, indent=2).encode("utf-8")
        return j, "application/json"
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        # Header
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "JAL-RAKSHA AI", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80,80,80)
        pdf.cell(0, 5, "AI-Powered Spring Revival & Recharge Decision Support", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(0,102,90)
        pdf.line(10, 20, 200, 20)
        pdf.ln(6)
        # Title
        pdf.set_text_color(0,0,0)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _sanitize(f"Assessment Report - {spring_id}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100,100,100)
        pdf.cell(0, 4, _sanitize(f"Generated: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} | Prototype Decision-Support Estimate"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        # 1 Location
        pdf.set_text_color(0,0,0)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "1. Location & Spring", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        spring = payload.get("spring") or {}
        for k,v in [("Spring ID", spring_id), ("Village", spring.get("nearby_village","-")), ("State", spring.get("state","-")), ("Coordinates", f"{spring.get('latitude','-')}, {spring.get('longitude','-')}"), ("Elevation", f"{spring.get('elevation_m','-')} m"), ("Rainfall", f"{spring.get('annual_rainfall_mm','-')} mm"), ("Geology", spring.get("geology","-")), ("Land Use", spring.get("land_use","-"))]:
            pdf.cell(35, 5, _sanitize(k+":"), border=0)
            pdf.cell(0, 5, _sanitize(str(v)), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        # 2 Recharge
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "2. AI Analysis - Recharge Suitability", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        recharge = payload.get("recharge") or {}
        pdf.cell(0, 5, _sanitize(f"Score: {recharge.get('score','-')} /100  Class: {recharge.get('class','-')}  Confidence: {recharge.get('confidence','-')}"), new_x="LMARGIN", new_y="NEXT")
        factors = recharge.get("factors") or {}
        if factors:
            pdf.set_font("Helvetica", "", 7)
            for k,v in list(factors.items())[:6]:
                # Simple line without bar to avoid horizontal space bug
                pdf.cell(0, 4, _sanitize(f"  {k}: {v}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        # 3 Priority
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "3. Priority & Risk", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        priority = payload.get("priority") or {}
        pdf.cell(0, 5, _sanitize(f"Priority: {priority.get('priority_score','-')} ({priority.get('priority_class','-')})"), new_x="LMARGIN", new_y="NEXT")
        if priority.get("why"):
            # Join with comma, no special chars
            why_text = "; ".join([_sanitize(x) for x in priority.get("why",[])[:2]])
            pdf.multi_cell(0, 4, _sanitize(f"Why: {why_text}"))
        risks = payload.get("risk_flags") or []
        if risks:
            pdf.set_font("Helvetica", "", 7)
            for rf in risks[:5]:
                if isinstance(rf, dict):
                    pdf.cell(0, 4, _sanitize(f" - {rf.get('flag','')} : {rf.get('status','')}"), new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.cell(0, 4, _sanitize(f" - {rf}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        # 4 Intervention
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "4. Recommended Intervention", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        rec = payload.get("recommendation") or payload.get("simulation") or {}
        if rec:
            pdf.multi_cell(0, 4, _sanitize(f"Type: {rec.get('intervention_type') or rec.get('type') or '-'}  Effect: {rec.get('predicted_score','-')} (from {rec.get('base_score','-')})  Cost: Rs {rec.get('estimated_cost_inr','-')}"))
            if rec.get("why"):
                pdf.multi_cell(0, 4, _sanitize(f"Why: {rec.get('why','-')}"))
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(120,20,20)
        pdf.multi_cell(0, 4, _sanitize("Disclaimer: Prototype Decision-Support Estimate - requires field validation. Synthetic data - replace with validated government/field data before operational use. Springshed is visual estimate. Intervention lift is heuristic."))
        pdf.set_text_color(80,80,80)
        pdf.set_font("Helvetica", "", 6)
        pdf.cell(0, 4, _sanitize("Generated by JAL-RAKSHA AI | OSM | Synthetic Prototype Dataset"), align="C", new_x="LMARGIN", new_y="NEXT")
        out = pdf.output()
        if isinstance(out, str): out = out.encode("latin-1")
        elif isinstance(out, bytearray): out = bytes(out)
        return out, "application/pdf"
    except Exception as e:
        # Absolute fallback - minimal PDF
        try:
            from fpdf import FPDF as _FPDF2
            pdf2 = _FPDF2()
            pdf2.add_page()
            pdf2.set_font("Helvetica", "B", 12)
            pdf2.cell(0, 10, _sanitize(f"JAL-RAKSHA AI Report - {spring_id}"), new_x="LMARGIN", new_y="NEXT")
            pdf2.set_font("Helvetica", "", 9)
            pdf2.multi_cell(0, 6, _sanitize(f"Score: {payload.get('recharge',{}).get('score','-')}  State: {payload.get('spring',{}).get('state','-')}  Error detail was: {str(e)[:200]}"))
            out2 = pdf2.output()
            if isinstance(out2, bytearray): out2 = bytes(out2)
            elif isinstance(out2, str): out2 = out2.encode("latin-1")
            return out2, "application/pdf"
        except Exception as e2:
            j = json.dumps({"error": str(e), "payload": payload}).encode("utf-8")
            return j, "application/json"

def generate_html_report(payload: Dict[str,Any]) -> str:
    import html as h
    spring_id = payload.get("spring_id") or "SPR-001"
    return f"""<html><body style="font-family:system-ui;padding:20px">
<h1>JAL-RAKSHA AI - {h.escape(spring_id)}</h1>
<pre>{h.escape(json.dumps(payload, indent=2))}</pre>
<p><em>Prototype Decision-Support Estimate</em></p>
</body></html>"""
