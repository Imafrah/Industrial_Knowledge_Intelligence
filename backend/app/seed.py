"""
Seed script — generates realistic mock industrial documents and equipment failure records.
Runs automatically on first startup if the documents table is empty.
"""
import logging
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Document, EquipmentFailure, IncidentReport
from app.ingestion import ingest_text_document
from app import gemini_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock Industrial Documents
# ---------------------------------------------------------------------------

MOCK_DOCUMENTS = [
    {
        "filename": "MP-2024-001_Centrifugal_Pump_Maintenance.txt",
        "content": """MAINTENANCE PROCEDURE MP-2024-001
Title: Centrifugal Pump P-101A/B Quarterly Maintenance
Equipment: P-101A, P-101B (Centrifugal Feed Pumps)
Location: Unit 3, Building A
Revision: Rev 3
Date: March 15, 2024
Prepared by: John Martinez, Senior Maintenance Engineer

1. SCOPE AND PURPOSE
This procedure covers the quarterly preventive maintenance for centrifugal feed pumps P-101A and P-101B, located in the primary processing unit. These pumps handle feedstock transfer at 250 GPM and 150 PSI discharge pressure.

2. SAFETY PRECAUTIONS
- Lock-Out/Tag-Out (LOTO) must be performed per SOP-SAF-003 before any work begins.
- Wear appropriate PPE: safety glasses, steel-toe boots, chemical-resistant gloves.
- Verify zero energy state before opening any pump casing.
- Refer to MSDS for feedstock chemical properties.
- Emergency shower location: Building A, East wall.

3. REQUIRED TOOLS AND MATERIALS
- Vibration analyzer (CSI 2140 or equivalent)
- Dial indicator set (0.001" resolution)
- Torque wrench (50-250 ft-lbs)
- Mechanical seal kit (part# MS-P101-KIT)
- Bearing grease (Mobil SHC 100)
- Alignment laser system

4. PROCEDURE STEPS
4.1 Pre-Maintenance Checks
  a) Record current vibration readings at all four bearing positions.
  b) Record motor amperage under load.
  c) Check and record suction and discharge pressures.
  d) Verify coupling guard is secure.

4.2 Bearing Inspection
  a) Remove bearing housing covers.
  b) Inspect bearings for discoloration, pitting, or excessive wear.
  c) Replace bearings if vibration exceeds 0.3 in/sec or visual damage is noted.
  d) Repack bearings with specified grease (3/4 fill for ball bearings).

4.3 Mechanical Seal Inspection
  a) Check for visible leakage at seal faces.
  b) Inspect seal flush piping and flow rate (target: 1.5 GPM).
  c) Replace seal if leakage exceeds 5 drops per minute.

4.4 Alignment Check
  a) Perform laser alignment check on coupling.
  b) Acceptable tolerance: 0.002" offset, 0.001"/inch angularity.
  c) Shim and adjust as needed.

4.5 Post-Maintenance Verification
  a) Remove LOTO, restore pump to service.
  b) Run pump for 30 minutes and verify:
     - Vibration within spec (<0.2 in/sec)
     - No seal leakage
     - Motor amps within nameplate rating
     - Discharge pressure at design point

5. DOCUMENTATION
Complete maintenance work order WO-2024-Q1-P101 in SAP PM module.
Record all measurements in Equipment History database.
Notify Operations Supervisor upon completion.

References: API 610 (Centrifugal Pumps), ANSI/HI 9.6.4 (Vibration)
Next scheduled maintenance: June 15, 2024
"""
    },
    {
        "filename": "SI-2024-015_Monthly_Safety_Inspection.txt",
        "content": """SAFETY INSPECTION REPORT SI-2024-015
Facility: Eastside Processing Plant
Inspection Type: Monthly Comprehensive Safety Walk-down
Date: April 8, 2024
Inspector: Sarah Chen, HSE Manager
Accompanied by: Mike O'Brien (Operations Supervisor), David Kim (Maintenance Lead)

INSPECTION SCOPE
All areas of Unit 3 and associated tank farm (TK-301 through TK-310), including electrical substations, pump stations, and control room.

FINDINGS SUMMARY
Total items inspected: 147
Satisfactory: 138
Needs attention: 7
Critical: 2

CRITICAL FINDINGS

1. FIRE SUPPRESSION SYSTEM — PUMP HOUSE B
   Finding: Deluge system DS-03 quarterly test showed 15% flow reduction. Nozzle blockage suspected.
   Regulation: NFPA 15 Section 10.3.2 requires annual flow test within 10% of design.
   Action Required: Flush and test all nozzles in DS-03 system within 7 days.
   Assigned to: David Kim
   Due Date: April 15, 2024
   Risk Rating: HIGH

2. EMERGENCY EXIT — CONTROL ROOM EAST
   Finding: Emergency exit door E-7 found obstructed by temporary storage of electrical conduit.
   Regulation: OSHA 1910.36(d)(1) — exits must be free of obstructions.
   Action Required: Remove all obstructions immediately. Issue reminder to all shift supervisors.
   Assigned to: Mike O'Brien
   Due Date: April 9, 2024 (IMMEDIATE)
   Risk Rating: CRITICAL

ITEMS NEEDING ATTENTION

3. Eye wash station EWS-12 near Tank TK-305: weekly inspection tag missing for 2 weeks.
4. Guardrail on platform PL-3A has loose bolt. Structurally sound but needs tightening.
5. Spill containment berm at loading dock LD-2 shows minor crack (3 inches). No active leakage.
6. Three fire extinguisher inspection tags expired (FE-27, FE-31, FE-45).
7. Safety shower SS-08 tepid water supply reading at 58°F (spec: 60-100°F per ANSI Z358.1).
8. Ventilation hood V-12 in lab area showing reduced airflow. Filter replacement may be needed.
9. Cable tray CT-15 near Substation 3 has missing cover plate, exposing cables to environment.

POSITIVE OBSERVATIONS
- All LOTO stations properly stocked and organized.
- New arc flash labels installed on all MCC panels — excellent work by electrical team.
- Emergency muster point signage updated per recent drill feedback.
- Gas detection system GDS-3 calibration is current (last cal: March 28, 2024).

NEXT INSPECTION: May 6, 2024
Distribution: Plant Manager, Operations Manager, HSE Department, Maintenance Department

Compliance Standards Referenced: OSHA 1910, NFPA 15, NFPA 25, ANSI Z358.1, API 2510
"""
    },
    {
        "filename": "EM-HX201_Heat_Exchanger_Manual_Excerpt.txt",
        "content": """EQUIPMENT MANUAL — SHELL AND TUBE HEAT EXCHANGER HX-201
Manufacturer: Alfa Laval Industrial
Model: M10-BFG, Serial No: AL-2019-44821
Installation Date: September 2019
Location: Unit 3, Cooling Circuit Loop B

1. GENERAL DESCRIPTION
The HX-201 is a fixed-tubesheet shell-and-tube heat exchanger designed for process cooling duty. It cools the reactor effluent stream from 285°F to 140°F using cooling water on the shell side.

Design Specifications:
- Tube side: Process fluid, Design P = 300 PSIG, Design T = 350°F
- Shell side: Cooling water, Design P = 150 PSIG, Design T = 200°F
- Heat duty: 4.2 MMBTU/hr
- TEMA class: BEM
- Material: Tubes — 316L SS; Shell — Carbon Steel SA-516 Gr 70
- Surface area: 850 sq ft
- Number of tubes: 224 (3/4" OD x 16 BWG x 12 ft)
- Tube passes: 4; Shell passes: 1

2. OPERATING PARAMETERS
Normal Operating Conditions:
  Tube side inlet: 285°F, 180 PSIG, 450 GPM
  Tube side outlet: 140°F, 165 PSIG
  Shell side inlet: 85°F, 60 PSIG, 800 GPM
  Shell side outlet: 115°F, 45 PSIG
  
Performance Monitoring:
  Monitor approach temperature (tube outlet minus shell inlet). 
  Design approach: 55°F. If approach exceeds 70°F, fouling is indicated.
  
  Clean U-value: 120 BTU/hr·ft²·°F
  Fouled U-value (design): 85 BTU/hr·ft²·°F
  If calculated U-value drops below 65 BTU/hr·ft²·°F, chemical or mechanical cleaning is required.

3. MAINTENANCE SCHEDULE
Routine (Monthly):
  - Check shell and tube side pressure drops. Rising ΔP indicates fouling.
  - Verify cooling water flow rate and inlet temperature.
  - Inspect for external leaks at flanges, nozzles, and expansion joints.
  
Annual Turnaround:
  - Hydrostatic test per ASME Section VIII (tube side: 450 PSIG, shell side: 225 PSIG).
  - Pull tube bundle for inspection. Check for tube wall thinning via eddy current testing.
  - Clean tubes mechanically (hydroblasting at 10,000 PSI max).
  - Replace gaskets (spiral wound, 316L/graphite, per API 601).
  - Verify tube-to-tubesheet joint integrity.

4. TROUBLESHOOTING GUIDE
| Symptom | Probable Cause | Action |
|---------|---------------|--------|
| High tube outlet temp | Fouling on tube/shell side | Clean; check CW flow |
| Low shell ΔP | Baffle damage or bypass | Inspect baffles during turnaround |
| Tube leak | Corrosion or erosion | Plug or replace affected tubes |
| Vibration | Flow-induced tube vibration | Check flow rates, verify baffle spacing |
| External leak at flanges | Gasket failure | Retorque or replace gaskets |

5. SPARE PARTS
- Tube bundle gasket set: P/N AL-GK-M10-001
- Floating head gasket: P/N AL-GK-M10-002
- Tube plugs (316L): P/N AL-TP-075-316
- Channel cover gasket: P/N AL-GK-M10-003

References: ASME BPVC Section VIII Div 1, TEMA Standards 10th Ed, API 660
"""
    },
    {
        "filename": "IR-2024-003_Near_Miss_Incident_Report.txt",
        "content": """INCIDENT / NEAR-MISS REPORT IR-2024-003
Classification: NEAR MISS (No injury, no environmental release)
Date of Incident: February 22, 2024, 14:35 hours
Location: Unit 3, Pump Area — near P-101A
Reported by: Carlos Gutierrez, Process Operator (Shift B)
Investigated by: Sarah Chen (HSE), John Martinez (Maintenance), Lisa Park (Operations Manager)

INCIDENT DESCRIPTION
During normal operations, operator Carlos Gutierrez was performing rounds in the pump area. While walking past pump P-101A, a section of 2-inch steam tracing tubing (ST-P101-03) separated at a threaded connection, releasing live steam at approximately 150 PSIG. The steam release lasted approximately 8 seconds before the upstream isolation valve was closed by the responding operator.

Mr. Gutierrez was approximately 6 feet from the release point. He was not struck by steam and suffered no injuries. He was wearing all required PPE including safety glasses, hard hat, hearing protection, and FRC clothing.

IMMEDIATE ACTIONS TAKEN
1. Area was barricaded and all personnel evacuated from 25-foot radius.
2. Steam supply to affected tracing circuit was isolated and locked out.
3. Shift supervisor notified; incident report initiated.
4. All other steam tracing connections in Unit 3 were inspected — two additional connections showed signs of thinning and were proactively repaired.

ROOT CAUSE ANALYSIS
Primary Cause: Corrosion under insulation (CUI) at the threaded connection caused wall thinning to the point of failure. The connection had thinned from nominal 0.154" to approximately 0.030" wall thickness.

Contributing Factors:
- Steam tracing system was installed in 2015 and had not been included in the CUI inspection program.
- Threaded connections in steam service are inherently vulnerable to CUI due to crevice geometry.
- The insulation material (calcium silicate) had absorbed moisture from a previous rainwater intrusion event in August 2023. This was not addressed at the time.

CORRECTIVE ACTIONS
| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | Add all steam tracing to CUI inspection program | David Kim | March 15, 2024 | Complete |
| 2 | UT thickness survey of all steam tracing threaded connections, Unit 3 | David Kim | March 31, 2024 | In Progress |
| 3 | Replace calcium silicate insulation with closed-cell foam on all steam tracing | John Martinez | June 30, 2024 | Planned |
| 4 | Toolbox talk: CUI awareness for all maintenance and operations crews | Sarah Chen | March 8, 2024 | Complete |
| 5 | Update P&ID to show steam tracing circuits for inspection planning | Lisa Park | April 30, 2024 | Planned |

LESSONS LEARNED
- Steam tracing systems, while "auxiliary," can present serious burn and pressure hazards and must be included in formal inspection programs.
- CUI is insidious and can progress rapidly once moisture is present. All moisture intrusion events must trigger a CUI assessment of affected areas.
- The operator's awareness and quick response in isolating the steam supply prevented a potential serious burn injury.

Investigation completed: March 5, 2024
Report approved by: Plant Manager, Robert Walsh
OSHA Recordable: No
"""
    },
    {
        "filename": "RC-2024-Q1_Regulatory_Compliance_Checklist.txt",
        "content": """REGULATORY COMPLIANCE CHECKLIST RC-2024-Q1
Facility: Eastside Processing Plant
Period: Q1 2024 (January–March)
Completed by: Amanda Foster, Compliance Engineer
Review Date: April 1, 2024
Approved by: Robert Walsh, Plant Manager

═══════════════════════════════════════════════════════════
ENVIRONMENTAL COMPLIANCE
═══════════════════════════════════════════════════════════

1. AIR EMISSIONS (Clean Air Act / State Air Permit #AP-2019-1247)
   [✓] Continuous Emissions Monitoring System (CEMS) operational — 99.2% uptime (req: >95%)
   [✓] Quarterly VOC leak detection (LDAR) completed — 3 leaks found, all repaired within 15 days per consent decree
   [✓] Flare pilot flame monitoring — zero outage events
   [✓] Annual emissions inventory submission — submitted February 28, 2024
   [!] Cooling tower PM10 drift eliminator inspection due May 2024 — schedule with turnaround

2. WATER DISCHARGE (NPDES Permit #WA-0023561)
   [✓] Monthly effluent sampling completed — all parameters within limits
   [✓] pH range: 6.8–7.9 (limit: 6.0–9.0) ✓
   [✓] Total Suspended Solids: max 18 mg/L (limit: 30 mg/L) ✓
   [✓] Oil & Grease: max 8 mg/L (limit: 15 mg/L) ✓
   [✓] Stormwater Pollution Prevention Plan (SWPPP) annual update completed
   [✓] Spill Prevention Control & Countermeasure (SPCC) plan current

3. WASTE MANAGEMENT (RCRA / State ID# WAD-991234567)
   [✓] Hazardous waste manifests filed within 30 days — 12 shipments this quarter
   [✓] 90-day storage area inspections weekly — no violations
   [✓] Used oil properly accumulated and recycled (2,400 gallons this quarter)
   [✓] Waste minimization report submitted with biennial report

═══════════════════════════════════════════════════════════
PROCESS SAFETY MANAGEMENT (OSHA PSM 1910.119)
═══════════════════════════════════════════════════════════

4. PROCESS HAZARD ANALYSIS (PHA)
   [✓] Unit 3 PHA revalidation completed January 2024 (5-year cycle)
   [✓] 14 recommendations generated — 8 completed, 6 in progress (all within schedule)
   [!] Unit 5 PHA revalidation due Q3 2024 — team leads identified

5. MECHANICAL INTEGRITY
   [✓] Pressure vessel inspections current per API 510 / NB-23
   [✓] Relief valve testing program: 47/52 valves tested this quarter (remaining 5 scheduled for April turnaround)
   [✓] Piping inspections per API 570 — risk-based inspection plan current
   [✓] Equipment failure analysis reports filed for 3 incidents

6. MANAGEMENT OF CHANGE (MOC)
   [✓] 9 MOCs initiated this quarter; 7 completed and closed, 2 in review
   [✓] Pre-startup safety review (PSSR) completed for all MOC-related changes
   [✓] All affected procedures updated before restart

7. TRAINING
   [✓] Initial PSM training completed for 4 new hires
   [✓] Refresher training completed for 89/92 personnel (3 on medical leave — scheduled upon return)
   [✓] Contractor safety orientation: 23 contractors trained this quarter

═══════════════════════════════════════════════════════════
OVERALL STATUS: COMPLIANT with 2 upcoming action items noted
Next Review: July 1, 2024
═══════════════════════════════════════════════════════════
"""
    },
    {
        "filename": "RFI-2024-008_Reactor_Temperature_Excursion.txt",
        "content": """REQUEST FOR INFORMATION RFI-2024-008
Project: Unit 3 Reliability Improvement Program
Subject: Reactor R-201 Temperature Excursion Event Analysis
Date: March 28, 2024
From: Lisa Park, Operations Manager
To: Process Engineering Team (cc: Robert Walsh, Plant Manager)

BACKGROUND
On March 20, 2024, Reactor R-201 experienced an unplanned temperature excursion during the catalyst regeneration cycle. The reactor bed temperature reached 782°F, exceeding the normal operating limit of 750°F and approaching the catalyst manufacturer's absolute maximum of 800°F. The excursion lasted approximately 12 minutes before operators were able to reduce the regeneration air flow and bring temperatures back within normal range.

No catalyst damage has been confirmed, but the event has raised concerns about the reliability of the temperature control system and the adequacy of our regeneration procedure.

INFORMATION REQUESTED

1. Temperature Control System Review
   Please provide:
   a) Analysis of TIC-R201-01 (reactor bed temperature controller) tuning parameters and response time during the excursion.
   b) Review of thermocouple placement — are the 6 existing thermocouples sufficient to detect hot spots in the 14-foot diameter bed?
   c) Recommendation on whether a high-temperature interlock (safety instrumented function) should be added. Current protection is alarm-only at 740°F.

2. Regeneration Procedure Analysis
   a) Review the current regeneration air flow ramp rate (currently 500 SCFM/hour increase). Is this too aggressive?
   b) What was the coke loading on the catalyst at the time? Higher-than-normal coke loading may explain the temperature spike.
   c) Provide comparison with regeneration procedures from similar reactors (reference: Reactor R-301 at Westside Plant).

3. Catalyst Impact Assessment
   a) Obtain catalyst vendor's assessment of potential damage from 12 minutes at 782°F.
   b) Recommend whether catalyst sampling and lab analysis should be performed.
   c) Estimate remaining catalyst life impact, if any.

TIMELINE
Please provide preliminary findings by April 12, 2024, with a full report by April 30, 2024. 
This analysis will feed into the Q2 process safety review and may result in a Management of Change (MOC) for any hardware or procedure modifications.

PRIORITY: HIGH
Related Equipment: R-201, TIC-R201-01, FIC-R201-AIR, TK-205 (Regeneration Air Receiver)
Related Procedures: SOP-OPS-012 (Catalyst Regeneration), SOP-OPS-015 (Reactor Emergency Procedures)
"""
    },
]


