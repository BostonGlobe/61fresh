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

var redis = require("redis");

var rc = redis.createClient();

rc.on("error", function (err) {
        console.log("Error " + err);
});

var mysql      = require('mysql');
var sql_conn = mysql.createConnection({
  host     : 'localhost',
  user     : 'root',
  password : '',
  database : 'condor',
  supportBigNumbers : 'true',
  timezone : 'UTC'
});

var portUsers = function() {
	rc.smembers('seen_uids',
		function(e,r) {
			// console.log(r);
			sql_conn.query("INSERT IGNORE INTO users (user_id) VALUES ?", [r.map(function(d) {return [d];})], function(err) {
	    		if (err) console.log(err);
			});
		});
};

var list_destroy_pointer = 0;

var destroyLists = function() {
	console.log(list_destroy_pointer);
	var params = {owner_screen_name: my_screen_name, slug: 'a'+list_destroy_pointer};
	T.post('lists/destroy', params,
		function(err, reply) {
			if (err) {
				console.log('lists/destroy');
				console.log(params);
				console.log(err);
			} else {
				list_destroy_pointer++;
				if (list_destroy_pointer === 1000) {
					clearInterval(destroyTrigger);
				}
			}
		});
};

var list_create_pointer = 0;

var createLists = function() {
	console.log(list_create_pointer);
	var params = {name: 'a'+list_create_pointer, mode:'private'};
	T.post('lists/create', params,
		function(err, reply) {
			if (err) {
				console.log('lists/create');
				console.log(params);
				console.log(err);
			} else {
				list_create_pointer++;
				if (list_create_pointer === 1000) {
					clearInterval(createTrigger);
				}
			}
		});
};

var destroyTrigger = setInterval(destroyLists,(15*60*1000)/175);
var createTrigger = setInterval(createLists,(15*60*1000)/175);
