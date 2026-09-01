from app.models.applications import ApplicationStatus
from app.services.state import application_state_machine


def test_infer_initial_state():
    assert application_state_machine.infer_initial_state("APPL", "FRST") == ApplicationStatus.APPLIED
    assert application_state_machine.infer_initial_state("DENY", "COMP") == ApplicationStatus.DENIED
    assert application_state_machine.infer_initial_state("DDEF", "HCOF") == ApplicationStatus.REVIEWED


def test_infer_initial_state_strips_and_uppercases():
    assert application_state_machine.infer_initial_state("  ddef ", " hod ") == ApplicationStatus.APPLIED


def test_infer_initial_state_unknown_returns_none():
    assert application_state_machine.infer_initial_state("ZZZZ", "XXXX") is None


def test_get_candidate_transition_state():
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.APPLIED, "DDEF", "HCOF"
        )
        == ApplicationStatus.REVIEWED
    )
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.REVIEWED, "COND", "TERT"
        )
        == ApplicationStatus.CONDITIONAL_OFFER
    )


def test_get_candidate_transition_state_unknown_returns_none():
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.APPLIED, "ZZZZ", "XXXX"
        )
        is None
    )


def test_gap_bridging_transitions_from_applied():
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.APPLIED, "DENY", "ENRQ"
        )
        == ApplicationStatus.DENIED
    )
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.APPLIED, "COND", "TERT"
        )
        == ApplicationStatus.CONDITIONAL_OFFER
    )
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.APPLIED, "DEIN", "NDPC"
        )
        == ApplicationStatus.READY_TO_REGISTER
    )


def test_terminal_identity_loops():
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.DENIED, "DENY", "COMP"
        )
        == ApplicationStatus.DENIED
    )
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.CANCELLED, "WADM", "CHNG"
        )
        == ApplicationStatus.CANCELLED
    )


def test_decision_mapping_matches_it_cs_processing():
    # IT/CS "Decision" vocabulary -> our ApplicationStatus (reasons ignored).
    # Firm Offer == Accepted, Deny == Denied, Conditional Offer == Conditional Offer.
    assert application_state_machine.infer_initial_state("ADMT", "FIRM") == ApplicationStatus.ACCEPTED
    assert application_state_machine.infer_initial_state("DENY", "COMP") == ApplicationStatus.DENIED
    assert application_state_machine.infer_initial_state("DENY", "ENRQ") == ApplicationStatus.DENIED
    assert (
        application_state_machine.infer_initial_state("COND", "TERT")
        == ApplicationStatus.CONDITIONAL_OFFER
    )
    assert (
        application_state_machine.infer_initial_state("COND", "CERT")
        == ApplicationStatus.CONDITIONAL_OFFER
    )


def test_offer_decisions_are_granular_but_consistent():
    # Our system splits each offer into "made" vs "applicant accepted"; both
    # stages still belong to the same IT/CS decision, so:
    #   Conditional Offer -> CONDITIONAL_OFFER (made) or READY_TO_REGISTER (accepted)
    #   Firm Offer       -> ACCEPTED (made)            or READY_TO_REGISTER (accepted)
    assert (
        application_state_machine.infer_initial_state("DEIN", "NDPC")
        == ApplicationStatus.READY_TO_REGISTER
    )
    assert (
        application_state_machine.infer_initial_state("DEIN", "NDPF")
        == ApplicationStatus.READY_TO_REGISTER
    )


def test_reimporting_the_same_decision_is_idempotent():
    """Loading the same ASR sheet twice must not flag rows whose decision is
    already recorded. Every state an (action, reason) can produce has to accept
    that same pair again as a no-op, or a re-import reports invalid transitions
    for work that has not changed.
    """
    for (_from_state, action, reason), new_state in list(
        application_state_machine.TRANSITIONS.items()
    ):
        assert (
            application_state_machine.get_candidate_transition_state(
                new_state, action, reason
            )
            == new_state
        ), f"{new_state.value} rejects a repeat of {action}/{reason}"


def test_end_states_accept_their_own_repeat():
    # the specific ones that were missing: a re-import of an unchanged December
    # sheet flagged 251 of 383 rows because of these
    cases = [
        (ApplicationStatus.READY_TO_REGISTER, "DEIN", "NDPC"),
        (ApplicationStatus.READY_TO_REGISTER, "DEIN", "NDPF"),
        (ApplicationStatus.CONDITIONAL_OFFER, "COND", "TERT"),
        (ApplicationStatus.CONDITIONAL_OFFER, "COND", "CERT"),
        (ApplicationStatus.ACCEPTED, "ADMT", "FIRM"),
    ]
    for state, action, reason in cases:
        assert (
            application_state_machine.get_candidate_transition_state(state, action, reason)
            == state
        )


def test_terminal_states_absorb_recognised_actions():
    """Duplicate detection can deny an application locally while the ASR export
    still carries its original action for weeks. That arrives as DENIED plus a
    perfectly ordinary action, which is a stale source rather than a real
    lifecycle move, so it holds instead of erroring.
    """
    for state in (ApplicationStatus.DENIED, ApplicationStatus.CANCELLED):
        for action, reason in (("DDEF", "HOD"), ("DEIN", "NDPC"), ("WADM", "CHNG"), ("APPL", "FRST")):
            assert (
                application_state_machine.get_candidate_transition_state(state, action, reason)
                == state
            ), f"{state.value} should hold on {action}/{reason}"


def test_terminal_states_still_reject_unknown_actions():
    # absorbing is only for the known vocabulary: a genuinely unrecognised pair
    # is a data-quality signal and must still surface
    assert (
        application_state_machine.get_candidate_transition_state(
            ApplicationStatus.DENIED, "ZZZZ", "XXXX"
        )
        is None
    )
