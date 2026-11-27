# OpenAPI spec enum discrepancies

**Audience:** owners of the Trading API and Broker API OpenAPI specs.

alpaca-py generates enums from pinned copies of the public OpenAPI specs. Three generated enums have
values that differ from the ones the hand-written SDK enums have sent and accepted since 2022–2023.
If the spec is wrong, a client generated from it (alpaca-py or any other) either rejects real API
responses or sends values the API may not accept.

Pinned specs compared (in this repository):

| File | `info.title` / `info.version` | SHA-256 |
| --- | --- | --- |
| `tools/openapi/specs/broker-api.json` | Broker API 1.1.1 | `02e96e2b52708cd9315aaad8a9e76e3a3e68559f029e3ede5a61ed5d68af91d0` |
| `tools/openapi/specs/trading-api.json` | Trading API 2.0.1 | `1651b0c3d257b7acb439ae4356b6367aa134c3915d0ca52935c3ff9c3bd5bffe` |

Public docs were checked on 2026-10-30. The reference pages at docs.alpaca.markets are rendered from
these same specs, so where they repeat a spec value they confirm what is published, not what the
server does. The hand-written guides (Data Validations, IRA) are independent evidence.

The alpaca-py test fixtures quoted below are mocked responses, not captures from the live API. They
show what the SDK expects, not what the server returns.

## Summary

| # | Spec | Schema | Spec value(s) | SDK legacy value(s) | Likely wrong | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Broker | `AnnouncementCASubType` | `until_split` | `unit_split` | Spec (typo) | High |
| 2 | Trading | `CorporateActionCaType` | `Dividend`, `Merger`, `Split`, `Spinoff`, `Reorg` | `dividend`, `merger`, `spinoff`, `split` | Unclear; needs server confirmation | Low |
| 3 | Broker | `Disclosures.employment_status` | `unemployed`, `employed`, `student`, `retired` | `UNEMPLOYED`, `EMPLOYED`, `STUDENT`, `RETIRED` | Spec (casing) | Medium–high |

---

## 1. Broker `AnnouncementCASubType`: `until_split` should probably be `unit_split`

**Spec location:** `broker-api.json`, schema `AnnouncementCASubType`
- Enum: `#/components/schemas/AnnouncementCASubType/enum`
- Used by: `#/components/schemas/Announcement/properties/ca_sub_type`

**Spec values:**
`cash`, `stock`, `merger_update`, `merger_completion`, `stock_split`, `until_split`, `reverse_split`,
`recapitalization`, `spinoff`

