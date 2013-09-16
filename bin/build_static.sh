pushd .
cd $CONDOR_HOME

phantomjs render_static_page.js www/index.html > www/static.html 

popd