# ---------------------------------------------------------------------------
# Mock Equipment Failure Records
# ---------------------------------------------------------------------------

MOCK_FAILURES = [
    {"equipment_id": "P-101A", "failure_date": date(2023, 3, 15), "failure_type": "Mechanical seal failure", "root_cause": "Dry running due to loss of seal flush", "downtime_hours": 18.0},
    {"equipment_id": "P-101A", "failure_date": date(2023, 8, 22), "failure_type": "Bearing failure", "root_cause": "Inadequate lubrication — grease fitting blocked", "downtime_hours": 24.0},
    {"equipment_id": "P-101A", "failure_date": date(2024, 1, 10), "failure_type": "Excessive vibration", "root_cause": "Coupling misalignment after motor replacement", "downtime_hours": 8.0},
    {"equipment_id": "P-101B", "failure_date": date(2023, 6, 5), "failure_type": "Impeller erosion", "root_cause": "Cavitation due to low suction pressure", "downtime_hours": 48.0},
    {"equipment_id": "P-101B", "failure_date": date(2024, 2, 18), "failure_type": "Mechanical seal failure", "root_cause": "Thermal shock from process upset", "downtime_hours": 16.0},
    {"equipment_id": "HX-201", "failure_date": date(2023, 4, 12), "failure_type": "Tube leak", "root_cause": "Stress corrosion cracking in 316L tubes", "downtime_hours": 72.0},
    {"equipment_id": "HX-201", "failure_date": date(2023, 11, 30), "failure_type": "Fouling — high approach temperature", "root_cause": "Biological growth in cooling water side", "downtime_hours": 36.0},
    {"equipment_id": "HX-201", "failure_date": date(2024, 3, 5), "failure_type": "Gasket leak at channel cover", "root_cause": "Bolt relaxation from thermal cycling", "downtime_hours": 12.0},
    {"equipment_id": "R-201", "failure_date": date(2023, 7, 19), "failure_type": "Temperature control malfunction", "root_cause": "Thermocouple TC-03 failed — reading low", "downtime_hours": 6.0},
    {"equipment_id": "R-201", "failure_date": date(2023, 12, 8), "failure_type": "Catalyst bed channeling", "root_cause": "Uneven catalyst loading during last change-out", "downtime_hours": 96.0},
    {"equipment_id": "R-201", "failure_date": date(2024, 3, 20), "failure_type": "Temperature excursion during regeneration", "root_cause": "Excessive coke loading, aggressive air ramp rate", "downtime_hours": 4.0},
    {"equipment_id": "DS-03", "failure_date": date(2024, 4, 8), "failure_type": "Reduced flow — nozzle blockage", "root_cause": "Scale buildup in deluge nozzles", "downtime_hours": 0.0},
]


