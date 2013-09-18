var Twit = require('twit')

// These credentials are for the 61fresh twitter account.
// This is different from the account and application that handles the ingest.
var T = new Twit({
    consumer_key:         '***REMOVED***'
  , consumer_secret:      '***REMOVED***'
  , access_token:         '***REMOVED***'
  , access_token_secret:  '***REMOVED***'
});

var data = require(__dirname + '/data_staging/data.json');

var article = data.articles.clusters[0][0];

var tweet_id_to_retweet;

article.tweeters.forEach(function(tweet,i){
	if (tweet.created_at===article.first_tweeted) tweet_id_to_retweet = tweet.tweet_id;
})

T.post('statuses/retweet/:id', {id: tweet_id_to_retweet})