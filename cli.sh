PROJECT_PATH="/src/app"
# PROJECT_PATH=/home/amir/apps/wqdms/monotremata-interface
cmd_update(){
    cd $PROJECT_PATH
    # . ./cli.sh
    . ~/.bashrc
    cd -
}
cmd_set_git_uer(){
    git config --global user.name "$USER:$HOSTNAME"
    git config --global user.email "$USER@$HOSTNAME.local"
    git config --global http.sslVerify "false"
}
cmd_pre(){
    cd $PROJECT_PATH
    # python3 manage.py dumpdata monotremata > presets.json
    rm ./db.sqlite3 || true
    rm -drf ./monotremata/migrations || true
    mkdir -p ./monotremata/migrations
    touch ./monotremata/migrations/__init__.py
    python3 manage.py makemigrations
    python3 manage.py migrate
    python3 manage.py loaddata user.json
    # python3 manage.py loaddata presets.json
    python3 manage.py runserver 0.0.0.0:8000
}

cmd_after(){
    cd $PROJECT_PATH
    python3 manage.py makemigrations
    python3 manage.py migrate
    # python3 manage.py loaddata user.json
    # python3 manage.py loaddata presets.json
    python3 manage.py runserver 0.0.0.0:8000
}



cmd_package(){
    cd $PROJECT_PATH
    rm -rdf ./packaged
    mkdir -p ./packaged
    cd $PROJECT_PATH/packaged
    u1='/?id=&name=wqdms&tag=&label=&applications__name=&applications__tag=&applications__label='
    u2='http://192.168.179.6:8000/project/?format=download&name=wqdms&id='
    curl $u2 --output mono.zip
    
    unzip ./mono.zip -d ./
    cd wqdms
    python manage.py makemigrations
    python manage.py migrate
    DJANGO_PORT=8002 python manage.py setup -s
    
}

cmd_clean_package(){
    cd $PROJECT_PATH
    rm -rdf ./packaged
    mkdir -p ./packaged
}

cmd_clean_app(){
    cd $PROJECT_PATH
    rm -rdf ./monotremata/migrations
    mkdir -p ./monotremata/migrations
    touch ./monotremata/migrations/__init__.py
    rm -drf ./interface/__pycache__
    rm -drf ./monotremata/__pycache__
    rm ./db.sqlite3
}

cmd_debug(){
    cmd_set_git_uer
    . .venv/bin/activate && uv sync
    cd ${PROJECT_PATH}
    uv run debugpy --listen 0.0.0.0:${DEBUGPY_PORT} manage.py runserver 0.0.0.0:${DJANGO_PORT}
}

cmd_jupyter(){
    cmd_set_git_uer
    . .venv/bin/activate && uv sync
    cd ${PROJECT_PATH}
    uv run manage.py shell_plus --lab
}

cmd_debug_shell(){
    cd ${PROJECT_PATH}
    # . .venv/bin/activate && \
    sleep 4
    uv run debugpy --listen 0.0.0.0:${DEBUGPY_PORT} \
        manage.py git \
        -a delete \
        -t token \
        -u amir \
        -p admin1234 \
        -o 1 \
        -g http://192.168.179.3:3000
}

cmd_debug_shell_create_organization(){
    cd ${PROJECT_PATH}
    # . .venv/bin/activate && \
    sleep 4
    uv run debugpy --listen 0.0.0.0:${DEBUGPY_PORT} \
        manage.py git \
        -a create \
        -t organization \
        -u amir \
        -p admin1234 \
        -o TestDemoOrg \
        -d TestDemoOrg \
        -g http://192.168.179.3:3000
}

cmd_build_dockerimage_cluster(){
    podman build -f ./Dockerfile.cluster --tag cluster.local:32000/mono:latest .
    podman push cluster.local:32000/mono:latest
}

cmd_demonstartion_wqdms(){
    cd /tmp/
    . /src/.venv/bin/activate
    git clone http://192.168.179.3:3000/unep/wqdms.git
    cd wqdms
    python manage.py setup -s
    python manage.py runserver 0.0.0.0:8002
}

