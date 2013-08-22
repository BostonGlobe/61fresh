pushd .
cd ~/condor
rm -rf data
mkdir data
python hotlist2.py --num_results=20 > data/articles_12.json
cp data/articles_12.json data/articles.json

mkdir data/hashtags
python hotlist2.py --hashtag=bospoli 	--no_tweeters --num_results=5 > data/hashtags/bospoli.json
python hotlist2.py --hashtag=mapoli 	--no_tweeters --num_results=5 > data/hashtags/mapoli.json
python hotlist2.py --hashtag=bosmayor --no_tweeters --num_results=5 > data/hashtags/bosmayor.json
python hotlist2.py --hashtag=redsox 	--no_tweeters --num_results=5 > data/hashtags/redsox.json
python hotlist2.py --hashtag=patriots --no_tweeters --num_results=5 > data/hashtags/patriots.json

mkdir data/leaders
python hotlist2.py --no_tweeters --num_results=10 --age=168 > data/leaders/week.json
cat data/leaders/week.json > data/articles_168.json

rm -rf www/json
mkdir www/json
python combine_json.py data > www/json/data.json
mv data/* www/json
popd
