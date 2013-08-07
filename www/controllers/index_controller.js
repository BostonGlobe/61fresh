IndexController = function()
{

	this.start = function()
	{
		this.json = {"links":[	
			{
				'name':'hotlist',
				'set':'hotlist'
			},
			{
				'name':'#bosmayor hashtag',
				'set':'#bosmayor'
			},
			{
				'name':'#boston hashtag',
				'set':'#boston'
			},
			{
				'name':'#bospoli hashtag',
				'set':'#bospoli'
			},
			{
				'name':'#mapoli hashtag',
				'set':'#mapoli'
			}
			]
		}
		this.render("index")
	}
	this.start();
}

IndexController.prototype=new ApplicationController();

IndexController();
