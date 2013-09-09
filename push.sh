bucket_name="s3://$(python bucket_name.py)"
echo "commiting code, pushing back end to production, pushing front end to bucket $bucket_name"
pushd .
git commit -am "$1"
git push origin master
ssh -t ec2-user@ec2-54-242-45-233.compute-1.amazonaws.com "cd condor;git pull"
cd $CONDOR_HOME/www
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type controllers css feed.html index.html homepage.html js piggyback templates $bucket_name
popd