# ---------------------------------------------------------------------------
# Seed Runner
# ---------------------------------------------------------------------------


async def run_seed(db: AsyncSession):
    """
    Seed the database with mock documents and equipment failure records.
    Only runs if the documents table is empty (first startup).
    """
    # Check if already seeded
    result = await db.execute(select(func.count()).select_from(Document))
    doc_count = result.scalar()
    if doc_count > 0:
        logger.info(f"Database already has {doc_count} documents — skipping seed.")
        return

    logger.info("=" * 60)
    logger.info("SEEDING DATABASE with mock industrial documents...")
    logger.info("=" * 60)

    # Seed equipment failures first (no API calls needed)
    for failure_data in MOCK_FAILURES:
        failure = EquipmentFailure(**failure_data)
        db.add(failure)
    await db.commit()
    logger.info(f"Seeded {len(MOCK_FAILURES)} equipment failure records.")

    # Seed incident reports (lessons learned) with embeddings
    logger.info("Seeding incident reports (lessons learned)...")
    for inc_data in MOCK_INCIDENTS:
        try:
            emb = await gemini_client.generate_embedding(inc_data["description"])
            inc = IncidentReport(
                equipment_id=inc_data["equipment_id"],
                incident_date=inc_data["incident_date"],
                title=inc_data["title"],
                description=inc_data["description"],
                root_cause=inc_data["root_cause"],
                resolutions=inc_data["resolutions"],
                embedding=emb
            )
            db.add(inc)
        except Exception as e:
            logger.error(f"Failed to generate embedding for incident: {inc_data['title']}, error: {e}")
            inc = IncidentReport(
                equipment_id=inc_data["equipment_id"],
                incident_date=inc_data["incident_date"],
                title=inc_data["title"],
                description=inc_data["description"],
                root_cause=inc_data["root_cause"],
                resolutions=inc_data["resolutions"]
            )
            db.add(inc)
    await db.commit()
    logger.info(f"Seeded {len(MOCK_INCIDENTS)} incident reports.")

    # Seed documents through the full ingestion pipeline
    for i, doc_data in enumerate(MOCK_DOCUMENTS, 1):
        try:
            logger.info(f"[{i}/{len(MOCK_DOCUMENTS)}] Ingesting: {doc_data['filename']}")
            await ingest_text_document(
                text=doc_data["content"],
                filename=doc_data["filename"],
                db=db,
            )
            logger.info(f"[{i}/{len(MOCK_DOCUMENTS)}] ✓ Done: {doc_data['filename']}")
        except Exception as e:
            logger.error(f"[{i}/{len(MOCK_DOCUMENTS)}] ✗ Failed to seed {doc_data['filename']}: {e}")
            # Continue with next document even if one fails
            continue

    logger.info("=" * 60)
    logger.info("SEED COMPLETE")
    logger.info("=" * 60)


