
SET SQL_SAFE_UPDATES = 0;

# Setze überall quantityreceived = quantity wo es eine invoice id gibt, sorgt für ("erh." Anzeige).
UPDATE `aqorders` SET `quantityreceived` = quantity WHERE `invoiceid` IS NOT NULL;

# Setze closedate auf null in baskets mit standing order, damit im Interface wieder die Optionen angezeigt werden.
SET SQL_SAFE_UPDATES = 0;
UPDATE `aqbasket` SET `closedate` = null WHERE `is_standing` = 1;

# Bestellstatus auf complete/partial für alle standing order
UPDATE `aqorders` SET `orderstatus` = 'complete' WHERE `invoiceid` IS NOT NULL AND parent_ordernumber != ordernumber;
UPDATE `aqorders` SET `orderstatus` = 'partial' WHERE `invoiceid` IS NOT NULL AND parent_ordernumber = ordernumber;

# "Zugegangen Datum" basierend auf Rechnung setzen
UPDATE `aqorders`, `aqinvoices` SET `aqorders`.`datereceived` = `aqinvoices`.`closedate` WHERE `aqorders`.`invoiceid` = `aqinvoices`.`invoiceid`;
SET SQL_SAFE_UPDATES = 1;

# Zusätzliche numberpatterns
INSERT INTO subscription_numberpatterns
(`label`, `displayorder`, `description`, `numberingmethod`, `label1`, `add1`, `every1`, `whenmorethan1`, `setto1`, `numbering1`, `label2`, `add2`, `every2`, `whenmorethan2`, `setto2`, `numbering2`, `label3`, `add3`, `every3`, `whenmorethan3`, `setto3`, `numbering3`) 
VALUES
	('{Band Fortlaufend}{Jahr} {Heft}, alle 2 Monate', '1', '_alle 2Monate.6 Hefte im Jahr.Fortlaufende Zählung', '{Y}, {Z}  ({X})', 'Jahr', '1', '6', '99999', '0', '', 'Band', '1', '6', '99999', '0', '', 'Heft', '1', '1', '6', '1', ''),
	('{Band Fortlaufend}{Jahr} {Heft}, alle 4 Monate', '1', '_alle 4 Monate.3 Hefte im Jahr.Fortlaufende Zählung', '{Y}, {Z}  ({X})', 'Jahr', '1', '3', '99999', NULL, NULL, 'Band', '1', '3', '99999', NULL, NULL, 'Heft', '1', '1', '3', '1', NULL),
	('{Band Fortlaufend}{Jahr} {Heft}, halbjährlich', '1', '_Halbjährlich. Fortlaufende Zählung', '{Y} ({X}),{Z}', 'Jahr', '1', '2', '99999', NULL, NULL, 'Band', '1', '2', '9999', NULL, NULL, 'Heft', '1', '1', '2', '1', NULL),
	('{Band Fortlaufend}{Jahr} {Heft}, alle 3 Monate', '1', '_alle 3 Monate.4 Hefte im Jahr.Fortlaufende Zählung', '{Y}, {Z}  ({X})', 'Jahr', '1', '4', '99999', NULL, NULL, 'Band', '1', '4', '99999', NULL, NULL, 'Heft', '1', '1', '4', '1', NULL),
	('{Band Fortlaufend} ({Jahr}),{Heft}, monatlich', '1', '_Monatlich.Fortlaufende Zählung', '{Y} ({X}),{Z}', 'Jahr', '1', '12', '99999', NULL, NULL, 'Band', '1', '12', '9999', NULL, NULL, 'Heft', '1', '1', '12', '1', NULL)
;
