# API Captures: Balance Reports

## Purpose
- Store concrete request/response examples from live UI traffic.
- Keep these separate from discovery summaries.
- Use sanitized captures for tests and wrapper contracts.

## Coverage Status
- Captured now:
  - Summary request/response sample for Income
  - Detail request/response sample for Income subgroup (Nettoomsetning)
  - Summary request/response sample for Asset
  - Detail request/response sample for Asset subgroup (Varige driftsmidler)
  - Summary request/response sample for Liability
  - Detail request/response sample for Liability Equity
  - Fiscal period and date parameter behavior

## Full Re-Capture Pass Results (fresh tab)
- Run date: 2026-03-30
- Fiscal: 104779
- Note: when subgroup is expanded, group switch and filter changes trigger both summary and detail requests.

### Step 1: Group switch to Resultatregnskap
- Request: GET /Api/Fiscal/104779/Transaction/LedgerGroupData
- Query highlights:
  - fiscalPeriodId=2586516686
  - fiscalDateFrom=20120
  - fiscalDateTo=20147
  - ledgerGroup=Xena_Domain_Income_Accounts
- Response:
  - status=200
  - Count=12
  - first Group=Xena_Domain_Income_Accounts_Net_Turn_Over

### Step 2: Income detail for Nettoomsetning
- Request: GET /Api/Fiscal/104779/Transaction/LedgerGroupDataDetail
- Query highlights:
  - fiscalPeriodId=2586516686
  - FiscalDateFrom=20120
  - FiscalDateTo=20147
  - ledgerAccount=Xena_Domain_Income_Accounts_Net_Turn_Over
- Response:
  - status=200
  - Count=4
  - first Description=3001 Secura KS - oppdateringer og vedlikehold

### Step 3: Group switch to Eiendeler
- Request: GET /Api/Fiscal/104779/Transaction/LedgerGroupData
- Query highlights:
  - fiscalPeriodId=2586516686
  - fiscalDateFrom=20120
  - fiscalDateTo=20147
  - ledgerGroup=Xena_Domain_Asset_Accounts
- Response:
  - status=200
  - Count=10
  - first Group=Xena_Domain_Asset_Accounts_Intangible_Fixed_Asset

### Step 4: Asset detail for Varige driftsmidler
- Request: GET /Api/Fiscal/104779/Transaction/LedgerGroupDataDetail
- Query highlights:
  - fiscalPeriodId=2586516686
  - FiscalDateFrom=20120
  - FiscalDateTo=20147
  - ledgerAccount=Xena_Domain_Asset_Accounts_Tangible_Fixed_Asset
- Response:
  - status=200
  - Count=1
  - first Description=1280 Kontormaskiner

### Step 5: Group switch to Egenkapital + Gjeld
- Request: GET /Api/Fiscal/104779/Transaction/LedgerGroupData
- Query highlights:
  - fiscalPeriodId=2586516686
  - fiscalDateFrom=20120
  - fiscalDateTo=20147
  - ledgerGroup=Xena_Domain_Liability_Accounts
- Response:
  - status=200
  - Count=7
  - first Group=Xena_Domain_Liability_Accounts_Equity

### Step 6: Liability detail for Egenkapital
- Request: GET /Api/Fiscal/104779/Transaction/LedgerGroupDataDetail
- Query highlights:
  - fiscalPeriodId=2586516686
  - FiscalDateFrom=20120
  - FiscalDateTo=20147
  - ledgerAccount=Xena_Domain_Liability_Accounts_Equity
- Response:
  - status=200
  - Count=6
  - first Description=2000 Aksjekapital

### Step 7: Change Regnskapsar (2025 -> 2026)
- Summary request: GET /Api/Fiscal/104779/Transaction/LedgerGroupData
- Detail request: GET /Api/Fiscal/104779/Transaction/LedgerGroupDataDetail
- Query highlights:
  - fiscalPeriodId=2944485122
  - fiscalDateFrom=20454
  - fiscalDateTo=20818
  - FiscalDateFrom=20454
  - FiscalDateTo=20818
  - ledgerGroup=Xena_Domain_Liability_Accounts
  - ledgerAccount=Xena_Domain_Liability_Accounts_Equity
- Response:
  - summary status=200, Count=7
  - detail status=200, Count=6

### Step 8: Change dates (01.01.2026-31.12.2026 -> 01.02.2026-28.02.2026)
- Summary request: GET /Api/Fiscal/104779/Transaction/LedgerGroupData
- Detail request: GET /Api/Fiscal/104779/Transaction/LedgerGroupDataDetail
- Query highlights:
  - fiscalPeriodId=2944485122
  - fiscalDateFrom=20485
  - fiscalDateTo=20512
  - FiscalDateFrom=20485
  - FiscalDateTo=20512
  - ledgerGroup=Xena_Domain_Liability_Accounts
  - ledgerAccount=Xena_Domain_Liability_Accounts_Equity
- Response:
  - summary status=200, Count=7
  - detail status=200, Count=6

## Recommended Full Re-Capture Pass
- Goal: complete request/response pairs for all key states in one clean session.
- Start conditions:
  - Open reports page in a fresh tab and wait for first data load.
  - Keep only one subgroup expanded at a time.
- Run order:
  1. Group = Resultatregnskap, collapsed -> capture summary pair.
  2. Expand Nettoomsetning -> capture detail pair.
  3. Group = Eiendeler, collapsed -> capture summary pair.
  4. Expand Varige driftsmidler -> capture detail pair.
  5. Group = Egenkapital + Gjeld, collapsed -> capture summary pair.
  6. Expand Egenkapital -> capture detail pair.
  7. Change Regnskapsar -> capture summary pair and expanded-detail pair.
  8. Change Fra/Til date range -> capture summary pair and expanded-detail pair.
