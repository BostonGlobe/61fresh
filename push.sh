pushd .
git commit -am "$2"
git push origin master
ssh -t ec2-user@ec2-54-242-45-233.compute-1.amazonaws.com "cd condor;git pull"
cd ~/condor/www
s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type controllers css feed.html index.html homepage.html js piggyback templates s3://$1
popd
