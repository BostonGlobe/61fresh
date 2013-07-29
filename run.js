var bignum = require('bignum');
var _ = require("underscore");
var crypto = require('crypto');

var Twit = require('twit')

var T = new Twit({
    consumer_key:         '***REMOVED***'
  , consumer_secret:      '***REMOVED***'
  , access_token:         '***REMOVED***'
  , access_token_secret:  '***REMOVED***'
});

var my_screen_name = "***REMOVED***";


var mysql      = require('mysql');
var sql_conn = mysql.createConnection({
  host     : 'localhost',
  user     : 'root',
  password : 'globelab',
  database : 'condor',
  supportBigNumbers : 'true',
  timezone : 'UTC',
  charset: 'UTF8MB4_UNICODE_CI'
});

sql_conn.on('error', function(err) {
  console.log(err);
});

// Algo ripped from https://github.com/client9/snowflake2time/blob/master/python/snowflake.py
var snowflakeToUTC = function(sf) {
	return bignum(sf).shiftRight(22).add('1288834974657').toNumber(); //  Returned value is in ms
}

var utcToSnowflake = function(utc) {
	return bignum(utc).sub('1288834974657').shiftLeft(22); //  Takes value in ms
}

var snowflakeToSecondsAgo = function(sf) {
	return Math.floor(((new Date).getTime()-snowflakeToUTC(sf))/(1000));
}


var addTweets = function(tweets,memo) {
	if (tweets.length > 0) {
		var tweet_rows = tweets.map(
			function(d) {
				return [d.id_str, d.text, new Date(d.created_at), d.user.id_str];
			});
		sql_conn.query("REPLACE INTO tweets (tweet_id, text, created_at, user_id) VALUES ?", [tweet_rows],
			function (e) {
				if (e) {
					console.log(e);
					console.log(tweet_rows);
				}
			});
		var url_rows = [];
		var hashtag_rows = [];
		var mention_rows = [];
		tweets.forEach(
			function(tweet) {
				tweet.entities.urls.forEach(
					function (url) {
						var url_hash = crypto.createHash('sha1').update(url.expanded_url).digest("hex");
						url_rows.push([url.expanded_url, url_hash, tweet.user.id_str, tweet.id_str, new Date(tweet.created_at)])
					});
				if ('media' in tweet.entities) {
					tweet.entities.media.forEach(
						function (url) {
							var url_hash = crypto.createHash('sha1').update(url.expanded_url).digest("hex");
							url_rows.push([url.expanded_url, url_hash, tweet.user.id_str, tweet.id_str, new Date(tweet.created_at)])
						});
				}
				tweet.entities.hashtags.forEach(
					function (hashtag) {
						hashtag_rows.push([hashtag.text, tweet.user.id_str, tweet.id_str, new Date(tweet.created_at)])
					});
				tweet.entities.user_mentions.forEach(
					function (mention) {
						mention_rows.push([mention.id_str, tweet.user.id_str, tweet.id_str, new Date(tweet.created_at)])
					});
			});
		sql_conn.query("INSERT IGNORE INTO tweeted_urls (url, url_hash, user_id, tweet_id, created_at) VALUES ?", [url_rows],
			function (e) {
				if (e) {
					console.log(e);
					console.log(url_rows);
				}
			});
		sql_conn.query("INSERT IGNORE INTO tweeted_hashtags (hashtag, user_id, tweet_id, created_at) VALUES ?", [hashtag_rows],
			function (e) {
				if (e) {
					console.log(e);
					console.log(hashtag_rows);
				}
			});
		sql_conn.query("INSERT IGNORE INTO tweeted_mentions (mentioned_user_id, user_id, tweet_id, created_at) VALUES ?", [mention_rows],
			function (e) {
				if (e) {
					console.log(e);
					console.log(mention_rows);
				}
			});
	}
}

var search_since_id = '0';

