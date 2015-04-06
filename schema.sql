# Dump of table domains
# ------------------------------------------------------------

CREATE TABLE `domains` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `domain_set` varchar(255) DEFAULT NULL,
  `domain` varchar(255) DEFAULT NULL,
  `subset` char(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `set_domain` (`domain_set`,`domain`),
  KEY `domain` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tweeted_hashtags
# ------------------------------------------------------------

CREATE TABLE `tweeted_hashtags` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `hashtag` varchar(255) DEFAULT NULL,
  `user_id` bigint(64) DEFAULT NULL,
  `tweet_id` bigint(64) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hashtag` (`hashtag`,`tweet_id`),
  KEY `hashtag_2` (`hashtag`),
  KEY `tweet_id` (`tweet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tweeted_mentions
# ------------------------------------------------------------

CREATE TABLE `tweeted_mentions` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `mentioned_user_id` bigint(64) DEFAULT NULL,
  `user_id` bigint(64) DEFAULT NULL,
  `tweet_id` bigint(64) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mentioned_user_id` (`mentioned_user_id`,`tweet_id`),
  KEY `mentioned_user_id_2` (`mentioned_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tweeted_urls
# ------------------------------------------------------------

CREATE TABLE `tweeted_urls` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `url` text,
  `user_id` bigint(64) DEFAULT NULL,
  `tweet_id` bigint(64) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `url_hash` varchar(255) DEFAULT NULL,
  `real_url` text,
  `real_url_hash` varchar(255) DEFAULT NULL,
  `domain` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_hash` (`url_hash`,`tweet_id`),
  KEY `url_hash_2` (`url_hash`),
  KEY `real_url_hash` (`real_url_hash`),
  KEY `created_at` (`created_at`),
  KEY `created_at_2` (`created_at`,`real_url_hash`),
  KEY `user_id` (`user_id`),
  KEY `real_url_hash_2` (`real_url_hash`,`user_id`),
  KEY `real_url_hash_3` (`real_url_hash`,`user_id`,`tweet_id`,`created_at`),
  KEY `domain` (`domain`),
  KEY `real_url` (`real_url`(150)),
  KEY `created_at_3` (`created_at`,`real_url_hash`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tweets
# ------------------------------------------------------------

CREATE TABLE `tweets` (
  `tweet_id` bigint(64) unsigned NOT NULL,
  `text` varchar(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  `created_at` datetime NOT NULL,
  `user_id` bigint(64) unsigned NOT NULL,
  `retweeted_tweet_id` bigint(64) DEFAULT NULL,
  PRIMARY KEY (`tweet_id`),
  KEY `created_at` (`created_at`),
  KEY `user_id` (`user_id`),
  FULLTEXT KEY `text` (`text`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table url_info
# ------------------------------------------------------------

CREATE TABLE `url_info` (
  `real_url_hash` varchar(255) NOT NULL DEFAULT '',
  `embedly_blob` mediumtext,
  `topic_blob` text,
  `sports_score` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`real_url_hash`),
  FULLTEXT KEY `embedly_blob` (`embedly_blob`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table users
# ------------------------------------------------------------

CREATE TABLE `users` (
  `user_id` bigint(64) unsigned NOT NULL,
  `list_id` int(11) DEFAULT NULL,
  `screen_name` varchar(255) DEFAULT NULL,
  `friends_count` int(11) DEFAULT NULL,
  `followers_count` int(11) DEFAULT NULL,
  `last_updated` datetime DEFAULT NULL,
  `suspended` tinyint(4) NOT NULL DEFAULT '0',
  `source` varchar(255) NOT NULL DEFAULT 'geo',
  `name` varchar(255) DEFAULT NULL,
  `profile_image_url` text,
  `home_domain` varchar(255) DEFAULT NULL,
  `home_domain_percent` int(11) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  KEY `list_id` (`list_id`),
  KEY `last_updated` (`last_updated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
