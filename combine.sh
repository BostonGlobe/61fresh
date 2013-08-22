pushd .
cd ~/condor
rm -rf data
mkdir data
python hotlist2.py $1 --num_results=20 > data/articles_12.json
mv data/articles_12.json data/articles.json

mkdir data/hashtags
python hotlist2.py $1 --hashtag=bospoli 	--min --no_tweeters --num_results=5 > data/hashtags/bospoli.json
python hotlist2.py $1 --hashtag=mapoli 		--min --no_tweeters --num_results=5 > data/hashtags/mapoli.json
python hotlist2.py $1 --hashtag=bosmayor 	--min --no_tweeters --num_results=5 > data/hashtags/bosmayor.json
python hotlist2.py $1 --hashtag=redsox 		--min	--no_tweeters --num_results=5 > data/hashtags/redsox.json
python hotlist2.py $1 --hashtag=patriots 	--min --no_tweeters --num_results=5 > data/hashtags/patriots.json

mkdir data/leaders
python hotlist2.py --min --no_tweeters --num_results=10 --age=168 > data/leaders/week.json

rm -rf www/json
mkdir www/json
python combine_json.py data > www/json/data.json
cp data/leaders/week.json data/articles_168.json
mv data/* www/json
popd
