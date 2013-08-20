pushd .
cd ~/condor
git commit -am "$1"
git push origin master
./www/push.sh
popd
