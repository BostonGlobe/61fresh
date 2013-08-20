HomepageController = function()
{

	this.rail_sets={'sets':
		[
			{
				'label':'#bosmayor',
				'set_name':'bosmayor',
				'type':'hashtag'
			},
			{
				'label':'#bospoli',
				'set_name':'bospoli',
				'type':'hashtag'
			}
		]
	}

	this.do_rail_sets = function()
	{
		_.each(rail_sets.sets,function(rail_set) {
			$("#right_rail").append("<div id='"+rail_set.set_name+"'></div")
			set_url = "json/"+rail_set.set_name+".json"
			$.ajax({
				url:set_url,
				dataType: 'json',
				success: function(json){
					this.log("in handler:" + context.rail_set.set_name)
					this.rail_set = context.rail_set
					this.json = json
					this.render(that.rail_set.set_name,"rail_set")
				},
				cache: true
			})
		})
	}
	
	this.handle_combined_json = function(json)
	{
		this.log('handle_combined_json')
		this.json = json
		titles = {}
		that=this
		// loop through & process articles
		_.each(this.json.articles.articles,function(article){
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
		this.render("index",'homepage')
	}
	

	this.start = function()
	{
		this.DEFAULT_SET='data'
		this.set = this.query_param("set")
		this.diag = this.query_param("diag")
		if (!this.set) this.set=this.DEFAULT_SET
		this.log("rendering homepage page with set "+set)
		set_url = "json/"+set+".json"
		$.ajax({
			url: set_url,
			dataType: 'json',
			context: this,
			success: this.handle_combined_json,
			cache: false
		})
	}
	
	this.start();
}

HomepageController.prototype=new ApplicationController();

HomepageController();
