nohup python27 -u geo_search_to_queue.py &
nohup python27 -u list_statuses_to_queue.py &

nohup python27 -u tweet_queue_to_sql.py &
nohup python27 -u user_queue_to_sql.py &
