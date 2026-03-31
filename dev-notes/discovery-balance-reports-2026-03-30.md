# Discovery: Balance Reports (UI traffic)

## Context
- Date: 2026-03-30
- Area: Finansrapporter -> Balanse
- Trigger/user action: Open report page, change Finansgruppe, expand a subgroup row
- Fiscal used during capture: 104779

## Verified Calls

### 1) Initial metadata calls on page load
- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/LedgerTag/LedgerGroup
- Params seen: ForceNoPaging=true

- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/FiscalPeriod
- Params seen: ForceNoPaging=true

- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/Department
- Params seen: ForceNoPaging=true

- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/Bearer
- Params seen: ForceNoPaging=true

- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/Purpose
- Params seen: ForceNoPaging=true

### 2) Summary rows for selected Finansgruppe
- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/Transaction/LedgerGroupData
- Required params observed:
  - ForceNoPaging=true
  - Page=0
  - PageSize=10
  - ShowDeactivated=false
  - fiscalPeriodId=<id>
  - fiscalDateFrom=<int>
  - fiscalDateTo=<int>
  - ledgerId=
  - includeSimulatedBookkeeping=false
  - ledgerGroup=<group code>
- Notes:
  - UI adds cache-buster param _=<timestamp>
  - Sometimes a first request without period params is aborted; the period-filtered request succeeds

### 3) Detail rows (accounts within subgroup)
- Method: GET
- Endpoint: /Api/Fiscal/{fiscalId}/Transaction/LedgerGroupDataDetail
- Required params observed:
  - ForceNoPaging=true
  - Page=0
  - PageSize=10
  - ShowDeactivated=true
  - fiscalPeriodId=<id>
  - FiscalDateFrom=<int>
  - FiscalDateTo=<int>
  - ledgerAccount=<subgroup code>
  - includeSimulatedBookkeeping=false
  - ledgerId=
- Notes:
  - UI uses FiscalDateFrom/FiscalDateTo (capital F) on this endpoint
  - UI adds cache-buster param _=<timestamp>

### 4) Change Regnskapsar (fiscal year)
- Trigger: change Regnskapsar combobox value
- Verified behavior:
  - fiscalPeriodId changes to selected period id
  - fiscalDateFrom/fiscalDateTo are reset to that fiscal period boundaries
  - UI reloads LedgerGroupData immediately
  - If a subgroup is expanded, UI also reloads LedgerGroupDataDetail for that subgroup

### 5) Change date range (Fra/Til)
- Trigger: update fiscalDateFrom/fiscalDateTo in view model
- Verified behavior:
  - UI reloads LedgerGroupData with updated fiscalDateFrom/fiscalDateTo
  - If a subgroup is expanded, UI also reloads LedgerGroupDataDetail with updated FiscalDateFrom/FiscalDateTo
  - Date params are integer day values
  - Integer dates match Unix day numbers (days since 1970-01-01 UTC)

## Verified group mapping from selector
- Resultatregnskap -> Xena_Domain_Income_Accounts
- Eiendeler -> Xena_Domain_Asset_Accounts
- Egenkapital + Gjeld -> Xena_Domain_Liability_Accounts

## Verified fiscal period mapping from selector
- 01.01.2026 - 31.12.2026 -> 2944485122
- 01.01.2025 - 31.12.2025 -> 2586516686
- 01.01.2024 - 31.12.2024 -> 2188936542
- 01.01.2023 - 31.12.2023 -> 2181157216

## Date integer examples
- 2025-01-01 -> 20089
- 2025-12-31 -> 20453
- 2025-02-01 -> 20120
- 2025-02-28 -> 20147

## Response Notes

### LedgerGroupData response shape
- Top keys:
  - Count
  - Entities
- Entity keys observed:
  - Group
  - TranslatedGroup
  - AmountMonth
  - AmountYearToDate
  - AmountMonthPrevious
  - AmountYearToDatePrevious
  - DifferencePeriod
  - DifferenceYearToDate
  - DifferencePeriodPercentage
  - DifferenceYearToDatePercentage
  - AmountMonthDebit
  - AmountMonthCredit
  - AmountYearToDateDebit
  - AmountYearToDateCredit
  - AmountMonthPreviousDebit
  - AmountMonthPreviousCredit
  - AmountYearToDatePreviousDebit
  - AmountYearToDatePreviousCredit

### LedgerGroupDataDetail response shape
- Top keys:
  - Count
  - Entities
- Entity keys observed:
  - Controller
  - ControllerAction
  - Id
  - AccountNumber
  - AccountDescription
  - LedgerAccount
  - Group
  - GroupIndex
  - Description
  - DifferencePeriod
  - DifferenceYearToDate
  - DifferencePeriodPercentage
  - DifferenceYearToDatePercentage
  - AmountMonth
  - AmountMonthDebit
  - AmountMonthCredit
  - AmountYearToDate
  - AmountYearToDateDebit
  - AmountYearToDateCredit
  - AmountMonthPrevious
  - AmountMonthDebitPrevious
  - AmountMonthCreditPrevious
  - AmountYearToDatePrevious
  - AmountYearToDateDebitPrevious
  - AmountYearToDateCreditPrevious

## Example subgroup code observed
- Egenkapital row expand used:
  - ledgerAccount=Xena_Domain_Liability_Accounts_Equity

## Open Questions
- Confirm whether wrapper should always include both debit/credit fields and signed aggregate fields, or normalize to one representation.
- Confirm expected conversion/meaning of fiscalDateFrom/fiscalDateTo integer values in domain layer.
- Confirm whether we should support optional ledgerId filter in v1 workflow.

## Related Artifacts
- See api-captures-balance-reports-2026-03-30.md for sanitized request/response examples.
