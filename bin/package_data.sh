bucket_name="s3://$(python $CONDOR_HOME/bucket_name.py)"
timestring="$(date +%Y%m%d%H%M%S)$RANDOM"
echo "packaging data into  $CONDOR_HOME/data_staging and $CONDOR_HOME/www/json ..."

pushd . > /dev/null
cd $CONDOR_HOME > /dev/null
mkdir -p data_staging/$timestring
python27 hotlist2.py $1 $2 $3 --group_clusters 1 --num_results=40 > data_staging/$timestring/articles.json

mkdir data_staging/$timestring/hashtags
python27 hotlist2.py $1 --hashtag=bospoli	--min --no_tweeters --num_results=5 > data_staging/$timestring/hashtags/bospoli.json
python27 hotlist2.py $1 --hashtag=mapoli 		--min --no_tweeters --num_results=5 > data_staging/$timestring/hashtags/mapoli.json
python27 hotlist2.py $1 --hashtag=bosmayor 	--min --no_tweeters --num_results=5 > data_staging/$timestring/hashtags/bosmayor.json
python27 hotlist2.py $1 --hashtag=redsox 		--min	--no_tweeters --num_results=5 > data_staging/$timestring/hashtags/redsox.json
python27 hotlist2.py $1 --hashtag=patriots 	--min --no_tweeters --num_results=5 > data_staging/$timestring/hashtags/patriots.json

mkdir data_staging/$timestring/leaders
python27 hotlist2.py --min --no_tweeters --num_results=10 --age=168 > data_staging/$timestring/leaders/week.json

mkdir data_staging/$timestring/domain_leaders
python top_domains.py --age=1 --num_results=25 > data_staging/$timestring/domain_leaders/domains_1.json

# We do this cd dance because the actual path by which the staging directory is passed in affects the structure of the json.
cd data_staging
python ../combine_json.py $timestring ../www/json/data.json
cd ..

rm -r data_staging/$timestring

popd > /dev/null
