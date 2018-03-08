USE koha_mapping_db;

CREATE TABLE `aqbudgetperiods` (
  `budget_period_id` int(11) NOT NULL AUTO_INCREMENT,
  `budget_period_startdate` date NOT NULL,
  `budget_period_enddate` date NOT NULL,
  `budget_period_active` tinyint(1) DEFAULT 0,
  `budget_period_description` mediumtext COLLATE utf8_unicode_ci DEFAULT NULL,
  `budget_period_total` decimal(28,6) DEFAULT NULL,
  `budget_period_locked` tinyint(1) DEFAULT NULL,
  `sort1_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `sort2_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`budget_period_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

INSERT INTO `aqbudgetperiods`
(`budget_period_id`, `budget_period_startdate`, `budget_period_enddate`, `budget_period_active`, `budget_period_description`, `budget_period_total`, `budget_period_locked`, `sort1_authcat`, `sort2_authcat`)
VALUES
(1,'1990-01-01','2017-12-31',0,'ALEPH Altdaten',0.0,1,NULL,NULL),
(2,'2018-01-01','2018-12-31',1,'2018DAIM, Gesamtetat Madrid',0.000000,NULL,NULL,NULL),
(3,'2018-01-01','2018-12-31',1,'2018DAIO, Gesamtetat OA, Damaskus, Sanaa',0.000000,0,NULL,NULL),
(4,'2018-01-01','2018-12-31',1,'2018DAIF, Gesamtetat RGK',0.000000,NULL,NULL,NULL),
(5,'2018-01-01','2018-12-31',1,'2018DAIR, Gesamtetat Rom',0.000000,NULL,NULL,NULL),
(6,'2018-01-01','2018-12-31',1,'2018DAIZ, Gesamtetat Zentrale',0.000000,NULL,NULL,NULL),
(7,'2018-01-01','2018-12-31',1,'2018DAIB, Gesamtetat KAAK',0.000000,NULL,NULL,NULL),
(8,'2018-01-01','2018-12-31',1,'2018DAIE, Gesamtetat Eurasien-Abt.',0.000000,0,NULL,NULL),
(9,'2018-01-01','2018-12-31',1,'2018DAIA, Gesamtetat Athen',0.000000,NULL,NULL,NULL),
(10,'2018-01-01','2018-12-31',1,'2018DAIK, Gesamtetat Kairo',0.000000,NULL,NULL,NULL),
(11,'2018-01-01','2018-12-31',1,'2018DAII, Gesamtetat Istanbul',0.000000,NULL,NULL,NULL),
(12,'2018-01-01','2018-12-31',1,'2018DAIEP, Gesamtetat Elektronische Publikationen',0.000000,NULL,NULL,NULL);