- Save format per step:
  - Request method, endpoint, full query params.
  - Response status, top keys, Count, first entity sample.
  - UI state note (group, period id, date range, expanded subgroup).

## Sanitization Rules
- Keep fiscalId values if needed for endpoint shape examples.
- Remove cache-buster query param _.
- Avoid storing tokens, cookies, headers, or personal/company identifiers.
- Prefer one representative response item instead of full payload dumps.

## Capture 1: Group Summary (Income)

### Request
- Method: GET
- Endpoint: /Api/Fiscal/104779/Transaction/LedgerGroupData
- Query:
  - ForceNoPaging=true
  - Page=0
  - PageSize=10
  - ShowDeactivated=false
  - fiscalPeriodId=2586516686
  - fiscalDateFrom=20089
  - fiscalDateTo=20453
  - ledgerId=
  - includeSimulatedBookkeeping=false
  - ledgerGroup=Xena_Domain_Income_Accounts

### Response (trimmed)
```json
{
  "Count": 13,
  "Entities": [
    {
      "Group": "Xena_Domain_Income_Accounts_Net_Turn_Over",
      "TranslatedGroup": "Nettoomsetning",
      "AmountMonth": null,
      "AmountYearToDate": 740037.5,
      "AmountMonthPrevious": null,
      "AmountYearToDatePrevious": 541082.45,
      "DifferencePeriod": null,
      "DifferenceYearToDate": 198955.05,
      "DifferencePeriodPercentage": null,
      "DifferenceYearToDatePercentage": 36.77,
      "AmountMonthDebit": null,
      "AmountMonthCredit": null,
      "AmountYearToDateDebit": null,
      "AmountYearToDateCredit": 740037.5,
      "AmountMonthPreviousDebit": null,
      "AmountMonthPreviousCredit": null,
      "AmountYearToDatePreviousDebit": null,
      "AmountYearToDatePreviousCredit": 541082.45
    }
  ]
}
```

## Capture 2: Group Summary (Liability)

### Request
- Method: GET
- Endpoint: /Api/Fiscal/104779/Transaction/LedgerGroupData
- Query:
  - ForceNoPaging=true
  - Page=0
  - PageSize=10
  - ShowDeactivated=false
  - fiscalPeriodId=2944485122
  - fiscalDateFrom=20454
  - fiscalDateTo=20818
  - ledgerId=
  - includeSimulatedBookkeeping=false
  - ledgerGroup=Xena_Domain_Liability_Accounts

### Response (trimmed)
```json
{
  "Count": 7,
  "Entities": [
    {
      "Group": "Xena_Domain_Liability_Accounts_Equity",
      "TranslatedGroup": "Egenkapital",
      "AmountMonth": -191179.09,
      "AmountYearToDate": -777118.84,
      "AmountMonthPrevious": -316060.36,
      "AmountYearToDatePrevious": -585306.75,
      "DifferencePeriod": 124881.27,
      "DifferenceYearToDate": -191812.09,
      "DifferencePeriodPercentage": -39.51184197853853,
      "DifferenceYearToDatePercentage": 32.77120757619829,
      "AmountMonthDebit": null,
      "AmountMonthCredit": 191179.09,
      "AmountYearToDateDebit": null,
      "AmountYearToDateCredit": 777118.84,
      "AmountMonthPreviousDebit": null,
      "AmountMonthPreviousCredit": 316060.36,
      "AmountYearToDatePreviousDebit": null,
      "AmountYearToDatePreviousCredit": 585306.75
    }
  ]
}
```

## Capture 3: Subgroup Detail (Liability Equity)

### Request
- Method: GET
- Endpoint: /Api/Fiscal/104779/Transaction/LedgerGroupDataDetail
- Query:
  - ForceNoPaging=true
  - Page=0
  - PageSize=10
  - ShowDeactivated=true
  - fiscalPeriodId=2944485122
  - FiscalDateFrom=20454
  - FiscalDateTo=20818
  - ledgerAccount=Xena_Domain_Liability_Accounts_Equity
  - includeSimulatedBookkeeping=false
  - ledgerId=

### Response (trimmed)
```json
{
  "Count": 6,
  "Entities": [
    {
      "Controller": "LedgerTag",
      "ControllerAction": null,
      "Id": "2181159363",
      "AccountNumber": 2000,
      "AccountDescription": "Aksjekapital",
      "LedgerAccount": "Xena_Domain_Liability_Accounts_Equity",
      "Group": null,
      "GroupIndex": 0,
      "Description": "2000 Aksjekapital",
      "DifferencePeriod": 0,
      "DifferenceYearToDate": 0,
      "DifferencePeriodPercentage": null,
      "DifferenceYearToDatePercentage": 0,
      "AmountMonth": 0,
      "AmountMonthDebit": null,
      "AmountMonthCredit": null,
      "AmountYearToDate": -40000,
      "AmountYearToDateDebit": null,
      "AmountYearToDateCredit": 40000,
      "AmountMonthPrevious": 0,
      "AmountMonthDebitPrevious": null,
      "AmountMonthCreditPrevious": null,
      "AmountYearToDatePrevious": -40000,
      "AmountYearToDateDebitPrevious": null,
      "AmountYearToDateCreditPrevious": 40000
    }
  ]
}
```

## Capture 4: Date Range Effect

### Request Before
- fiscalDateFrom=20089
- fiscalDateTo=20453

### Request After
- fiscalDateFrom=20120
- fiscalDateTo=20147

### Verified Effect
- Same endpoints are called with updated date integers.
- Expanded subgroup triggers both summary and detail refresh.
