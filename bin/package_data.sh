bucket_name="s3://$(python $CONDOR_HOME/bucket_name.py)"
echo "packaging data into  $CONDOR_HOME/data_staging and $CONDOR_HOME/www/json ..."

pushd . > /dev/null
cd $CONDOR_HOME > /dev/null
rm -rf data_staging
mkdir data_staging
python27 hotlist2.py $1 $2 $3 --group_clusters 1 --num_results=40 > data_staging/articles_12.json
mv data_staging/articles_12.json data_staging/articles.json

mkdir data_staging/hashtags
python27 hotlist2.py $1 --hashtag=bospoli	--min --no_tweeters --num_results=5 > data_staging/hashtags/bospoli.json
python27 hotlist2.py $1 --hashtag=mapoli 		--min --no_tweeters --num_results=5 > data_staging/hashtags/mapoli.json
python27 hotlist2.py $1 --hashtag=bosmayor 	--min --no_tweeters --num_results=5 > data_staging/hashtags/bosmayor.json
python27 hotlist2.py $1 --hashtag=redsox 		--min	--no_tweeters --num_results=5 > data_staging/hashtags/redsox.json
python27 hotlist2.py $1 --hashtag=patriots 	--min --no_tweeters --num_results=5 > data_staging/hashtags/patriots.json

mkdir data_staging/leaders
python27 hotlist2.py --min --no_tweeters --num_results=10 --age=168 > data_staging/leaders/week.json

mkdir data_staging/domain_leaders
python top_domains.py --age=1 --num_results=25 > data_staging/domain_leaders/domains_1.json

# rm -rf www/json
# mkdir www/json
python combine_json.py data_staging www/json/data.json
# cp data.json data_staging 
# cp data.json www/json
#cp data_staging/leaders/week.json data_staging/articles_168.json
#cp -r data/* www/json
popd > /dev/null
