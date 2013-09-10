cb = null
function PiggyBack()
{
	debug=true
	
	this.render = function(id,template,post_load)
	{
		if (template==null) template=id
		this.log("rendering template <"+template+"> into id <" + id + "> ... ")
		fragment = new EJS({url: 'templates/'+template+'.ejs'}).render(this)		// render page fragment
		$("#"+id).html(fragment)
		if (post_load) post_load();
	}
	
	this.set_cookie = function(name,value,days) 
	{
		if (days) {
			var date = new Date();
			date.setTime(date.getTime()+(days*24*60*60*1000));
			var expires = "; expires="+date.toGMTString();
		}
		else var expires = "";
		document.cookie = name+"="+value+expires+"; path=/";
	}

	this.get_cookie=function (name) 
	{
	    var prefix = name + '=';
	    var c = document.cookie;
	    var nullstring = '';
	    var cookieStartIndex = c.indexOf(prefix);
	    if (cookieStartIndex == -1) return nullstring;
	    var cookieEndIndex = c.indexOf(";", cookieStartIndex + prefix.length);
	    if (cookieEndIndex == -1) cookieEndIndex = c.length;
	    return unescape(c.substring(cookieStartIndex + prefix.length, cookieEndIndex));     
	}
	
	this.empty = function(s)
	{
		s = $.trim(s)
		if (s.length==0||s==null) return true
		else return false
	}
	

	// method can either be a method name or an anonymous function 
	this.callback = function(obj,func,extra)
	{
		if (_.isFunction(func))
		{
			method_name = "method_"+Math.floor(Math.random()*Math.min(1e15,Number.MAX_VALUE)) // generate a random name for the anon function
			obj[method_name]=func // add this function, with the given name, to the object.
		}
		else
		{
			method_name = func // just treat it as a string, the name of a method already defined
		}
		callback_name = "callback_"+method_name

		code = callback_name + " = function(data,extra) {obj."+method_name+"(data,extra)}"
		eval(code) // create global callback
		
		return callback_name;
	}
	
	this.call_api = function(that,url,callback,extra)
	{
		callback = this.callback(that,callback,extra)
		$.ajax({
			url: url,
			dataType: 'jsonp',
			jsonpCallback: callback,
			cache: true
		})
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

	this.query_param = function(key)
	{
		query = document.location.href
		that=this
		pairs = query.match(/([^&=?]+)=([^&=?]+)/g)
		kvs={}
		_(pairs).each(function(elem){
			toks = elem.split("=")
			kvs[toks[0]]=toks[1]
		})
		return kvs[key]
	}
	
	this.query_string_to_hash = function (query) {
	  var query_string = {};
	  var vars = query.split("&");
	  for (var i=0;i<vars.length;i++) {
	    var pair = vars[i].split("=");
	    pair[0] = decodeURIComponent(pair[0]);
	    pair[1] = decodeURIComponent(pair[1]);
	        // If first entry with this name
	    if (typeof query_string[pair[0]] === "undefined") {
	      query_string[pair[0]] = pair[1];
	        // If second entry with this name
	    } else if (typeof query_string[pair[0]] === "string") {
	      var arr = [ query_string[pair[0]], pair[1] ];
	      query_string[pair[0]] = arr;
	        // If third or later entry with this name
	    } else {
	      query_string[pair[0]].push(pair[1]);
	    }
	  } 
	  return query_string;
	};

}

PiggyBack();


