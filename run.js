var bignum = require('bignum');
var _ = require("underscore");

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
  password : '',
  database : 'condor',
  supportBigNumbers : 'true',
  timezone : 'UTC'
});

sql_conn.on('error', function(err) {
  console.log(err);
});

// Algo ripped from https://github.com/client9/snowflake2time/blob/master/python/snowflake.py
var snowflakeToUTC = function(sf) {
	return bignum(sf).shiftRight(22).add('1288834974657'); //  Returned value is in ms
}

var utcToSnowflake = function(utc) {
	return bignum(utc).sub('1288834974657').shiftLeft(22); //  Takes value in ms
}

var snowflakeToSecondsAgo = function(sf) {
	return Math.floor(((new Date).getTime()-snowflakeToUTC(sf))/(1000));
}

var addTweets = function(tweets,memo) {
	var values = tweets.map(
		function(d) {
			return [d.id_str, d.text, new Date(d.created_at), d.user.id_str];
		});
	sql_conn.query("REPLACE INTO tweets (tweet_id, text, created_at, user_id) VALUES ?", [values], function(err) {
	    if (err) console.log(err);
	});
}

var search_since_id = '0';

var refreshBoston = function() {
	T.get('search/tweets', {geocode:'42.3583,-71.0603,10mi', result_type: 'recent', count:100, since_id:search_since_id},
		function(err, reply) {
			if (err) {
				console.log("search/tweets");
				console.log(err);
			} else if (reply.statuses.length > 0) {
				search_since_id = reply.search_metadata.max_id_str;
				sql_conn.query("INSERT IGNORE INTO users (user_id) VALUES ?", [reply.statuses.map(function(d) {return [d.user.id_str];})]);
				addTweets(reply.statuses,"search");
			}
		})
};

var lists_info = []

for (var i=0;i < 1000;i++) {
	lists_info.push({index:i,since_id:0,timestamp:0,members:0});
}

var users_per_fill = 30;
var per_fill_backoff = 10;

var fillLists = function() {
	// var durf = Math.random().toString(36).substring(5);
	// console.log("Start " + durf);
	sql_conn.query("SELECT list_id, COUNT(*) as num FROM users WHERE list_id IS NOT NULL GROUP BY list_id", function(e,r) {
		r.forEach(function(d) {lists_info[d.list_id].members=d.num});
		var target = _.find(lists_info, function(d) {return d.members < 5000;});
		var list_fill_pointer = target.index;
		var num_to_add = Math.min(5000-target.members,users_per_fill);
		sql_conn.query("SELECT user_id FROM users WHERE list_id IS NULL LIMIT ?", num_to_add,
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


var refreshLists = function() {
	var l = _.min(lists_info.filter(function(d) {return d.members===5000}),function(d) {return d.timestamp});
	// var l = lists_info[0];
	var params = {owner_screen_name: my_screen_name, slug: 'a'+l.index, count:200};
	if (l.since_id > 0) {
		params.since_id = l.since_id.toString();
	}
	T.get('lists/statuses', params,
			function(err, reply) {
				if (err) {
					console.log('lists/statuses');
					console.log(params);
					console.log(err);
				} else if (reply.length > 0) {
					var new_since_id = bignum(reply[0].id_str);
					console.log("List a" + l.index + " was " + snowflakeToSecondsAgo(l.since_id) + " seconds behind, now " + snowflakeToSecondsAgo(new_since_id) + ". (" + reply.length + ")")
					lists_info[l.index].timestamp = snowflakeToUTC(new_since_id);
					lists_info[l.index].since_id = new_since_id;
					addTweets(reply,'list');
				} else {
					console.log("List a" + l.index + " gave us nothing.");
					lists_info[l.index].timestamp = (new Date).getTime();
				}
			});
}

var friends_state = {};
var followers_state = {};

var getRandomUser = function(callback) {
	sql_conn.query("SELECT COUNT(*) as num FROM users",
		function(err, rows) {
			sql_conn.query("SELECT user_id FROM users limit ?,1",Math.floor(Math.random()*rows[0].num),
				function(err, rows) {
					callback(rows[0].user_id);
				});
		});
}

var startRelationships = function() {
	if (friends_state.user_id === undefined) {
		getRandomUser(function(r) {
			friends_state = {user_id:r, cursor: -1, so_far:[], created_at: new Date};
			finishRelationships('friends',friends_state);
		});
	} else {
		finishRelationships('friends',friends_state);
	}

	if (followers_state.user_id === undefined) {
		getRandomUser(function(r) {
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
						 response: JSON.stringify(state.so_far),
						 created_at: state.created_at},
						function(err) {
	    					if (err) console.log(err);
						});
					delete state.user_id;
				} else {
					state.cursor = reply.next_cursor_str;
				}
			}
		});
};

var refreshBostonTrigger = setInterval(refreshBoston,(15*60*1000)/175);
var refreshListsTrigger = setInterval(refreshLists,(15*60*1000)/179);
var relationsTrigger = setInterval(startRelationships,61*1000);
fillLists();
