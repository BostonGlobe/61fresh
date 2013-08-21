# Condor

To install me on amazon linux, here are the steps:

    sudo yum install -y git gcc-c++ openssl-devel make python-botocore MySQL-python
    wget http://nodejs.org/dist/node-latest.tar.gz
    tar -zxvf node-latest.tar.gz
    cd node-v*
    ./configure
    make
    sudo make install
    cd ~
    rm -rf node-*

    put the private key in ~/.ssh/id_rsa (with proper permissions)

    git clone git@github.com:globelab/condor.git
    cd condor
    npm install bignum mysql twit underscore


To start the main ingest and url resolver:

    nohup python forever.py &
    nohup node resolve_urls.js &

The database config (and eventually Twitter creds etc.) are read from config.json, unless config-local.json exists. Create that file with values for your dev environment, but don't check it in. If you're using an ssh tunnel, use '127.0.0.1' for the host, not 'localhost', or python will try to use a unix socket.