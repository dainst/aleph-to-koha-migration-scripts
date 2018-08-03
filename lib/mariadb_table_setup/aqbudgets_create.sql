USE koha_mapping_db;

CREATE TABLE `aqbudgets` (
  `budget_id` int(11) NOT NULL AUTO_INCREMENT,
  `budget_parent_id` int(11) DEFAULT NULL,
  `budget_code` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `budget_name` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
  `budget_branchcode` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `budget_amount` decimal(28,6) DEFAULT 0.000000,
  `budget_encumb` decimal(28,6) DEFAULT 0.000000,
  `budget_expend` decimal(28,6) DEFAULT 0.000000,
  `budget_notes` mediumtext COLLATE utf8_unicode_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `budget_period_id` int(11) DEFAULT NULL,
  `sort1_authcat` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
  `sort2_authcat` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
  `budget_owner_id` int(11) DEFAULT NULL,
  `budget_permission` int(1) DEFAULT 0,
  PRIMARY KEY (`budget_id`),
  KEY `budget_parent_id` (`budget_parent_id`),
  KEY `budget_code` (`budget_code`),
  KEY `budget_branchcode` (`budget_branchcode`),
  KEY `budget_period_id` (`budget_period_id`),
  KEY `budget_owner_id` (`budget_owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;