MOCK_INCIDENTS = [
    {
        "equipment_id": "P-101A",
        "incident_date": date(2023, 3, 15),
        "title": "Centrifugal Pump Seal Blowout & Feed Leak",
        "description": "During shift handover, pump P-101A seal blowout occurred, causing a hydrocarbon feedstock spill and minor fire. Operator response succeeded in isolating fuel source. Extinguished within 5 minutes.",
        "root_cause": "Dry running of mechanical seal due to block in seal flush plan 11 piping.",
        "resolutions": "Replaced mechanical seal, flushed and cleared flush piping, installed a low-flow alarm on the seal flush loop."
    },
    {
        "equipment_id": "HX-201",
        "incident_date": date(2023, 4, 12),
        "title": "Heat Exchanger Tube Rupture & Overpressure Event",
        "description": "Tube side leak allowed reactor effluent stream to enter lower-pressure cooling water shell side, triggering shell side relief valves to open. Cooling loop was contaminated with hydrocarbons.",
        "root_cause": "Stress corrosion cracking in SA-213 316L tubes, accelerated by chloride buildup in cooling water.",
        "resolutions": "Plugged ruptured tubes, upgraded tube metallurgy to Duplex 2205 for next turnaround, instituted daily chloride audits of cooling loop."
    },
    {
        "equipment_id": "R-201",
        "incident_date": date(2024, 3, 20),
        "title": "Reactor Temp Excursion during Catalyst Regen",
        "description": "Reactor R-201 bed temperature spiked to 782°F during catalyst regeneration run, exceeding high alarm trip. Operators immediately cut air feed rate and ramped up nitrogen purge.",
        "root_cause": "Regeneration air ramp rate was too aggressive combined with high initial carbon loading on catalyst.",
        "resolutions": "Revised SOP-OPS-012 (Catalyst Regeneration) to implement 50% slower initial air ramp, added high-temp alarm interlock to cut feed air automatically."
    },
    {
        "equipment_id": "P-101B",
        "incident_date": date(2023, 6, 5),
        "title": "Pump Cavitation and Impeller Destruction",
        "description": "P-101B experienced severe vibration and suction pressure drop. Dismantling revealed total destruction of suction side impeller vanes.",
        "root_cause": "Entrained vapor and vapor pocket formation due to low liquid level in supply accumulator tank TK-205.",
        "resolutions": "Replaced impeller, updated interlock logic to shut down pump when supply tank TK-205 level drops below 15%."
    }
]
