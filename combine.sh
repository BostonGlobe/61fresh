if [[ -z "$1" ]]
	then
		echo "you must specify a name for this dataset (ex: ./combine.sh data)" && exit 1
fi
pushd .
cd ~/condor
rm -rf $1
mkdir $1
python27 hotlist2.py $2 $3 $4 --num_results=40 > $1/articles_12.json
mv data/articles_12.json $1/articles.json

mkdir data/hashtags
python27 hotlist2.py --hashtag=bospoli	--min --no_tweeters --num_results=5 > $1/hashtags/bospoli.json
python27 hotlist2.py --hashtag=mapoli 	--min --no_tweeters --num_results=5 > $1/hashtags/mapoli.json
python27 hotlist2.py --hashtag=bosmayor --min --no_tweeters --num_results=5 > $1/hashtags/bosmayor.json
python27 hotlist2.py --hashtag=redsox 	--min	--no_tweeters --num_results=5 > $1/hashtags/redsox.json
python27 hotlist2.py --hashtag=patriots --min --no_tweeters --num_results=5 > $1/hashtags/patriots.json

mkdir data/leaders
python27 hotlist2.py --min --no_tweeters --num_results=10 --age=168 > $1/leaders/week.json

mkdir data/domain_leaders
python top_domains.py --age=1 --num_results=25 > data/domain_leaders/domains_1.json

rm -rf www/json
mkdir www/json
mkdir www/json/$1
python combine_json.py $1 > www/json/$1.json
cp data/leaders/week.json $1/articles_168.json
cp -r $1/* www/json/$1
popd
