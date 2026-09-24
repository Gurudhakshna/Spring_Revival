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
        import traceback as _tb
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        # Header
        try:
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "JAL-RAKSHA AI", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(80,80,80)
            pdf.cell(0, 5, "AI-Powered Spring Revival & Recharge Decision Support", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(0,102,90)
            pdf.line(10, 20, 200, 20)
            pdf.ln(6)
        except Exception as e:
            print(f"[PDF DEBUG] header failed: {e}"); _tb.print_exc(); raise
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
            pdf.cell(0, 5, _sanitize(f"{k}: {v}"), new_x="LMARGIN", new_y="NEXT")
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
            why_text = "; ".join([_sanitize(x) for x in priority.get("why",[])[:2]])
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 4, _sanitize(f"Why: {why_text}"))
        risks = payload.get("risk_flags") or []
        if risks:
            pdf.set_font("Helvetica", "", 7)
            for rf in risks[:6]:
                if isinstance(rf, dict):
                    code = rf.get('code') or rf.get('flag') or 'RISK'
                    msg = rf.get('message') or rf.get('status') or ''
                    lvl = (rf.get('level') or '').upper()
                    pdf.cell(0, 4, _sanitize(f" - [{lvl or 'INFO'}] {code.upper()}: {msg}"), new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.cell(0, 4, _sanitize(f" - {rf}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        # 4 Intervention
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "4. Recommended Intervention", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        rec = payload.get("recommendation") or payload.get("simulation") or {}
        if rec:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 4, _sanitize(f"Type: {rec.get('intervention_type') or rec.get('type') or '-'}  Effect: {rec.get('predicted_score','-')} (from {rec.get('base_score','-')})  Cost: Rs {rec.get('estimated_cost_inr','-')}"))
            if rec.get("why"):
                pdf.set_x(pdf.l_margin)
                # Use cell with wrapping via multi_cell but ensure X is at left margin and text is sanitized + truncated if very long
                why_txt = _sanitize(str(rec.get('why','-')))
                # Truncate very long why to 200 chars to avoid overflow, and ensure spaces
                if len(why_txt) > 200:
                    why_txt = why_txt[:200] + "..."
                pdf.multi_cell(0, 4, _sanitize(f"Why: {why_txt}"))
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(120,20,20)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 4, _sanitize("Disclaimer: Prototype Decision-Support Estimate - requires field validation. Synthetic data - replace with validated government/field data before operational use. Springshed is visual estimate. Intervention lift is heuristic."))
        pdf.set_text_color(80,80,80)
        pdf.set_font("Helvetica", "", 6)
        pdf.cell(0, 4, _sanitize("Generated by JAL-RAKSHA AI | OSM | Synthetic Prototype Dataset"), align="C", new_x="LMARGIN", new_y="NEXT")
        out = pdf.output()
        if isinstance(out, str): out = out.encode("latin-1")
        elif isinstance(out, bytearray): out = bytes(out)
        return out, "application/pdf"
    except Exception as e:
        import traceback as _tb
        print(f"[PDF ERROR] detailed generation failed for {spring_id}: {e}")
        _tb.print_exc()
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
    spring = payload.get("spring") or {}
    recharge = payload.get("recharge") or {}
    priority = payload.get("priority") or {}
    rec = payload.get("recommendation") or payload.get("simulation") or {}
    risks = payload.get("risk_flags") or []
    factors = recharge.get("factors") or {}

    score = recharge.get("score", "-")
    cls_name = recharge.get("class", "MEDIUM")
    cls_color = "#15803d" if cls_name == "HIGH" else ("#d97706" if cls_name == "MEDIUM" else "#b91c1c")
    prio_color = "#b91c1c" if priority.get("priority_class") == "HIGH" else "#4b5563"

    factors_html = "".join(f"""
      <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9;">
        <span style="color:#64748b;text-transform:capitalize;">{h.escape(k.replace('_', ' '))}:</span>
        <strong style="color:#1e293b;">{h.escape(str(v))}</strong>
      </div>
    """ for k, v in list(factors.items())[:8])

    risks_html = "".join(f"""
      <li style="margin-bottom:6px;color:{'#b91c1c' if rf.get('level') == 'warn' else '#15803d'};">
        <strong>[{h.escape(rf.get('level', 'info').upper())}] {h.escape(str(rf.get('code','')).upper())}:</strong>
        <span style="color:#334155;">{h.escape(str(rf.get('message','')))}</span>
      </li>
    """ for rf in risks if isinstance(rf, dict)) if risks else "<p style='color:#64748b;'>No risk flags logged.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>JAL-RAKSHA AI Report - {h.escape(spring_id)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
    .container {{ max-width: 860px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); padding: 32px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0284c7; padding-bottom: 16px; margin-bottom: 24px; }}
    .title {{ font-size: 24px; font-weight: 800; color: #0369a1; margin: 0; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; color: #fff; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
    .card h3 {{ margin: 0 0 12px 0; font-size: 15px; color: #334155; text-transform: uppercase; letter-spacing: 0.05em; }}
    .kpi {{ font-size: 32px; font-weight: 800; margin: 4px 0; }}
    .disclaimer {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 14px; font-size: 12px; color: #991b1b; line-height: 1.5; margin-top: 24px; }}
    .footer {{ margin-top: 24px; text-align: center; font-size: 11px; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title">JAL-RAKSHA AI — Comprehensive Spring Report</h1>
        <div style="color:#64748b;font-size:13px;margin-top:4px;">Spring ID: <strong>{h.escape(spring_id)}</strong> | Nearby Village: {h.escape(str(spring.get('nearby_village', 'N/A')))} ({h.escape(str(spring.get('state', 'N/A')))})</div>
      </div>
      <span class="badge" style="background:{cls_color};">{h.escape(str(cls_name))} RECHARGE</span>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Recharge Suitability</h3>
        <div class="kpi" style="color:{cls_color};">{h.escape(str(score))}%</div>
        <div style="font-size:12px;color:#64748b;">Confidence: {h.escape(str(recharge.get('confidence', '0.85')))} · Class: {h.escape(str(cls_name))}</div>
      </div>
      <div class="card">
        <h3>Priority Assessment</h3>
        <div class="kpi" style="color:{prio_color};">{h.escape(str(priority.get('priority_score', '-')))}</div>
        <div style="font-size:12px;color:#64748b;">Class: <strong>{h.escape(str(priority.get('priority_class', '-')))}</strong></div>
      </div>
      <div class="card">
        <h3>Recommended Intervention</h3>
        <div style="font-size:18px;font-weight:700;color:#0284c7;margin:4px 0;">{h.escape(str(rec.get('intervention_type') or rec.get('type') or 'Recharge Trench'))}</div>
        <div style="font-size:12px;color:#64748b;">Est. Cost: <strong>₹{h.escape(str(rec.get('estimated_cost_inr', '-')))}</strong> | Projected Score: <strong>{h.escape(str(rec.get('predicted_score', '-')))}%</strong></div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Factor Contribution</h3>
        {factors_html}
      </div>
      <div class="card">
        <h3>Risk Flags & Diagnostics</h3>
        <ul style="padding-left:18px;margin:0;font-size:13px;line-height:1.5;">
          {risks_html}
        </ul>
      </div>
    </div>

    <div class="disclaimer">
      <strong>⚠️ Prototype Decision-Support Disclaimer:</strong> This assessment was generated by JAL-RAKSHA AI using prototype hydrological scoring and synthetic demo datasets. All scores and recommendations are advisory estimates intended to guide field hydrologists and local water managers. Ground-truthing, hydrogeological surveys, and community consultation are mandatory before operational expenditure.
    </div>

    <div class="footer">
      JAL-RAKSHA AI · Decision Support Platform for Spring Revival & Groundwater Recharge · Smart India Hackathon
    </div>
  </div>
</body>
</html>"""

