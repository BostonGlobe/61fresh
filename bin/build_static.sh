pushd .
cd $CONDOR_HOME

phantomjs render_static_page.js "www/index.html?absdate&static_mode" > www/static.html 

popd