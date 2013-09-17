# will 
# - deploy json/data.json to s3 bucket specified in bucket specificied in $CONDOR_HOME/config-$CONDOR_ENV.json
# - also deploy code to appropriate archive directory

bucket_name="s3://$(python $CONDOR_HOME/bucket_name.py)"
day_part_name=`$CONDOR_HOME/bin/day_part_name.sh`
formatted_date=`TZ=America/New_York date +"%Y%m%d"`

echo "using CONDOR_ENV $CONDOR_ENV, pushing data.json to buckets $bucket_name/json, $bucket_name/$formatted_date/$day_part_name/json"

pushd .
cd $CONDOR_HOME/data_staging

echo "zipping data ..."
gzip data.json

echo "deploying to production root ..."
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type --add-header "Content-Encoding: gzip" data.json.gz $bucket_name/json/data.json

echo "deploying to archive ..."
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type --add-header "Content-Encoding: gzip" data.json.gz $bucket_name/$formatted_date/$day_part_name/json/data.json
popd