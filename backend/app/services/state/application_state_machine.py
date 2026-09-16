from app.models.applications import ApplicationStatus, DenyReason

# if the user does not have an existing application in the database then infer the state
INITIAL_STATES = {
    ("APPL", "FRST"): ApplicationStatus.APPLIED,    # initial application
    ("APPL", "SCND"): ApplicationStatus.APPLIED,    # initial application
    ("DDEF", "HOD"): ApplicationStatus.APPLIED,     # Referral to department awaiting review
    
    ("DDEF", "HCOF"): ApplicationStatus.REVIEWED,   # Department recommends conditional offer
    ("DDEF", "HFOF"): ApplicationStatus.REVIEWED,   # Department recommends firm offer
    ("DDEF", "HDNY"): ApplicationStatus.REVIEWED,   # Department recommends denying the application
    ("DDEF", "HWTL"): ApplicationStatus.REVIEWED,   # Department recommends waitlisting
    ("DDEF", "HRSL"): ApplicationStatus.REVIEWED,   # Department recommends waiting for final results
    
    ("COND", "TERT"): ApplicationStatus.CONDITIONAL_OFFER,   # Conditional offer awaiting agreemenent to ts and cs
    ("COND", "CERT"): ApplicationStatus.CONDITIONAL_OFFER,   # Conditional offer awaiting certified transcript
    ("DATA", "CONF"): ApplicationStatus.ACCEPTED,            # A condition of the offer has been met and offer is confirmed
    ("ADMT", "FIRM"): ApplicationStatus.ACCEPTED,            # Firm offer made
    ("DEIN", "NDPC"): ApplicationStatus.READY_TO_REGISTER,   # Applicant accepted conditional offer
    ("DEIN", "NDPF"): ApplicationStatus.READY_TO_REGISTER,   # Applicant accepted firm offer
    
    ("DENY", "COMP"): ApplicationStatus.DENIED,       # Deny non competitve
    ("DENY", "ENRQ"): ApplicationStatus.DENIED,       # Deny requirements not met

    ("WAPP", "REJO"): ApplicationStatus.CANCELLED,       # Applicant rejected offer
    ("WADM", "ICOM"): ApplicationStatus.CANCELLED,       # Cancelled  info not provided
    ("WADM", "CHNG"): ApplicationStatus.CANCELLED,       # Cancelled  changed programme
    ("WAPP", "WDRN"): ApplicationStatus.CANCELLED,       # Applicant withdrew   
}


DENY_REASON_MAPPING = {
    ("DENY", "COMP"): DenyReason.NOT_COMPETITIVE,
    ("DENY", "ENRQ"): DenyReason.REQUIREMENTS_NOT_MET,

}

#  (current state, new pa, new pr): new state
# (if in state, and program action, and program reason): new program status
TRANSITIONS = {
    # initial 
    (ApplicationStatus.APPLIED, "APPL", "FRST"): ApplicationStatus.APPLIED,
    (ApplicationStatus.APPLIED, "APPL", "SCND"): ApplicationStatus.APPLIED,
    # Applied -> stays Applied until reviewed
    (ApplicationStatus.APPLIED, "DDEF", "HOD"): ApplicationStatus.APPLIED,
    
    # Department recommendation 
    (ApplicationStatus.APPLIED, "DDEF", "HCOF"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.APPLIED, "DDEF", "HFOF"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.APPLIED, "DDEF", "HDNY"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.APPLIED, "DDEF", "HWTL"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.APPLIED, "DDEF", "HRSL"): ApplicationStatus.REVIEWED,
    
    # Looping: if already Reviewed, stays Reviewed until faculty acts
    (ApplicationStatus.REVIEWED, "DDEF", "HCOF"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.REVIEWED, "DDEF", "HFOF"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.REVIEWED, "DDEF", "HDNY"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.REVIEWED, "DDEF", "HWTL"): ApplicationStatus.REVIEWED,
    (ApplicationStatus.REVIEWED, "DDEF", "HRSL"): ApplicationStatus.REVIEWED,
    
    # Reviewed -> Conditional Offer
    (ApplicationStatus.REVIEWED, "COND", "TERT"): ApplicationStatus.CONDITIONAL_OFFER,
    (ApplicationStatus.REVIEWED, "COND", "CERT"): ApplicationStatus.CONDITIONAL_OFFER,

    # Reviewed -> Accepted (Firm Offer jumps straight to Accepted)
    (ApplicationStatus.REVIEWED, "ADMT", "FIRM"): ApplicationStatus.ACCEPTED,
    # Offer condition met -> Accept the applicant
    (ApplicationStatus.ACCEPTED, "DATA", "CONF"): ApplicationStatus.ACCEPTED,

    # Conditional Offer -> Accepted (applicant accepts)
    (ApplicationStatus.CONDITIONAL_OFFER, "DEIN", "NDPC"): ApplicationStatus.READY_TO_REGISTER,
    (ApplicationStatus.CONDITIONAL_OFFER, "DEIN", "NDPF"): ApplicationStatus.READY_TO_REGISTER,
    
    # Reviewed -> DENY
    (ApplicationStatus.REVIEWED, "DENY", "COMP"): ApplicationStatus.DENIED,
    (ApplicationStatus.REVIEWED, "DENY", "ENRQ"): ApplicationStatus.DENIED,

    (ApplicationStatus.REVIEWED, "WADM", "ICOM"): ApplicationStatus.CANCELLED, # Cancelled info not provided
    (ApplicationStatus.REVIEWED, "WADM", "CHNG"): ApplicationStatus.CANCELLED, # Cancelled changed programme
    (ApplicationStatus.REVIEWED, "WAPP", "REJO"): ApplicationStatus.CANCELLED, # Applicant rejected offer
    (ApplicationStatus.REVIEWED, "WAPP", "WDRN"): ApplicationStatus.CANCELLED, # Applicant withdrew
    
    # Conditional Offer -> DENY (applicant rejects)
    (ApplicationStatus.CONDITIONAL_OFFER, "WAPP", "WDRN"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.CONDITIONAL_OFFER, "WAPP", "REJO"): ApplicationStatus.CANCELLED,



    # Because of the gap between the asr files I added theese which allow state jumping
    # Worth asking question about frequency of asr uploads
    (ApplicationStatus.APPLIED, "DENY", "ENRQ"): ApplicationStatus.DENIED,
    (ApplicationStatus.APPLIED, "DENY", "COMP"): ApplicationStatus.DENIED,
    (ApplicationStatus.APPLIED, "COND", "TERT"): ApplicationStatus.CONDITIONAL_OFFER,
    (ApplicationStatus.APPLIED, "COND", "CERT"): ApplicationStatus.CONDITIONAL_OFFER,
    (ApplicationStatus.APPLIED, "DEIN", "NDPC"): ApplicationStatus.READY_TO_REGISTER,
    (ApplicationStatus.APPLIED, "DEIN", "NDPF"): ApplicationStatus.READY_TO_REGISTER,
    (ApplicationStatus.APPLIED, "ADMT", "FIRM"): ApplicationStatus.ACCEPTED,
    (ApplicationStatus.APPLIED, "DATA", "CONF"): ApplicationStatus.ACCEPTED,
    (ApplicationStatus.APPLIED, "WAPP", "REJO"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.APPLIED, "WAPP", "WDRN"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.APPLIED, "WADM", "ICOM"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.APPLIED, "WADM", "CHNG"): ApplicationStatus.CANCELLED,

    # Terminal identity loops: an application already finalized stays put when
    # a later sheet repeats the same decision, instead of rejecting the row.
    (ApplicationStatus.DENIED, "DENY", "ENRQ"): ApplicationStatus.DENIED,
    (ApplicationStatus.DENIED, "DENY", "COMP"): ApplicationStatus.DENIED,
    (ApplicationStatus.CANCELLED, "WADM", "ICOM"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.CANCELLED, "WADM", "CHNG"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.CANCELLED, "WAPP", "REJO"): ApplicationStatus.CANCELLED,
    (ApplicationStatus.CANCELLED, "WAPP", "WDRN"): ApplicationStatus.CANCELLED,
}

