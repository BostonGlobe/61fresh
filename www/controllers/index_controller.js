IndexController = function()
{
	this.DEFAULT_SET='daniel';
	this.handle_json = function(json)
	{
		this.json = json
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
