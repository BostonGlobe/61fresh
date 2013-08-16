pushd .
cd ~/condor
git commit -am "$1"
git push origin master
./push.sh
popd
