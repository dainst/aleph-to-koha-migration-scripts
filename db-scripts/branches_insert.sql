DROP TABLE IF EXISTS `koha_zenon`.`branches`;
CREATE TABLE `koha_zenon`.`branches` ( -- information about your libraries or branches are stored here
  `branchcode` varchar(10) NOT NULL default '', -- a unique key assigned to each branch
  `branchname` mediumtext NOT NULL, -- the name of your library or branch
  `branchaddress1` mediumtext, -- the first address line of for your library or branch
  `branchaddress2` mediumtext, -- the second address line of for your library or branch
  `branchaddress3` mediumtext, -- the third address line of for your library or branch
  `branchzip` varchar(25) default NULL, -- the zip or postal code for your library or branch
  `branchcity` mediumtext, -- the city or province for your library or branch
  `branchstate` mediumtext, -- the state for your library or branch
  `branchcountry` text, -- the county for your library or branch
  `branchphone` mediumtext, -- the primary phone for your library or branch
  `branchfax` mediumtext, -- the fax number for your library or branch
  `branchemail` mediumtext, -- the primary email address for your library or branch
  `branchreplyto` mediumtext, -- the email to be used as a Reply-To
  `branchreturnpath` mediumtext, -- the email to be used as Return-Path
  `branchurl` mediumtext, -- the URL for your library or branch's website
  `issuing` tinyint(4) default NULL, -- unused in Koha
  `branchip` varchar(15) default NULL, -- the IP address for your library or branch
  `branchprinter` varchar(100) default NULL, -- unused in Koha
  `branchnotes` mediumtext, -- notes related to your library or branch
  opac_info text, -- HTML that displays in OPAC
  `geolocation` VARCHAR(255) default NULL, -- geolocation of your library
  PRIMARY KEY (`branchcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

INSERT INTO `koha_zenon`.`branches`
(`branchcode`, 
`branchname`,
`branchaddress1`,
`branchaddress2`,
`branchaddress3`,
`branchzip`,
`branchcity`,
`branchstate`,
`branchcountry`,
`branchphone`,
`branchfax`,
`branchemail`,
`branchreplyto`,
`branchreturnpath`,
`branchurl`,
`issuing`,
`branchip`,
`branchprinter`,
`branchnotes`,
`opac_info`,
`geolocation`)
VALUES
('BASSM','Archäologische Staatssammlung, Museum für Vor- und Frühgeschichte, München',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,null),
('BBSA','Bibliothek der British School at Athens','Odos Souedias 52','','','10676','Athen','','Griechenland','','','','','','',NULL,'',NULL,'','',null),
('BIAUL','Institut Archeologii der Uniwersytet Marii Curie-Sklodowskiej, Lublin ',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,null),
('BICUAZ','Bibliothek des International Centre for Underwater Archaeology Zadar',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,null),
('BLDMV','Landesamt für Denkmalpflege Mecklenburg-Vorpommern ',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,null),
('BWINCK','Bibliothek der Winckelmann-Gesellschaft, Stendal',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,null),
('DAIA','DAI Athen','Odos Fidiou 1','','','10678','Athen','','Griechenland','','','','','','',NULL,'',NULL,'','',null),
('DAIB','DAI KAAK, Bonn','Dürenstr. 35-37','','','53173','Bonn','Nordrhein-Westfalen','Deutschland','','','','','','',NULL,'',NULL,'','',null),
('DAID','DAI, Außenstelle Damaskus','8, Malki Street ','POB 11870','','','Damaskus ','','Syrien','','','','','','',NULL,'',NULL,'','',null),
('DAIE','DAI Eurasien-Abteilung','Im Dol 2-6','','','14195','Berlin','Berlin','Deutschland','','','','','','',NULL,'',NULL,'','',null),
('DAIF','DAI RGK, Frankfurt am Main','Palmengartenstraße 10-12 ','','','60325','Frankfurt a.M.','Hessen','Deutschland','','','','','','',NULL,'',NULL,'','',null),
('DAIG','DAI Gesamt E','','','','','','','','','','','','','',NULL,'',NULL,'','',null),
('DAII','DAI Istanbul','Inönü Caddesi 10','','','34437','Istanbul','','Türkei','','','','','','',NULL,'',NULL,'','',null),
('DAIK','DAI Kairo','31, Abu el Feda','','','11211 ','Kairo - Zamalek ','','Ägypten ','','','','','','',NULL,'',NULL,'','',null),
('DAIM','DAI Madrid','Calle Serrano, 159','','','28002','Madrid','','Spanien','','','','','','',NULL,'',NULL,'','',null),
('DAIO','DAI Orient-Abteilung','Podbielskiallee 69-71','','','14195 ','Berlin ','Berlin','Deutschland','','','','','','',NULL,'',NULL,'','',null),
('DAIP','DAI, Außenstelle Peking','','','','','','','','','','','','','',NULL,'',NULL,'','',null),
('DAIR','DAI Rom','Via Valadier, 37','','','00193 ','Rom ','','Italien','','','','','','',NULL,'',NULL,'','',null),
('DAIS','DAI, Außenstelle Sanaa','Embassy of the Federal Republic of Germany,  Bibliothek ','POB 2562 ','','','Sanaa','','Jemen','','','','','','',NULL,'',NULL,'','',null),
('DAIT','DAI, Außenstelle Teheran','','','','','','','','','','','','','',NULL,'',NULL,'','',null),
('DAIZ','DAI Zentrale','Podbielskiallee 69-71','','','14195','Berlin','Berlin','Deutschland','','','','','','',NULL,'',NULL,'','<p>zenon.dainst.org</p>',null),
('DEIA','DEI Amman','Forschungsstelle Amman, Deutsches Evangelisches Institut für Altertumswissenschaft des Heiligen Landes (DEI), zugleich Forschungsstelle des Deutschen Archäologischen Instituts','P.O. Box 183 ','','11118 ','Amman','','Jordanien','','','','','','',NULL,'',NULL,'','',null),
('DEIJ','DEI Jerusalem',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,null);


