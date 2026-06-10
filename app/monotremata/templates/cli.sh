{% autoescape off %}

#!/bin/bash
export MY_PASS=$ADMIN_PASSWORD
export MY_USERNAME=$ADMIN_USERNAME
export DEPLOYMENT_URL='{{ SERVICE_URL }}/deployment/{{ id }}'

cmd_monotremata_download(){
    curl -u "$MY_USERNAME:$MY_PASS" '{{ SERVICE_URL }}/deployment/{{ id }}/?format=download' --output mono.zip
}

cmd_monotremata_deployment(){
    cmd_monotremata_download
    unzip ./mono.zip -d ./mono
    cd ./mono/{{ project.name | lower }}
    uv run manage.py setup -s run
}

cmd_monotremata_deployment_json(){
    curl -H "ContentType: application/json" -u "$MY_USERNAME:$MY_PASS" "$DEPLOYMENT_URL/?format=json"
}

cmd_monotremata_deployment_scripts(){
   curl -H "ContentType: application/json" -u "$MY_USERNAME:$MY_PASS" "$DEPLOYMENT_URL/?format=json"  | jq .results[0].script
}

cmd_monotremata_deployment_script_cli(){
   curl -H "ContentType: application/json" -u "$MY_USERNAME:$MY_PASS" "$DEPLOYMENT_URL/?format=json"  | jq -r .results[0].script.cli
}

cmd_monotremata_deployment_script_applicationset(){
   curl -H "ContentType: application/json" -u "$MY_USERNAME:$MY_PASS" "$DEPLOYMENT_URL/?format=json"  | jq -r .results[0].script.applicationset
}

cmd_monotremata_deployment_script_dockerfile(){
   curl -H "ContentType: application/json" -u "$MY_USERNAME:$MY_PASS" "$DEPLOYMENT_URL/?format=json"  | jq -r .results[0].script.Dockerfile
}

cmd_monotremata_deployment_script_docker_compose(){
   curl -H "ContentType: application/json" -u "$MY_USERNAME:$MY_PASS" "$DEPLOYMENT_URL/?format=json"  | jq -r .results[0].script.'docker_compose'
}
cmd_podman_build_image(){
    podman build -f Dockerfile --tag {{ registry_url }}/monotremata-{{ project.category }}:latest
}

cmd_podman_push_image(){
    podman push {{ registry_url }}/monotremata-{{ project.category }}:latest
}

cmd_podman_update(){
    cmd_podman_build_image
    cmd_podman_push_image
}

cmd_setup_cli_script(){
    cmd_monotremata_deployment_script_cli > ./cli.sh
    . ./cli.sh
}

cmd_cleanup(){
    rm ./mono.zip
    rm -drf mono
}

cmd_git_deployment(){
    git config --global user.name "{{ has_owner }}:$HOSTNAME"
    git config --global user.email "{{ git_organization_user }}@groupeffect.de"
    git config --global http.sslVerify "false"
    cmd_monotremata_download
    unzip ./mono.zip -d ./mono
    git clone {{ git_api_url }}/{{ organization.name | lower }}/{{ project.name | lower }}.git
    cp -r ./mono/{{ project.name | lower }}/. ./{{ project.name | lower }}/.
    git add -A
    git commit -m "monotremata deployment | $(date)"
    git push 
}

cmd_python_setup(){
    python manage.py makemigrations
    python manage.py migrate
}
{% endautoescape %}
