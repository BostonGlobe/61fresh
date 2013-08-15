IndexController = function()
{

	this.start = function()
	{
		this.json = {"links":[	
			{
				'name':'hotlist2',
				'set':'hotlist2'
			},
			{
				'name':'#bosmayor hashtag',
				'set':'bosmayor'
			},
			{
				'name':'#boston hashtag',
				'set':'boston'
			},
			{
				'name':'#bospoli hashtag',
				'set':'bospoli'
			},
			{
				'name':'#mapoli hashtag',
				'set':'mapoli'
			},
			{
				'name':'#redsox hashtag',
				'set':'redsox'
			},
			{
				'name':'#MBTA hashtag',
				'set':'mbta'
			}
			
			]
		}
		this.render("index")
	}
	this.start();
}

IndexController.prototype=new ApplicationController();

IndexController();
