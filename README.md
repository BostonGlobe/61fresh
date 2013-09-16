# Condor

To install me on amazon linux, here are the steps:

    sudo yum install -y git gcc-c++ openssl-devel make python-botocore MySQL-python python27 python27-devel mysql blas-devel lapack-devel

    wget http://nodejs.org/dist/node-latest.tar.gz
    tar -zxvf node-latest.tar.gz
    cd node-v*
    ./configure
    make
    sudo make install
    cd ~
    rm -rf node-*

    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | sudo python27
    sudo /usr/bin/python27 /usr/bin/easy_install pip

    sudo pip-2.7 install boto MySQL-python numpy pyyaml nltk simplejson beautifulsoup4 gensim
    (note: gensim will install scipy, which takes forever to build on an ec2 micro. Said build
    will probably also run out of memory if the box is doing anything else at the time. On the mac,
    it looks like scipy's only dependency is gfortran, which is available through homebrew.)

    (Maybe look for the current/up-to-date version of phantomjs?)
    wget https://phantomjs.googlecode.com/files/phantomjs-1.9.2-linux-x86_64.tar.bz2
    tar -jxvf phantomjs-1.9.2-linux-x86_64.tar.bz2
    sudo mv phantomjs-1.9.2-linux-x86_64/bin/phantomjs /usr/local/bin
    rm -rf phantomjs-*

    put the private key in ~/.ssh/id_rsa (with proper permissions)

    git clone git@github.com:globelab/condor.git
    cd condor
    npm install bignum mysql twit underscore
	sudo ln -s /usr/bin/python /usr/bin/python27


To start the main ingest and url resolver:

    nohup python forever.py &
    nohup python resolve_forever.py &

The database config (and eventually Twitter creds etc.) are read from config.json, unless config-local.json exists. Create that file with values for your dev environment, but don't check it in. If you're using an ssh tunnel, use '127.0.0.1' for the host, not 'localhost', or python will try to use a unix socket.

Any scripts that require python 2.7 or nltk need to be run with the python27 command.


DEV ENV
