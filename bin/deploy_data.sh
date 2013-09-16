# will 
# - deploy json/data.json to s3 bucket specified in bucket specificied in $CONDOR_HOME/config-$CONDOR_ENV.json
# - also deploy code to appropriate archive directory

bucket_name="s3://$(python bucket_name.py)"
echo "using CONDOR_ENV $CONDOR_ENV, pushing json/data.json to bucket $bucket_name"

pushd .
cd $CONDOR_HOME

s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type data_staging/data.json $bucket_name/json/data.json

popd