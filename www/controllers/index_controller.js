IndexController = function()
{
	
	this.handle_json = function(json)
	{
		this.json = json
		this.render('index')
	}
	
	this.start = function()
	{
		this.log("index")
		$.ajax({
			url: "json/daniel.json",
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