`until_split` also appears in two descriptions: the `AnnouncementCASubType` description (as a bold
list item under the `split` type) and the `AnnouncementCAType` description ("has `stock_split`,
`until_split`, `reverse_split`, and `recapitalization` sub types").

**SDK legacy value:** `CorporateActionSubType.UNIT_SPLIT = "unit_split"`
([`alpaca/trading/enums.py`](../alpaca/trading/enums.py#L222)), present since commit `91b43d1`
(2022-05-23, "adds CorporateActionAnnouncement and related models").

**Evidence:**
- "Until split" is not a corporate-action term; "unit split" is.
- In the spec, the description of `until_split` is copied word for word from `stock_split`. This
  points to a hand-edited entry rather than a deliberate new subtype.
- The current Market Data corporate actions endpoint lists `unit_split` among its `types` values and
  has no `until_split`
  ([Corporate actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1)).
- The Broker Activities guide lists the activity `SPLIT` / `USPLIT` as "Unit split"
  ([Activities](https://docs.alpaca.markets/us/docs/activity-sse)).
- The Trading API reference for `/v2/corporate_actions/announcements` uses neither spelling
  ([Retrieve Announcements](https://docs.alpaca.markets/us/v1.1/reference/get-v2-corporate_actions-announcements-1)).
- The Broker spec published on 2026-11-27 still has `until_split`.

**Likely wrong:** the spec, through a typo.

**Suggested fix:** in `AnnouncementCASubType`, rename `until_split` to `unit_split` in the enum and in
both descriptions. Give it its own description, for example: "A unit split, in which a unit
security is separated into its component securities (for example shares and warrants)." Before
merging, confirm with the corporate-actions service owners which literal the API emits.

**alpaca-py workaround:** `tools/openapi/surfaces/broker/patches.json` replaces the enum with the
`unit_split` spelling, so the generated `AnnouncementCASubType` matches the SDK's released value. The
patch stops generation once the spec is fixed, which is the signal to delete it.

---

## 2. Trading `CorporateActionCaType`: capitalized values, while the SDK sends lowercase

**Spec location:** `trading-api.json`, schema `CorporateActionCaType`
- Enum: `#/components/schemas/CorporateActionCaType/enum` (`example: "Dividend"`)
- Used by:
  - the query parameter `ca_types` on `GET /v2/corporate_actions/announcements`:
    `#/paths/~1v2~1corporate_actions~1announcements/get/parameters/0/schema/items`
    (`style: form`, `explode: false`, `required: true`)
  - the response field `#/components/schemas/CorporateAnnouncement/properties/ca_type`

**Spec values:** `Spinoff`, `Merger`, `Split`, `Reorg`, `Dividend`

**SDK legacy values:** `CorporateActionType` sends `dividend`, `merger`, `spinoff`, `split`
([`alpaca/trading/enums.py`](../alpaca/trading/enums.py#L191)). These values go to
`GET /v2/corporate_actions/announcements?ca_types=...` through `GetCorporateAnnouncementsRequest`
([`alpaca/trading/requests.py`](../alpaca/trading/requests.py#L814)) and are joined with commas in
[`alpaca/trading/client.py`](../alpaca/trading/client.py#L706-L707). The SDK has done this since
commit `91b43d1` (2022-05-23). The SDK has no `Reorg` value.

**Comparison with the Broker spec:** the equivalent Broker schema is lowercase.
- `broker-api.json` `#/components/schemas/AnnouncementCAType/enum`: `dividend`, `merger`, `split`,
  `spinoff`
- The Broker `ca_types` parameter, `#/paths/~1v1~1corporate_actions~1announcements/get/parameters/0`,
  is an untyped `string` described as "A comma-delimited list of CorporateActionType values".

**Evidence:**
- The public Trading reference agrees with the Trading spec. It says `ca_types` is "A comma-delimited
  list of Dividend, Merger, Spinoff, or Split", and its response examples use `"ca_type": "Dividend"`.
  It also marks the endpoint as deprecated in favour of the Market Data corporate actions endpoint
  ([Retrieve Announcements](https://docs.alpaca.markets/us/v1.1/reference/get-v2-corporate_actions-announcements-1)).
- One of those same examples pairs `"ca_type": "Dividend"` with `"ca_sub_type": "DIV"`, and another
  with `"ca_sub_type": "cash"`. The Trading examples therefore do not match the Broker subtype enum
  either.
- The docstring of the legacy SDK enum links to the older Trading docs, which used lowercase values.
  The SDK's mocked fixtures use `"ca_type": "dividend"`
  (`tests/trading/trading_client/test_corporate_announcements.py`). We have no live capture of this
  endpoint.
- We know of no SDK bug reports saying that lowercase `ca_types` is rejected. This suggests the
  server matches case-insensitively, at least on input, but we have not confirmed it.

**Likely wrong:** unclear. The Trading spec and its docs agree with each other but disagree with the
Broker spec and with four years of SDK traffic. Possible explanations:
1. The server accepts both cases on input and returns capitalized `ca_type`. The spec is right about
   responses but should say that it accepts lowercase.
2. The server is lowercase end to end, as in the Broker spec. The Trading spec and docs are wrong.
3. The server is capitalized end to end and rejects lowercase. The SDK is wrong, which would conflict
   with the absence of bug reports.

**Suggested fix:** ask the Trading API owners which literals `/v2/corporate_actions/announcements`
accepts in `ca_types` and returns in `ca_type`. Then do one of the following:
- If input is case-insensitive, say so in the `ca_types` description, or model the parameter
  separately from the response enum. Keep `CorporateActionCaType` set to whatever the responses
  actually contain.
- If the API is lowercase, change `CorporateActionCaType` to lowercase so it matches the Broker
  `AnnouncementCAType`, and fix the examples.
- In any case, add `Reorg` (or `reorg`) to the Broker enum if the Broker endpoint can return it, or
  explain why only Trading has it. Also fix the example that pairs a `Dividend` type with `DIV` as its
  subtype.

---

## 3. Broker `Disclosures.employment_status`: lowercase in the spec, uppercase in the SDK and docs

**Spec location:** `broker-api.json`, inline enum on the `Disclosures` schema
- Enum: `#/components/schemas/Disclosures/properties/employment_status/enum`. alpaca-py's generator
  promotes it to `DisclosuresEmploymentStatus`.
- `Disclosures` is used by `Account`, `AccountExtended`, `AccountCreationRequest` and
  `AccountUpdateRequest` (`#/components/schemas/<name>/properties/disclosures`). The enum therefore
  applies both to request bodies and to responses.

**Spec values:** `unemployed`, `employed`, `student`, `retired`. The description reads: "One of the
following: `employed`, `unemployed`, `retired`, or `student`."

**SDK legacy values:** `EmploymentStatus` uses `UNEMPLOYED`, `EMPLOYED`, `STUDENT`, `RETIRED`
([`alpaca/broker/enums.py`](../alpaca/broker/enums.py#L130)). The SDK sends these values when
creating and updating accounts, and parses them from account responses
(`alpaca/broker/models/accounts.py`, `Disclosures.employment_status`).

**Evidence:**
- alpaca-py first had lowercase values. Commit `2487c98` (2023-01-16, "fixes employment status
  validation error") changed all four to uppercase. Because the SDK validates responses strictly, the
  likely trigger was the API returning uppercase values, which failed lowercase parsing.
- The [Data Validations](https://docs.alpaca.markets/us/docs/data-validations) guide says
  "`disclosures.employment_status` must be one of the allowed values (e.g. `EMPLOYED`, `UNEMPLOYED`,
  `RETIRED`, `STUDENT`)" and gives a maximum length of 12.
- The [IRA Accounts Overview](https://docs.alpaca.markets/us/docs/ira-accounts-overview) sample
  account-opening body uses `"employment_status": "retired"`. Input may therefore be
  case-insensitive.
- The [Create an Account](https://docs.alpaca.markets/us/reference/createaccount) reference repeats
  the spec's lowercase enum.

**Likely wrong:** the spec. The guides and the SDK's history point to uppercase as the canonical form,
at least in responses. The lowercase IRA sample suggests the server also accepts lowercase input.

**Suggested fix:** change the enum and its description to `UNEMPLOYED`, `EMPLOYED`, `STUDENT`,
`RETIRED`. If lowercase input is still accepted, say so in the description rather than in the enum,
so that generated clients parse responses correctly. Update the IRA guide sample to uppercase for
consistency. Confirm the casing of responses with the accounts service owners.

---

## Impact on alpaca-py

Until the specs are fixed, alpaca-py should not point its deprecation messages for
`CorporateActionType` and `EmploymentStatus` at generated replacements whose values differ. The
generated values would either fail validation on real responses or drop values that users rely on.
`CorporateActionSubType` is not affected for the Broker, because the `unit_split` patch in
`tools/openapi/surfaces/broker/patches.json` keeps the SDK's released spelling.
