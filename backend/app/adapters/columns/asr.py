"""
Contains the input, output and critical column enum and dictionary for the asr document adapter
"""

from enum import Enum

from app.adapters.validation.rules import ValidationRules as vr


class ASRInputColumn(
    Enum
):  # defines columns we deem nessicary from the asr sheet, these can be null, or empty, we just need to have the presence of these columns
    APPLICATION_NUMBER = "Application Number"
    CAMPUS_ID = "Campus Id"
    EMPLOYEE_ID = "Employee Id"
    ACADEMIC_PROGRAM_CODE = "Academic Program Code"
    TITLE = "Title"
    SEX = "Sex"
    ACADEMIC_PLAN1 = "Academic Plan 1"
    ACADEMIC_CAREER = "Academic Career"
    APPLICATION_DATE = "Application Date"
    CHOICE = "Choice"
    ADMIT_TYPE = "Admit Type"
    SEMESTER = "Semester"
    LAST_REGISTRATION = "Last Registration"
    PREVIOUS_APPLICATION_TERM = "Previous Application Term"
    FIRST_NAME = "First Name"
    LAST_NAME = "Last Name"
    CELL_PHONE = "Cell Phone"
    HOME_PHONE = "Home Phone"
    EMAIL = "Email Address"
    POPULATION_GROUP = "Population Group"
    BIRTH_DATE = "Birth Date"
    CITIZENSHIP_RESIDENCY = "Citizenship Residency"
    NON_SA_CITIZENSHIP = "Non SA Citizenship"
    EFFECTIVE_DATE = "Effective Date"
    PROGRAM_ACTION = "Program Action"
    PROGRAM_REASON = "Program Reason"
    PROGRAM_STATUS = "Program Status"
    # enum value: actually column value in the sheet


ASR_CRITICAL_COLUMNS = {  # defines what conditions columns have to pass
    ASRInputColumn.APPLICATION_NUMBER: [vr.NON_NULL],
    ASRInputColumn.CAMPUS_ID: [vr.NON_NULL],
    ASRInputColumn.EMPLOYEE_ID: [vr.NON_NULL],
    ASRInputColumn.FIRST_NAME: [vr.NON_NULL],
    ASRInputColumn.LAST_NAME: [vr.NON_NULL],
    ASRInputColumn.TITLE: [vr.NON_NULL],
    ASRInputColumn.SEX: [vr.NON_NULL],
    ASRInputColumn.CITIZENSHIP_RESIDENCY: [vr.NON_NULL],
    ASRInputColumn.ACADEMIC_CAREER: [vr.NON_NULL],
    # tbl applications
    ASRInputColumn.ACADEMIC_PROGRAM_CODE: [vr.NON_NULL],
    ASRInputColumn.ACADEMIC_PLAN1: [vr.NON_NULL],
    ASRInputColumn.CHOICE: [vr.NON_NULL],
}


ASR_OUTPUT_COLUMNS = {
    ASRInputColumn.APPLICATION_NUMBER: "application_number",  # tbl applications
    ASRInputColumn.CAMPUS_ID: "campus_id",  # shared
    ASRInputColumn.ACADEMIC_PROGRAM_CODE: "academic_program_code",
    ASRInputColumn.ACADEMIC_PLAN1: "academic_plan1",
    ASRInputColumn.ACADEMIC_CAREER: "academic_career",
    ASRInputColumn.APPLICATION_DATE: "application_date",
    ASRInputColumn.CHOICE: "choice",
    ASRInputColumn.ADMIT_TYPE: "admit_type",
    ASRInputColumn.SEMESTER: "semester",
    ASRInputColumn.LAST_REGISTRATION: "last_registration",
    ASRInputColumn.EFFECTIVE_DATE: "effective_date",
    ASRInputColumn.PREVIOUS_APPLICATION_TERM: "previous_application_term",  # end for application
    ASRInputColumn.EMPLOYEE_ID: "employee_id",  # tbl applicant
    ASRInputColumn.FIRST_NAME: "first_name",
    ASRInputColumn.LAST_NAME: "last_name",
    ASRInputColumn.CELL_PHONE: "cell_phone",
    ASRInputColumn.HOME_PHONE: "home_phone",
    ASRInputColumn.EMAIL: "email",
    ASRInputColumn.POPULATION_GROUP: "population_group",
    ASRInputColumn.BIRTH_DATE: "birth_date",
    ASRInputColumn.CITIZENSHIP_RESIDENCY: "citizenship_residency",
    ASRInputColumn.NON_SA_CITIZENSHIP: "non_sa_citizenship",  # end for applicant
    ASRInputColumn.PROGRAM_ACTION: "program_action",
    ASRInputColumn.PROGRAM_REASON: "program_reason",
    ASRInputColumn.PROGRAM_STATUS: "program_status",
    ASRInputColumn.SEX: "sex",
    ASRInputColumn.TITLE: "title",
}
