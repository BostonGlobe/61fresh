IndexController = function()
{
	this.start = function()
	{
		this.setup_routes(); // must be called once per page load
		this.log("index")
		this.render_plain('index');
	}
}

IndexController.prototype=new ApplicationController();

IndexController();

