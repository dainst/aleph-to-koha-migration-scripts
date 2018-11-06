SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE aqbasket;
TRUNCATE TABLE aqbasketgroups;
TRUNCATE TABLE aqbooksellers;
TRUNCATE TABLE aqbudgetperiods;
TRUNCATE TABLE aqbudgets;
TRUNCATE TABLE aqcontacts;
TRUNCATE TABLE aqinvoices;
TRUNCATE TABLE aqorders;
TRUNCATE TABLE aqorders_items;
TRUNCATE TABLE serial;
TRUNCATE TABLE serialitems;
TRUNCATE TABLE subscription;
TRUNCATE TABLE subscription_numberpatterns;
TRUNCATE TABLE subscription_frequencies;

SET FOREIGN_KEY_CHECKS = 1;
