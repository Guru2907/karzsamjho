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


# C2: one fixed Hinglish sentence per situation, written by code, never by AI.
# Never "safe", "illegal" or "fake" (D6, D37).
STEPS = {
    "DO_NOT_PAY_FIRST": ("Paise mat bhejo. Loan se pehle paise maangna dhokha ho sakta hai. "
                         "Shikayat: 1930 ya cybercrime.gov.in"),
    "NOT_IN_RBI_LIST": ("Yeh app RBI ki list mein nahi mila. Loan lene se pehle bank mitra se poochho. "
                        "Pareshani ho to sachet.rbi.org.in par batao."),
    "CHECK_APP_NAME": ("RBI ki list mein milta-julta naam hai. Download se pehle app ka sahi naam "
                       "aur website check karo."),
    "SEND_CLEARER": "Saare number saaf nahi padhe gaye. Saaf photo bhejo, ya bank mitra se poochho.",
    "FIND_CHEAPER": "Yeh loan bahut mehenga hai. Bank, SHG ya cooperative se sasta loan poochho.",
    "ASK_BANK_MITRA": "Loan mehenga hai. Lene se pehle bank mitra se poochho.",
    "KEEP_PAPERS": "Kharcha aam loan jaisa hai. Saare kagaz sambhal ke rakho aur EMI time par bharo.",
}
BY_VERDICT = {"CANNOT_SAY": "SEND_CLEARER", "VERY_COSTLY": "FIND_CHEAPER",
              "COSTLY": "ASK_BANK_MITRA", "USUAL": "KEEP_PAPERS"}


def next_step(verdict: str, lender_match: str | None, pay_first: float | None = None) -> dict:
    """C2: exactly ONE next action for a check. First match wins:
    money asked before the loan -> lender NOT_FOUND -> lender SIMILAR -> the verdict.
    lender_match None (not checked, e.g. the RBI list is empty) never blocks: the verdict decides.
    An unknown verdict is treated as CANNOT_SAY (never claim more than we know, K = 0).
    """
    if pay_first:
        code = "DO_NOT_PAY_FIRST"
    elif lender_match == "NOT_FOUND":
        code = "NOT_IN_RBI_LIST"
    elif lender_match == "SIMILAR":
        code = "CHECK_APP_NAME"
    else:
        code = BY_VERDICT.get(verdict, "SEND_CLEARER")
    return {"code": code, "text_hi": STEPS[code]}


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
