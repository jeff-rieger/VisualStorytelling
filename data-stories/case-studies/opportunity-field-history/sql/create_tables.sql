-- ============================================================
--  Opportunity Field History — Snowflake DDL
--  Case study: Opportunity Field History (Visual Storytelling)
--
--  Run these three CREATE TABLE statements in order before
--  loading data.  Foreign keys are declared for documentation;
--  Snowflake defines but does not enforce FK constraints.
--
--  Recommended COPY INTO options when loading from a CSV stage:
--    FILE_FORMAT = (
--        TYPE             = CSV
--        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
--        SKIP_HEADER      = 1
--        DATE_FORMAT      = 'YYYY-MM-DD'
--        EMPTY_FIELD_AS_NULL = TRUE   -- converts empty old_value → NULL
--        NULL_IF          = ('')
--    )
-- ============================================================


-- ────────────────────────────────────────────────────────────
--  1. ACCOUNTS
--     One row per company (parent and child accounts).
--     Parent/child relationship is self-referencing via
--     PARENT_ACCOUNT_ID (NULL for top-level accounts).
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ACCOUNTS (

    ACCOUNT_ID           VARCHAR(10)    NOT NULL   COMMENT 'Surrogate key — format ACC-NNNN',
    ACCOUNT_NAME         VARCHAR(100)   NOT NULL   COMMENT 'Full legal name of the account',
    INDUSTRY             VARCHAR(20)    NOT NULL   COMMENT 'Top-level industry: Healthcare | Government | Retail | Customer Service',
    SUBCATEGORY          VARCHAR(50)    NOT NULL   COMMENT 'Specific segment within the industry (e.g. Grocery, Health System, Contact Center)',
    ANNUAL_REVENUE       NUMBER(15, 0)  NOT NULL   COMMENT 'Annual revenue in USD, whole dollars',
    NUMBER_OF_EMPLOYEES  NUMBER(7, 0)   NOT NULL   COMMENT 'Full-time-equivalent headcount',
    PARENT_ACCOUNT_ID    VARCHAR(10)               COMMENT 'Self-referencing FK; NULL for top-level accounts',
    STREET_ADDRESS       VARCHAR(100)   NOT NULL   COMMENT 'Street line of mailing address',
    CITY                 VARCHAR(50)    NOT NULL,
    STATE                VARCHAR(2)     NOT NULL   COMMENT 'US two-letter state/territory code',
    ZIP_CODE             VARCHAR(10)    NOT NULL   COMMENT 'Stored as VARCHAR to preserve leading zeros',
    LATITUDE             FLOAT          NOT NULL   COMMENT 'WGS-84 decimal degrees',
    LONGITUDE            FLOAT          NOT NULL   COMMENT 'WGS-84 decimal degrees',

    CONSTRAINT PK_ACCOUNTS
        PRIMARY KEY (ACCOUNT_ID),

    CONSTRAINT FK_ACCOUNTS_PARENT
        FOREIGN KEY (PARENT_ACCOUNT_ID)
        REFERENCES ACCOUNTS (ACCOUNT_ID)

)
COMMENT = 'Company accounts — both parent (enterprise) and child (division) records';


-- ────────────────────────────────────────────────────────────
--  2. OPPORTUNITIES
--     Sales opportunities linked to accounts.
--     STATUS: Open | Won | Lost
--     STAGE:  1 - Prospecting | 2 - Scoping | 3 - Engaged |
--             4 - Proposal    | 5 - Negotiation |
--             6 - Closed Won  | 7 - Closed Lost
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS OPPORTUNITIES (

    OPPORTUNITY_ID    VARCHAR(10)    NOT NULL   COMMENT 'Surrogate key — format OPP-NNNNN',
    OPPORTUNITY_NAME  VARCHAR(200)   NOT NULL   COMMENT 'Account name + product/service description',
    ACCOUNT_ID        VARCHAR(10)    NOT NULL   COMMENT 'FK to ACCOUNTS',
    AMOUNT            NUMBER(15, 0)  NOT NULL   COMMENT 'Deal value in USD, rounded to nearest $1,000',
    CREATED_DATE      DATE           NOT NULL   COMMENT 'Date the opportunity was created',
    CLOSE_DATE        DATE           NOT NULL   COMMENT 'Current (final) targeted close date',
    STATUS            VARCHAR(10)    NOT NULL   COMMENT 'Open | Won | Lost',
    STAGE             VARCHAR(20)    NOT NULL   COMMENT 'Current pipeline stage label (see table comment)',
    PROBABILITY       NUMBER(3, 0)   NOT NULL   COMMENT 'Win probability % implied by stage: 10/15/25/60/80/100/0',

    CONSTRAINT PK_OPPORTUNITIES
        PRIMARY KEY (OPPORTUNITY_ID),

    CONSTRAINT FK_OPPORTUNITIES_ACCOUNT
        FOREIGN KEY (ACCOUNT_ID)
        REFERENCES ACCOUNTS (ACCOUNT_ID)

)
COMMENT = 'Sales opportunities; one row per deal. STAGE and STATUS reflect the final (current) state. Full edit history is in OPPORTUNITY_FIELD_HISTORY.';


-- ────────────────────────────────────────────────────────────
--  3. OPPORTUNITY_FIELD_HISTORY
--     Salesforce-style audit log of every field change on an
--     opportunity.  FIELD values: StageName | CloseDate | Amount
--
--     Creation events (when the opp is first saved) have
--     OLD_VALUE = NULL.  Subsequent edits carry both OLD_VALUE
--     and NEW_VALUE.  All three tracked fields produce a
--     creation row, so every opportunity has exactly 3 rows
--     with OLD_VALUE IS NULL.
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS OPPORTUNITY_FIELD_HISTORY (

    HISTORY_ID        VARCHAR(15)    NOT NULL   COMMENT 'Surrogate key — format HIST-NNNNNNN',
    OPPORTUNITY_ID    VARCHAR(10)    NOT NULL   COMMENT 'FK to OPPORTUNITIES',
    FIELD             VARCHAR(20)    NOT NULL   COMMENT 'Name of the changed field: StageName | CloseDate | Amount',
    OLD_VALUE         VARCHAR(100)              COMMENT 'Value before the change; NULL on creation events',
    NEW_VALUE         VARCHAR(100)   NOT NULL   COMMENT 'Value after the change',
    CREATED_DATE      DATE           NOT NULL   COMMENT 'Date the change was saved',
    CREATED_BY        VARCHAR(50)    NOT NULL   COMMENT 'Full name of the user who made the change',

    CONSTRAINT PK_OPPORTUNITY_FIELD_HISTORY
        PRIMARY KEY (HISTORY_ID),

    CONSTRAINT FK_OFH_OPPORTUNITY
        FOREIGN KEY (OPPORTUNITY_ID)
        REFERENCES OPPORTUNITIES (OPPORTUNITY_ID)

)
COMMENT = 'Audit log of field-level changes to opportunities, modelled after Salesforce OpportunityFieldHistory. Query pattern: filter by OPPORTUNITY_ID + FIELD, order by CREATED_DATE ASC to reconstruct the change timeline.';
