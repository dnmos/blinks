CREATE TABLE `wptq_tripster_links` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `post_id` VARCHAR(255) NOT NULL,
  `post_title` VARCHAR(255) NOT NULL,
  `link_type` ENUM('widget', 'deeplink') NOT NULL,
  `exp_id` VARCHAR(255) NULL,
  `exp_title` VARCHAR(255) NULL,
  `exp_url` VARCHAR(255) NULL,
  `link_status` ENUM('active', 'inactive') NOT NULL,
  `inactivity_reason` VARCHAR(255) NULL,
  `is_unknown_type` BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE KEY `unique_link` (`post_id`, `link_type`, `exp_id`, `exp_url`)
);