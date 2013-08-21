ApplicationController = function()
{
	this.get_param = function(query,key)
	{
		that=this
		pairs = query.match(/([^&=?]+)=([^&=?]+)/g)
		kvs={}
		_(pairs).each(function(elem){
			toks = elem.split("=")
			kvs[toks[0]]=toks[1]
		})
		return kvs[key]
	}
	this.log = function(s,data)
	{
		if (console && debug)
		{
			t=s
			if (data)
			{
				t+=":"
				t+=data.inspect();
			}
			console.log(t)
		}
	}

	
	
}

ApplicationController.prototype = new PiggyBack();

ApplicationController();
