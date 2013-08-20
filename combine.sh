pushd .
cd ~/condor
rm -rf data
mkdir data
python hotlist2.py > data/articles.json
mkdir data/hashtags
python hashtag.py bospoli > data/hashtags/bospoli.json
python hashtag.py mapoli > data/hashtags/mapoli.json
python hashtag.py bosmayor > data/hashtags/bosmayor.json
python hashtag.py redsox > data/hashtags/redsox.json
python hashtag.py patriots > data/hashtags/patriots.json

mkdir data/leaders
python hotlist2.py 168 > data/leaders/week.json

rm -rf www/json
mkdir www/json
python combine_json.py data > www/json/data.json
mv data/* www/json
popd
