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


var addTweets = function(tweets,memo) {
	rc.sadd(['seen_tweets'].concat(tweets.map(function(d) {return d.id_str;})),
		function(err, reply) {console.log(memo+": " + reply + " of " +tweets.length + " were new.");});
	rc.scard('seen_tweets',function(err, reply) {console.log("Tweets: "+reply);});
}

var refreshBoston = function() {
	T.get('search/tweets', {geocode:'42.3583,-71.0603,10mi', result_type: 'recent', count:100},
		function(err, reply) {
			if (err) {
				console.log("search/tweets");
				console.log(err);
			} else {
				rc.sadd(['seen_uids'].concat(reply.statuses.map(function(d) {return d.user.id_str;})));
				rc.scard('seen_uids',function(err, reply) {console.log("Seen: "+reply);});
				addTweets(reply.statuses,"search");
			}
		})
}

var list_fill_pointer = Math.floor((Math.random()*1000));

var fillLists = function() {
	list_fill_pointer = (list_fill_pointer + 1) % 1000;
	console.log("Fill Pointer: "+list_fill_pointer)
	rc.sdiff(['seen_uids','listed_uids'],
		function(err, reply) {
			var this_bucket = reply.filter(function(d) {return parseInt(d.slice(-3))==list_fill_pointer;}).slice(0,100);
			if (this_bucket.length > 0) {
				T.post('lists/members/create_all', {owner_screen_name: my_screen_name, slug: 'a'+list_fill_pointer, user_id: this_bucket.join(',')},
					function(err, reply) {
						if (err) {
							console.log('lists/members/create_all');
							console.log(err);
						} else {
							rc.sadd(['listed_uids'].concat(this_bucket));
							rc.scard('listed_uids',function(err, reply) {console.log("Listed: "+reply);});
						}
					});
			}
		});
}

var list_refresh_pointer = Math.floor((Math.random()*1000));

var refreshLists = function() {
	list_refresh_pointer = (list_refresh_pointer + 1) % 1000;
	T.get('lists/statuses', {owner_screen_name: my_screen_name, slug: 'a'+list_refresh_pointer, count:200},
			function(err, reply) {
				if (err) {
					console.log('lists/statuses');
					console.log(err);
				} else {
					addTweets(reply,'list');
				}
			});
}


var refreshBostonTrigger = setInterval(refreshBoston,(15*60*1000)/170);
var refreshListsTrigger = setInterval(refreshLists,(15*60*1000)/171);
var listsTrigger = setInterval(fillLists,(15*60*1000)/175);
