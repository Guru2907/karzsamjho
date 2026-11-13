"""Verdict + lender match -> exactly one next action (C2), and the complaint route for a case (F5).

complaint_route follows CLAUDE.md "Complaint routes". English, because it goes into the evidence PDF
and the complaint letter (D20, D44). The police line for threats is added by evidence.py, not here.
"""

ROUTE_REGULATED = ("Regulated lender (in RBI's directory): complain to the lender's grievance officer "
                   "first. If there is no answer within 30 days: RBI Ombudsman, cms.rbi.org.in, phone 14448.")
ROUTE_UNREGULATED = ("App not found in RBI's directory: Sachet portal (sachet.rbi.org.in) and "
                     "cybercrime.gov.in, phone 1930.")
ROUTE_UNSURE = ("Check the exact app name first. If it is a regulated lender: its grievance officer, then "
                "the RBI Ombudsman after 30 days (cms.rbi.org.in, 14448). If not: Sachet portal "
                "(sachet.rbi.org.in) and cybercrime.gov.in, phone 1930.")


def next_step(verdict: str, lender_match: str) -> dict:
    raise NotImplementedError("next_step: see docs/TASKS.md C2")


def complaint_route(lender_match: str | None, day: int | None = None) -> str:
    """F5: the one complaint route that fits this lender.

    FOUND     -> the lender's grievance officer, then RBI Ombudsman after 30 days (+ "day N of 30")
    NOT_FOUND -> Sachet portal + cybercrime.gov.in / 1930
    SIMILAR or None (not checked, e.g. no RBI list loaded) -> both, after checking the exact name
    Never "illegal" or "fake" (D6).
    """
    if lender_match == "FOUND":
        if isinstance(day, int) and day > 0:
            wait = ("the 30 days are over: go to the RBI Ombudsman now." if day > 30
                    else f"today is day {day} of 30.")
            return f"{ROUTE_REGULATED} Since the case was opened, {wait}"
        return ROUTE_REGULATED
    if lender_match == "NOT_FOUND":
        return ROUTE_UNREGULATED
    return ROUTE_UNSURE