var refreshBoston = function() {
	T.get('search/tweets', {geocode:'42.3583,-71.0603,10mi', result_type: 'recent', count:100, since_id:search_since_id},
		function(err, reply) {
			if (err) {
				console.log("search/tweets");
				console.log(err);
			} else if (reply.statuses.length > 0) {
				// Turns out the Boston geosearch includes tweets from Boston RTed by users from anywhere. THANKS, OBAMA.
				var real_statuses = reply.statuses.map(
					function (d) {
						if (d.retweeted_status !== undefined) {
							return d.retweeted_status;
						} else {
							return d;
						}
					})
					.filter(function(d) {return d.user !== undefined}) // Ideally we'd want to know what sort of tweet doesn't have a user, but for now I'm content with not crashing
				search_since_id = reply.search_metadata.max_id_str;
				sql_conn.query("INSERT IGNORE INTO users (user_id) VALUES ?", [real_statuses.map(function(d) {return [d.user.id_str];})]);
				addTweets(real_statuses,"search");
			}
		})
};


var users_per_fill = 30;
var per_fill_backoff = 10;

var fillLists = function() {
	// var durf = Math.random().toString(36).substring(5);
	// console.log("Start " + durf);
	sql_conn.query("SELECT list_id, COUNT(*) as num FROM users WHERE list_id IS NOT NULL GROUP BY list_id", function(e,r) {
		r.forEach(function(d) {lists_info[d.list_id].members=d.num});
		var target = _.find(lists_info, function(d) {return d.members < 4999;});
		var list_fill_pointer = target.index;
		var num_to_add = Math.min(4999-target.members,users_per_fill);
		sql_conn.query("SELECT user_id FROM users WHERE list_id IS NULL AND suspended = 0 LIMIT ?", num_to_add,
			function (e,r) {
				console.log("Adding " + r.length + " members to list a" + list_fill_pointer + ".");
				if (r.length > 0) {
					var uids = _.pluck(r, 'user_id');
					var params = {owner_screen_name: my_screen_name, slug: 'a'+list_fill_pointer, user_id: uids};
					T.post('lists/members/create_all', params,
						function (err,reply) {
							if (err) {
								console.log('lists/members/create_all');
								// console.log(params);
								console.log(err);
								// console.log("Error " + durf);
								users_per_fill = Math.max(1,users_per_fill-per_fill_backoff);
								setTimeout(fillLists,5000);
							} else {
								sql_conn.query("UPDATE users SET ? WHERE user_id IN (?)",[{list_id:list_fill_pointer},uids],
									function() {
										// console.log("Finish " + durf);
										users_per_fill = Math.min(100,users_per_fill+1);
										setTimeout(fillLists,5000);
									});
							}
						});
				} else {
					setTimeout(fillLists,10000);
				}
			});
	});
}

var lists_info = []

for (var i=0;i < 1000;i++) {
	lists_info.push({index:i,members:0});
}

var current_info;

var occ = false;
var refreshLists = function() {
	if (occ) {
		console.log("occ");
		return;
	}
	occ=true;

	if (current_info === undefined) {
		var l = _.min(lists_info.filter(function(d) {return d.members>4990}),function(d) {return d.since_id||0});
		if (l.index === undefined) {
			console.log("no lists worth refreshing!");
			occ=false;
			return;
		}
		current_info = {list_id:l.index, old_since_id:l.since_id,so_far:0};
		var log_line = "Starting on list a" + current_info.list_id;
		if (current_info.old_since_id !== undefined) 
			log_line += " which was " + snowflakeToSecondsAgo(current_info.old_since_id) + " seconds behind.";
		console.log(log_line);
	}
	var params = {owner_screen_name: my_screen_name, slug: 'a'+current_info.list_id, count:200};
	if (current_info.max_id !== undefined) {
		console.log("Fetching tweets more than " + snowflakeToSecondsAgo(current_info.max_id) + " seconds old.")
		params.max_id = current_info.max_id.toString(); 
	}
	// if (current_info.old_since_id !== undefined) {
	// 	params.since_id = utcToSnowflake(snowflakeToUTC(current_info.old_since_id)-2000).toString();
	// }
	// console.log(params);
	T.get('lists/statuses', params,
			function(err, reply) {
				if (err) {
					console.log('lists/statuses');
					console.log(params);
					console.log(err);
				} else {
					current_info.so_far += reply.length;
					addTweets(reply,'list');
					if (current_info.new_since_id === undefined) {
						current_info.new_since_id = bignum(reply[0].id_str); // Under the circumstances when this code is hit, reply[0] should ("should") exist
					}
					if ((reply.length<190) || (current_info.old_since_id === undefined) || (bignum(_.last(reply).id_str) <= current_info.old_since_id)) {
						// if (reply.length===0) {
						// 	var gap = snowflakeToSecondsAgo(current_info.old_since_id) - snowflakeToSecondsAgo(current_info.max_id);
						// 	console.log("twitter's tapped out... we lost " + gap + "seconds.");
						// }
						console.log("Total grabbed: " + current_info.so_far);
						lists_info[current_info.list_id].since_id = current_info.new_since_id;
						current_info = undefined;
					} else {
						current_info.max_id = bignum(_.last(reply).id_str);
					}
				}
				occ=false;
			});
}