# Re-importing a sheet has to be idempotent: the same ASR export can be loaded
# twice, and rows whose decision is already recorded must not come back as
# "invalid transition". If (action, reason) legitimately produces state X, then
# seeing that same pair again while already in X is a repeat of a decision we
# have, not a new one. Only DENIED and CANCELLED had these loops written out by
# hand above, which left Accepted, Conditional Offer and Ready to Register
# rejecting their own repeats: re-importing an unchanged December sheet flagged
# 251 of 383 rows. Derived from TRANSITIONS rather than listed, so it cannot
# drift as new transitions are added.
TRANSITIONS.update(
    {
        (new_state, action, reason): new_state
        for (_from_state, action, reason), new_state in list(TRANSITIONS.items())
        if (new_state, action, reason) not in TRANSITIONS
    }
)

# Terminal states absorb any recognised action instead of erroring. An
# application can reach DENIED or CANCELLED here without the sheet knowing:
# duplicate detection denies the weaker of a pair locally, while the ASR export
# still carries that application's original action for weeks afterwards. The
# next import then arrives with, say, DENIED + DDEF/HOD, which is not a real
# lifecycle move at all, just a source that has not caught up. Holding is right:
# the decision stands, and a convenor can still change it from the decisions
# screen. Only pairs already in the vocabulary are absorbed, so a genuinely
# unknown action/reason still flags as the data-quality signal it is.
_TERMINAL_STATES = (ApplicationStatus.DENIED, ApplicationStatus.CANCELLED)
_KNOWN_PAIRS = {(a, r) for (a, r) in INITIAL_STATES} | {
    (a, r) for (_s, a, r) in TRANSITIONS
}
TRANSITIONS.update(
    {
        (state, action, reason): state
        for state in _TERMINAL_STATES
        for (action, reason) in _KNOWN_PAIRS
        if (state, action, reason) not in TRANSITIONS
    }
)


def infer_initial_state(action: str, reason: str) -> ApplicationStatus | None:
    """
        Infer the state of an application if the status 
        has not been defined for an applicant.

        Returns: None if no state is defined for the given arguments
    """
    key = (action.strip().upper(), reason.strip().upper())
    initial_state = INITIAL_STATES.get(key)
    return initial_state



def get_candidate_transition_state(state: ApplicationStatus, action: str, reason: str) -> ApplicationStatus | None:
    """
        Returns the next state for a given application lifecycle entry
        or none if no transition is defined for that given arguments
    """
    key = (state, action.strip().upper(), reason.strip().upper())
    candidate_state = TRANSITIONS.get(key)
    return candidate_state




def get_deny_reason(action: str, reason: str) -> DenyReason | None:
    """Return the deny reason of an application"""

    key = (action.strip().upper(), reason.strip().upper())
    deny_reason = DENY_REASON_MAPPING.get(key)
    return deny_reason





 