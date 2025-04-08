INSERT INTO wptq_tripster_links (
  post_id,
  post_title,
  link_type,
  exp_id,
  exp_title,
  exp_url,
  status,
  inactivity_reason,
  is_unknown_type
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
  post_title = VALUES(post_title),
  status = VALUES(status),
  inactivity_reason = VALUES(inactivity_reason),
  is_unknown_type = VALUES(is_unknown_type);