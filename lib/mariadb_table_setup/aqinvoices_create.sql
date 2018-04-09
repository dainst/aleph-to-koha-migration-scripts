USE koha_mapping_db;

CREATE TABLE `aqinvoices` (
  `invoiceid` int(11) NOT NULL AUTO_INCREMENT,
  `invoicenumber` mediumtext COLLATE utf8_unicode_ci NOT NULL,
  `booksellerid` int(11) NOT NULL,
  `shipmentdate` date DEFAULT NULL,
  `billingdate` date DEFAULT NULL,
  `closedate` date DEFAULT NULL,
  `shipmentcost` decimal(28,6) DEFAULT NULL,
  `shipmentcost_budgetid` int(11) DEFAULT NULL,
  `message_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`invoiceid`),
  KEY `aqinvoices_fk_aqbooksellerid` (`booksellerid`),
#  KEY `edifact_msg_fk` (`message_id`),
  KEY `aqinvoices_fk_shipmentcost_budgetid` (`shipmentcost_budgetid`),
  CONSTRAINT `aqinvoices_fk_aqbooksellerid` FOREIGN KEY (`booksellerid`) REFERENCES `aqbooksellers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `aqinvoices_fk_shipmentcost_budgetid` FOREIGN KEY (`shipmentcost_budgetid`) REFERENCES `aqbudgets` (`budget_id`) ON DELETE SET NULL ON UPDATE CASCADE #,
#  CONSTRAINT `edifact_msg_fk` FOREIGN KEY (`message_id`) REFERENCES `edifact_messages` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci