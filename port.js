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


var destroyAllLists = function() {
	var listsToDestroy;
	var zapList = function() {
		var list_id = listsToDestroy.pop().id_str;
		console.log(listsToDestroy.length);
		T.post('lists/destroy', {list_id:list_id},
			function(err, reply) {
				if (err) {
					console.log('lists/destroy '+list_id);
					console.log(err);
					setTimeout(zapList,500);
				} else {
					setTimeout(zapList,0);
				}
			});
	}
	T.get('lists/ownerships',{screen_name:my_screen_name,count:1000},function(e,r) {
		listsToDestroy = r.lists;
		setTimeout(zapList,0);
	});
};

var createAllLists = function() {
	var list_create_pointer = 0;
	var createList = function() {
		// console.log(list_create_pointer);
		if (_.find(existing_lists,function(d) {return 'a'+list_create_pointer === d.name})===undefined) {
			console.log(list_create_pointer);
			var params = {name: 'a'+list_create_pointer, mode:'private'};
			T.post('lists/create', params,
				function(err, reply) {
					if (err) {
						console.log('lists/create');
						console.log(params);
						console.log(err);
					}
					list_create_pointer++;
					if (list_create_pointer < 1000) {
						setTimeout(createList,0);
					}
				});
		} else {
			list_create_pointer++;
			if (list_create_pointer < 1000) {
				setTimeout(createList,0);
			}
		}
	};
	var existing_lists;
	T.get('lists/ownerships',{screen_name:my_screen_name,count:1000},function(e,r) {
		existing_lists = r.lists;
		setTimeout(createList,0);
	});
};


