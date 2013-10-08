DomainController = function()
{

	this.MAX_ARTICLES = 20
	
	this.handle_json = function(json,status,error)
	{
		try
		{
			$('body').show()
			this.debug("domain controller:handle_json")
			
			this.json = json
			if (status!='error')
			{
				this.debug("# of articles in json",this.json.articles.length)
				titles = {}
				that=this
				// loop through & process articles
				num_articles = 0
				iter =0
				cluster_index = -1;
				_.each(this.json.articles,function(article,i){
					iter+=1
					if (iter>=that.MAX_ARTICLES) 
					{
						article.deleted=true
						return;
					}
					if (article.url=='Error') 
					{
						article.deleted=true;
						return;
					}
					if (that.sports_muted && article.sports_score>that.SPORTS_THRESHOLD) 
					{
						article.deleted=true
						return;
					}
					num_articles+=1
					this.log(":"+num_articles+":"+that.MAX_ARTICLES)
		
					article.order_within_cluster=i

					// find earliest tweet, make it the 'author' tweet
					article.first_tweeter = article.tweeters[0]
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
				
				
//				this.debug('rendering homepage.ejs')
				this.render("index",'domain',function(){
//					that.render('insights')
				})
			}

			// do DOM stuff
			that=this

			//sports mute button
			this.get_cookie("sports_mute")=='true' ? $("#sports_mute").prop('checked',true) : $("#sports_mute").prop('checked',false)
			$('#sports_mute').click(function(e) {
					that.mute_sports($(this).is(':checked'))
			});		
			
			// show/hide twitter sharing links
			$('.article').hover(function () {
			    $(this).find(".hover").show()
			    $(this).find(".article_is_new").hide()
			  },
			  function () {
			    $(this).find(".hover").hide()
			    $(this).find(".article_is_new").show()
			  })

			// debug statement
			if (status!='error') this.debug("json handled with # of articles",this.json.articles.length)
			
			// hack to remove 'forward' button on homepage
			if (document.location.href.indexOf("index.html")==-1)
			{
				$(".navigation_forward").hide()
			}
			
			// hack to make twitter think it hasn't already done this at the time of static generation
			$("body").attr("data-twttr-rendered","") 
			$.getScript("js/twitter_widgets.js")
			$.getScript('js/twitter_tweet_button.js')
			
			// track clicks on outbound links
			$(".outbound_link").on('click', function() {
					link = $(this).attr('href')
				  ga('send', 'event', 'outbound_link', 'click', link);
			});
	  }
		catch(err)
		{
			s = "ERROR: "+err.message
			if (err.line) s+=" (line #"+err.line+")"
			if (err.stack) s+="<br>STACKTRACE:<div style='margin-left:10px'>"+err.stack+"</div>"
			this.log(s)
			this.debug(s)
		}
	}
	
	this.archive_url = function(dt,step)
	{
		step=step*6
		hash = {
				0:'night',
				1:'morning',
				2:'afternoon',
				3:'evening'
				}
		var d = this.add_hours(new Date(dt),step);
   	var day = d.getDate();
    var month = d.getMonth() + 1; //Months are zero based
    if ((""+day).length==1) day="0"+day
    if ((""+month).length==1) month="0"+month
		var year = d.getFullYear();
		formatted_date=""+year+month+day
		day_part = hash[Math.floor(d.getHours()/6)];
		return "/"+formatted_date+"/"+day_part+"/index.html"
	}
	
	this.format_date = function(iso_string) {
		var moment_date = moment(iso_string);
		if (window.location.search === "?absdate") {
			return moment_date.format('MMMM Do, h:mm a');
		} else {
			return moment_date.fromNow();
		}
	}

	this.start = function()
	{
		this.debug("domain_controller start")
		this.domain = this.query_param("domain")
		this.diag = this.query_param("diag")
		if (!this.set) this.set=this.DEFAULT_SET
		this.log("rendering events page with set "+this.set)
		set_url = "json/domains/"+this.domain+".json"
		this.debug("loading json",set_url)
		$.ajax({
			url: set_url,
			dataType: 'json',
			context: this,
			success: this.handle_json,
			error: this.handle_json,
			cache: false
		})
	}
}

DomainController.prototype=new ApplicationController();

//HomepageController();
