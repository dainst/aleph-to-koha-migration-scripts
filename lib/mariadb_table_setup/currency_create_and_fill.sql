USE koha_mapping_db;

CREATE TABLE `currency` (
  `currency` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `symbol` varchar(5) COLLATE utf8_unicode_ci DEFAULT NULL,
  `isocode` varchar(5) COLLATE utf8_unicode_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `rate` float(15,5) DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `archived` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`currency`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

INSERT INTO `currency`
(`currency`, `symbol`, `isocode`, `rate`, `active`)
VALUES
('AUD','$A','AUD',1.56200,0),
('BGN','лв','BGN',1.95580,0),
('CAD','$C','CAD',1.50720,0),
('CHF','Fr.','CHF',1.17040,0),
('CNY','CN¥','CNY',7.77290,0),
('DKK','dkr.','DKK',7.44170,0),
('EGP','E£','EGP',20.93340,0),
('EUR','€','EUR',1.00000,1),
('GBP','£','GBP',0.87525,0),
('ILS','₪','ILS',4.13430,0),
('JPY','¥','JPY',133.25999,0),
('NOK','nkr','NOK',9.76650,0),
('RUB','₽','RUB',69.65110,0),
('SEK','Skr','SEK',9.97700,0),
('TRY','₺','TRY',4.51650,0),
('USD','$','USD',1.17420,0);

