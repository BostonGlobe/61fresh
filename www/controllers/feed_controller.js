FeedController = function()
{
	this.handle_articles_json = function(json)
	{
		$(".last_updated").html("last updated "+moment(new Date(json.generated_at)).fromNow())
		this.json = json
		titles = {}
		that=this
		// loop through & process articles
		_.each(this.json.articles,function(article){
			if (article.url=='Error') return;
			// find earliest tweet, make it the 'author' tweet
			article.first_tweeter=article.tweeters[0]
			if (!article.first_tweeter) 
			{
				article.deleted=true
				return
			}
			_.each(article.tweeters,function(tweet,i){
				if (new Date(tweet.created_at).getTime()<new Date(article.first_tweeter.created_at).getTime()) article.first_tweeter = tweet
			})
			// find and combine duplicate articles
			if (titles[article.title]) // found a dupe
			{
				if (article.source!=titles[article.title].source) titles[article.title].source +=", "+article.source
				article_to_use = titles[article.title]
				_.each(article.tweeters,function(tweeter){
					article_to_use.tweeters.push(tweeter)
				})
				article.deleted=true
				return; 
			}
			titles[article.title]=article;

			// replace headline with text of tweet by user with most followers
			article.tweet_title = article.first_tweeter.text
			article.tweet_title = article.tweet_title.replace (/http[^\s]+/g,"")
			article.tweet_title_screen_name = article.first_tweeter.screen_name
			article.profile_image_url = article.first_tweeter.profile_image_url

			// mark new articles as new
			if ((new Date().getTime()-new Date(article.first_tweeted).getTime())<60*60*1000) article.is_new=true // 1 hour
			else article.is_new=false
		})
		view = this.query_param("view")
		if (view==null) view='feed'
		
		this.render("index",view)
	}


	this.start = function()
	{
		this.set = this.query_param("set")
		this.diag = this.query_param("diag")
		if (!this.set) this.set=this.DEFAULT_SET
		this.log("rendering index page with set "+set)
		set_url = "json/"+this.set+".json"
		$.ajax({
			url: set_url,
			dataType: 'json',
			context: this,
			success: this.handle_articles_json,
			cache: true
		})
	}
	
	this.start();
}

FeedController.prototype=new ApplicationController();

FeedController();
