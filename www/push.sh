 s3cmd --add-header "Cache-Control: max-age=60" --recursive put --acl-public --guess-mime-type controllers css feed.html index.html js piggyback templates s3://condor.globe.com

