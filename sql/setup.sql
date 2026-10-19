-- Run in a Snowflake worksheet with a role allowed to create these objects.
-- Uses a small warehouse; pause it when finished to control credits.
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_KEMI;
CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_KEMI.PUBLIC;
CREATE TABLE IF NOT EXISTS SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS (
  EVENT_ID VARCHAR, EVENT_TIME TIMESTAMP_NTZ, SEVERITY VARCHAR,
  CATEGORY VARCHAR, SOURCE VARCHAR, DESCRIPTION VARCHAR
);
INSERT INTO SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS
SELECT column1, TO_TIMESTAMP_NTZ(column2), column3, column4, column5, column6
FROM VALUES
 ('EVT-001','2026-10-19 09:00:00','high','authentication','identity','Repeated failed login attempts'),
 ('EVT-002','2026-10-19 09:05:00','medium','network','firewall','Unusual outbound connections'),
 ('EVT-003','2026-10-19 09:10:00','low','endpoint','agent','Software update completed'),
 ('EVT-004','2026-10-19 09:15:00','critical','authentication','identity','Privileged account anomalous login'),
 ('EVT-005','2026-10-19 09:20:00','medium','endpoint','agent','Unexpected executable detected'),
 ('EVT-006','2026-10-19 09:25:00','high','network','firewall','Repeated blocked connections')
WHERE NOT EXISTS (SELECT 1 FROM SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS);
SELECT COUNT(*) AS EVENT_COUNT FROM SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS;
