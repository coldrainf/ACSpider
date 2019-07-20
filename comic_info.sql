/*
Navicat MySQL Data Transfer

Source Server         : localhost_3306
Source Server Version : 50724
Source Host           : localhost:3306
Source Database       : coldrain

Target Server Type    : MYSQL
Target Server Version : 50724
File Encoding         : 65001

Date: 2019-07-20 10:48:20
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for comic_info
-- ----------------------------
DROP TABLE IF EXISTS `comic_info`;
CREATE TABLE `comic_info` (
  `cid` int(11) NOT NULL,
  `cname` varchar(255) DEFAULT NULL,
  `cslug` varchar(100) DEFAULT NULL,
  `ccover` varchar(255) DEFAULT NULL,
  `clastname` varchar(255) DEFAULT NULL,
  `cauthor` varchar(255) DEFAULT NULL,
  `cserialise` tinyint(1) DEFAULT NULL,
  `ctype` varchar(255) DEFAULT NULL,
  `ccategory` varchar(25) DEFAULT NULL,
  `carea` varchar(15) DEFAULT NULL,
  `cupdate` varchar(255) DEFAULT NULL,
  `cchapters` text,
  `cchapterurl` text,
  PRIMARY KEY (`cid`),
  KEY `cslug` (`cslug`),
  KEY `cid` (`cid`,`clastname`),
  KEY `cname` (`cname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
