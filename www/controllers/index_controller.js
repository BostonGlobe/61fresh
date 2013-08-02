IndexController = function()
{
	this.DEFAULT_SET='daniel';
	this.handle_json = function(json)
	{
		this.json = json
		titles = {}
		that=this
		_.each(this.json.articles,function(article){
			if (titles[article.title]) // found a dupe
			{
				if (article.source!=titles[article.title].source) titles[article.title].source +=", "+article.source
				article.deleted=true
				return; 
			}
			titles[article.title]=article;
			if ((new Date().getTime()-new Date(article.first_tweeted).getTime())<30*60*1000) article.is_new=true // 1 hour
			else article.is_new=false
		})
		this.render('index')
	}

	this.start = function()
	{
		set = this.query_param("set")
		if (!set) set=DEFAULT_SET
		this.log("rendering index page with set "+set)
		set_url = "json/"+set+".json"
		$.ajax({
			url: set_url,
			dataType: 'json',
			context: this,
			success: this.handle_json,
			cache: true
		})
	}
	
	this.start();
}

IndexController.prototype=new ApplicationController();

IndexController();
