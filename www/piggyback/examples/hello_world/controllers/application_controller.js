ApplicationController = function()
{
	// ROUTE SETUP
	this.setup_routes = function()
	{
		var routes = {
		        '/index': new function() {that=new IndexController();that.index},
		        '/cat': new function() {that=new CatController();that.cat}
		      };
		
     var router = Router(routes);
     router.init();
//		new jQuery.mobile.Router([{"index":  { handler:"index", events:"bc" }}],new IndexController(),{});	
//		new jQuery.mobile.Router([{"cats-#(.+)-(.+)":  { handler:"cat", events:"bc" }}],new CatController(),{});	
	}
}
ApplicationController.prototype = new Base();

ApplicationController();
