# will 
# - deploy html/css/javascript files to s3 bucket specified in bucket specificied in $CONDOR_HOME/config-$CONDOR_ENV.json
# - also deploy code to appropriate archive directory

pushd . >/dev/null
cd $CONDOR_HOME >/dev/null

bucket_name="s3://$(python $CONDOR_HOME/bucket_name.py)"
day_part_name=`$CONDOR_HOME/bin/day_part_name.sh`
formatted_date=`TZ=America/New_York date +"%Y%m%d"`


if [ $(python $CONDOR_HOME/bucket_name.py) = "61fresh.com" ]; then
	node tweet_lead_story.js
fi

echo "using CONDOR_ENV $CONDOR_ENV, pushing code to buckets $bucket_name, $bucket_name/$formatted_date/$day_part_name"

echo "rendering pages with phantomjs ..."
phantomjs render_static_page.js "www/index.html?absdate">www/static_archive.html
phantomjs render_static_page.js "www/index.html">www/static.html

rm -r www_gzip_staging
cp -r www www_gzip_staging

function strip_gz { for i in "$@"; do j=`echo $i | sed "s/\.gz//"`; mv "$i" "$j"; done }
export -f strip_gz
gzip -r www_gzip_staging
find www_gzip_staging -name "*.gz" -exec bash -c "strip_gz {}" \;


echo "deploying to production root ..." 
cd www_gzip_staging > /dev/null
# deploy to production root
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type --add-header "Content-Encoding: gzip" controllers css feed.html about.html homepage.html js piggyback templates images favicon.ico json $bucket_name

#deploy gzipped static index page to production
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type --add-header "Content-Encoding: gzip" static.html $bucket_name/index.html


# deploy to archive folder
# create folder named after the date
# create morning.html,afternoon.html,evening.html or night.html
# ex: 61fresh.com/20130916/afternoon.html 
# copy static to index.html too, so that we will see the final file uploaded for that day in the root.
# ex: 61fresh.com/20130916/index.html 

echo "deploying to archive ..."
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type --add-header "Content-Encoding: gzip" controllers css about.html js piggyback templates images json $bucket_name/$formatted_date/$day_part_name/

s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type --add-header "Content-Encoding: gzip" static_archive.html $bucket_name/$formatted_date/$day_part_name/index.html

cd $CONDOR_HOME >/dev/null
rm -r www_gzip_staging

popd >/dev/null