var friends_state = {};
var followers_state = {};

var getRelationshipsUserToUpdate = function(relationship,callback) {
	sql_conn.query("select user_id from users where user_id not in (select user_id from relation_responses where direction=?)", relationship,
		function(err, rows) {
			callback(rows[Math.floor(Math.random()*rows.length)].user_id);
		});
}

var startRelationships = function() {
	if (friends_state.user_id === undefined) {
		getRelationshipsUserToUpdate('friends',function(r) {
			friends_state = {user_id:r, cursor: -1, so_far:[], created_at: new Date};
			finishRelationships('friends',friends_state);
		});
	} else {
		finishRelationships('friends',friends_state);
	}

	if (followers_state.user_id === undefined) {
		getRelationshipsUserToUpdate('followers',function(r) {
			followers_state = {user_id:r, cursor: -1, so_far:[], created_at: new Date};
			finishRelationships('followers',followers_state);
		});
	} else {
		finishRelationships('followers',followers_state);
	}
}

var finishRelationships = function(direction,state) {
	// console.log(state);
	T.get(direction+'/ids', {user_id:state.user_id, cursor:state.cursor},
		function (err,reply) {
			if (err) {
				console.log(direction+'/ids');
				console.log(err);
				delete state.user_id;
			} else {
				state.so_far = state.so_far.concat(reply.ids);
				if (reply.next_cursor_str === "0") {
					sql_conn.query("INSERT INTO relation_responses SET ?",
						{user_id: state.user_id,
						 direction: direction,
						 created_at: state.created_at},
						function(err, result) {
	    					if (err) {
	    						console.log(err);
	    					} else {
	    						var values = state.so_far.map(
									function(d) {
										if (direction==="friends") {
											return [result.insertId, state.user_id, d];
										} else {
											return [result.insertId, d, state.user_id];
										}
									});
	    						sql_conn.query("REPLACE INTO relations (relation_response_id, source_user_id, target_user_id) VALUES ?", [values]);
	    					}
	    					delete state.user_id;
						});
				} else {
					state.cursor = reply.next_cursor_str;
				}
			}
		});
};

var refreshUsers = function() {
	sql_conn.query("select user_id from users order by last_updated asc limit 100",
			function(err, rows) {
				var uids = _.pluck(rows,'user_id');
				T.get('users/lookup', {user_id:_.pluck(rows,'user_id')},
					function(err, reply) {
						if (err) {
							console.log("users/lookup");
							console.log(err);
						} else {
							console.log("Refreshing " + reply.length + " users.");
							uids.forEach(
								function(uid) {
									var d = _.find(reply, function(x) {return uid.toString() === x.id_str});
									var values;
									if (d !== undefined) {
										values = {
											screen_name: d.screen_name,
											friends_count: d.friends_count,
											followers_count: d.followers_count
										};
									} else {
										values = {suspended:1};
									}
									values.last_updated = new Date;
									sql_conn.query("UPDATE users SET ? WHERE user_id = ?",[values, uid]);
								});
						}
					});
			});
};


var refreshBostonTrigger = setInterval(refreshBoston,(15*60*1000)/175);
var refreshListsTrigger = setInterval(refreshLists,(15*60*1000)/179.5);
var relationsTrigger = setInterval(startRelationships,61*1000);
var refreshUsersTrigger = setInterval(refreshUsers,(15*60*1000)/176);
fillLists();
