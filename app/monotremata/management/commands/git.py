import os
from django.conf import settings
import requests
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from pprint import pp
import subprocess
from monotremata.modelling import ProjectZipFile, DeploymentConfigLoader
from pathlib import Path
# from monotremata.models import Organization, Deployment, Project
from types import SimpleNamespace
import json
import shutil
from monotremata.middleware import error_message

class RequestApi:
    def __init__(self):
        self.git_url = settings.GIT_URL
        self.session

    @staticmethod
    def request(args: SimpleNamespace):
        data = json.loads(args.data)
        session = requests.Session()
        session.headers["Content-Type"] = "application/json"
        session.auth = (args.user, args.password)
        try:
            response = getattr(session, args.method)(args.url, json=data)
            try:
                return response.json()
            except Exception as e:
                print(e)
            return response.text
        except Exception as e:
            return str(e)


class HttpApi:
    def __init__(self, url=None, user=None, password=None, token=None):
        self.token = token
        self.url = url
        self.session = requests.Session()
        self.user = user
        self.password = password

    def set_headers(
        self,
        headers: dict = {
            "Content-type": "application/json",
            "Accept": "application/json",
        },
    ):
        self.session.headers = {**self.session.headers, **headers}
        return self.session.headers

    def update_session_headers(self, jwt_key: str = "Bearer"):
        self.session.headers = {
            **self.session.headers,
            "Authorization": f"{jwt_key} {self.token}",
        }

    def login(self, url=None):
        if url is None:
            url = self.url
        response = self.session.post(
            f"{url}",
            json={"username": self.user, "password": self.password},
        )
        self.response = response
        self.token = response.json()["access"]
        self.update_session_headers()
        return response

    def request(self, url=None, method="get", data=None, json=None, files=None):
        if url is None:
            url = self.url

        response = None
        if method in ["put", "patch", "post"]:
            # print(["# update", method])
            response = getattr(self.session, method)(
                url, json=json, data=data, files=files
            )
        elif method in ["get", "delete", "options"]:
            # print(["# read,delete", method])
            response = getattr(self.session, method)(url)
        if response is not None:
            try:
                self.response = response
            except Exception as e:
                print(e)
        return response


class GitApi:
    """
    to use git api the git user must be configured for the sub process like:

    git config --global user.email "you@example.com"
    git config --global user.name "Your Name"
    
    """
    session = requests.Session()
    client = requests
    session.headers = {"Content-Type": "application/json"}

    def __init__(
        self,
        deployment,
        username: str = None,
        password: str = None,
        token: str = None,
        organization=None,
        GIT_URL: str = None,
        applicationset_manager_repository_name:str = "monotremata-clustermanager",
        applicationset_manager_organization_name:str = "wqdms",
        helm_folder_path: Path = settings.BASE_DIR / "helm-monotremata"
    ):
        self.GIT_URL = GIT_URL if GIT_URL else settings.GIT_URL
        self.username = username
        self.password = password
        self.token = token
        self.organization = organization
        self.deployment = deployment
        self.api_url = f"{self.GIT_URL}/api/v1"
        self.session.auth = (self.username, self.password)
        self.applicationset_manager_repository_name = applicationset_manager_repository_name
        self.applicationset_manager_organization_name = applicationset_manager_organization_name
        self.helm_folder_path = helm_folder_path

        if deployment and not organization:
            self.organization = deployment.organization

        self.token_name = f"{self.organization.name}-{self.deployment.project}-{self.deployment.git_organization_username}-token"

    def log(self, *args, **kwargs):
        print([args, kwargs])

    def url(self, url):
        if not str(url).startswith("/"):
            url = f"/{url}"
        return f"{self.api_url}{url}"

    def update_header(self, keystring="Bearer"):
        self.session.auth = (self.username, self.password)
        self.session.headers["Authorization"] = f"{keystring} {self.token}"

    def create_access_token(self):
        self.log("create_access_token")

        # first get then create
        try:
            r = self.session.post(
                url=self.url(f"/users/{self.username}/tokens"),
                json={
                    "name": self.token_name,
                    "scopes": [
                        "write:activitypub",
                        "write:misc",
                        "write:notification",
                        "write:organization",
                        "write:package",
                        "write:issue",
                        "write:repository",
                        "write:user",
                    ],
                },
                verify=False,
            )
            self.token = r.json()
            self.update_header()
            return self.token["sha1"] if "sha1" in self.token else None
        except Exception as e:
            error_message(str(e))
            return "No-Token"

    def delete_access_token(self):
        self.update_header()
        return self.session.delete(
            url=self.url(f"/users/{self.username}/tokens/{self.token_name}")
        )

    def delete_organization(self):
        self.update_header()
        return self.session.delete(
            url=self.url(f"/orgs/{self.organization.name.lower()}")
        )

    def create_organization(self):
        self.update_header()
        data = {
            # "name":f"{self.organization.name}",
            "description": "created by monotremata",
            # "email": f"mail@groupeffect.de",
            "email": f"{self.organization.name.lower()}@groupeffect.de",
            "full_name": f"{self.organization.name}",
            "location": str(),
            "repo_admin_change_team_access": True,
            "username": f"{self.organization.name.lower()}",
            "visibility": "public",
            "website": f"{self.deployment.service_public_url}",
        }
        r = self.session.post(
            url=self.url("/orgs"),
            json=data,
            verify=False,
        )
        try:
            return r.json()
        except Exception as e:
            error_message(str(e))
            return [e, r]

    def create_repository(self):
        data = {
            "auto_init": True,
            "default_branch": self.deployment.name.lower(),
            "description": self.deployment.project.description,
            "gitignores": None,
            "issue_labels": None,
            "license": None,
            "name": self.deployment.project.name.lower(),
            "object_format_name": "sha1",
            "private": False,
            "readme": None,
            "template": False,
            "trust_model": "default",
        }
        response = self.session.post(
            url=self.url(f"/orgs/{self.organization.name.lower()}/repos"), json=data
        )

        if response.status_code == 409:
            data = {"new_branch_name": self.deployment.name}
            response = self.session.post(
                url=self.url(
                    f"/repos/{self.organization.name.lower()}/{self.deployment.project.name.lower()}/branches"
                ),
                json=data,
            )
        return response

    def delete_repository(self):
        return self.session.delete(
            url=self.url(
                f"/repos/{self.organization.name.lower()}/{self.deployment.project.name.lower()}"
            ),
        )

    def write_project_zip_to_repository(self):
        if not self.deployment.git_token:
            return ["no-token-set"]
        d = DeploymentConfigLoader(self.deployment)
        p = ProjectZipFile(save_path="/tmp/mono.zip", response=d.load_zip())
        p.zip_as_folder()
        p.unzip_file()
        os.remove("/tmp/mono.zip")
        response = None
        if os.path.exists("/tmp/mono"):
            try:
                # clone repo
                response = subprocess.check_output(
                    [
                        "/bin/sh",
                        "-c",
                        f"cd /tmp && git clone {self.deployment.git_api_url.replace("://",f"://{self.deployment.git_token}@")}/{self.organization.name.lower()}/{self.deployment.project.name.lower()}.git",
                    ],
                )
            except Exception as e:
                error_message(str(e))
                print(e)
            print(response)

            # if repo downloaded copy to repo folder
            if os.path.exists(f"/tmp/{self.deployment.project.name.lower()}"):
                shutil.copytree(
                    f"/tmp/mono/{self.deployment.project.name.lower()}",
                    f"/tmp/{self.deployment.project.name.lower()}",
                    dirs_exist_ok=True,
                )
                try:
                    # git add
                    response = subprocess.check_output(
                        [
                            "/bin/sh",
                            "-c",
                            f"cd /tmp/{self.deployment.project.name.lower()} && git add -A",
                        ],
                    )
                except Exception as e:
                    print(e)
                try:
                    # git commit
                    response = subprocess.check_output(
                        [
                            "/bin/sh",
                            "-c",
                            f"cd /tmp/{self.deployment.project.name.lower()} && git commit -m 'mono update'",
                        ],
                    )
                except Exception as e:
                    print(e)

                try:
                    # git push
                    response = subprocess.check_output(
                        [
                            "/bin/sh",
                            "-c",
                            f"cd /tmp/{self.deployment.project.name.lower()} && git push",
                        ],
                    )
                except Exception as e:
                    error_message(str(e))
                    print(e)
                repo_name = self.applicationset_manager_repository_name
                org_name = self.applicationset_manager_organization_name
                try:
                    # clone repp cluste manager
                    if "applicationset" in self.deployment.script:

                        response = subprocess.check_output(
                            [
                                "/bin/sh",
                                "-c",
                                f"cd /tmp && git clone {self.deployment.git_api_url.replace("://",f"://{self.deployment.git_token}@")}/{org_name}/{repo_name}.git",
                            ],
                        )
                        
                        if os.path.exists(f"/tmp/{repo_name}"):
                            org_path = f"/tmp/{repo_name}/{self.deployment.organization.name.lower()}"
                            if not os.path.exists(org_path):
                                os.mkdir(org_path)
                            proj_path = f"{org_path}/{self.deployment.project.name.lower()}"
                            if not os.path.exists(proj_path):
                                os.mkdir(proj_path)
                            with open(f"{proj_path}/applicationset.yaml","w") as f:
                                f.write(self.deployment.script["applicationset"])
                            try:
                                shutil.copytree(
                                    self.helm_folder_path, 
                                    os.path.join(f"/tmp/{repo_name}","helm"),
                                    dirs_exist_ok=True
                                    )
                            except Exception as e:
                                error_message(str(e))
                            try:
                                response = subprocess.check_output([
                                    "/bin/sh",
                                    "-c",
                                    f"cd /tmp/{repo_name} && git add -A",
                                ])
                            except Exception as e:
                                error_message(str(e))   
                            try:
                                response = subprocess.check_output([
                                    "/bin/sh",
                                    "-c",
                                    f"cd /tmp/{repo_name} && git commit -m 'updated {self.deployment.name} {self.deployment.id}'",
                                ])
                            except Exception as e:
                                error_message(str(e))  
                                print(e)
                            try:
                                response = subprocess.check_output([
                                    "/bin/sh",
                                    "-c",
                                    f"cd /tmp/{repo_name} && git push",
                                ])
                            except Exception as e:
                                error_message(str(e))  
                                print(e)
                            
                except Exception as e:
                    error_message(str(e))  
                    print(response)


                if os.path.exists("/tmp/mono"):
                    shutil.rmtree("/tmp/mono")
                if os.path.exists(f"/tmp/{self.deployment.project.name.lower()}"):
                    shutil.rmtree(f"/tmp/{self.deployment.project.name.lower()}")
                if os.path.exists(f"/tmp/{repo_name}"):
                    shutil.rmtree(f"/tmp/{repo_name}")
                return response
        return response


class Command(BaseCommand):
    help = "Forgeo API and git manager"

    def add_arguments(self, parser):

        parser.add_argument(
            "-d",
            "--deployment",
            required=False,
            type=str,
            help=f"deployment name or id",
        )

        parser.add_argument(
            "-o",
            "--organization",
            required=False,
            type=str,
            help=f"organization name or id",
        )
        parser.add_argument(
            "-u",
            "--username",
            required=False,
            type=str,
            help=f"user name or id",
        )
        parser.add_argument(
            "-p",
            "--password",
            required=False,
            type=str,
        )
        parser.add_argument(
            "-g",
            "--git_url",
            required=False,
            default=None,
            type=str,
            help=f"git platform url http://... or https://...",
        )
        parser.add_argument(
            "-a",
            "--action",
            required=False,
            choices=["create", "delete"],
            type=str,
            help=f"create or delete target",
        )
        parser.add_argument(
            "-t",
            "--target",
            required=False,
            choices=["organization", "project", "user", "token"],
            type=str,
            help=f"use action on target choice",
        )

    def handle(self, *args, **options):
        _organization = options.get("organization")
        _git_url = options.get("git_url")
        _action = options.get("action")
        _target = options.get("target")
        _password = options.get("password")
        _username = options.get("username")
        _deployment = options.get("deployment")

        # delete_token = False
        # if _action in ["delete"] and _target in ["token"]:
        #     delete_token = True

        # create_organization = False
        # if _action in ["create"] and _target in ["organization"]:
        #     create_organization = True

        # org = None
        # if _organization and str(_organization).isdigit():
        #     org = Organization.objects.filter(id=int(_organization)).first()
        # elif _organization:
        #     org = Organization.objects.filter(name=str(_organization)).first()

        # depl = None
        # if _deployment and str(_organization).isdigit():
        #     depl = Deployment.objects.filter(id=int(_deployment)).first()
        # elif _deployment:
        #     depl = Deployment.objects.filter(name=str(_deployment)).first()

        # api = None
        # if depl or org:
        #     if delete_token:
        #         pp(api.delete_access_token())
        #         if depl:
        #             depl.git_token = None
        #             depl.save()

        #     api = GitApi(
        #         username=_username,
        #         password=_password,
        #         organization=org,
        #         deployment=depl,
        #         GIT_URL=_git_url,
        #     )
        #     pp(api.create_access_token())
        #     pp(api.__dict__)

        # if api:
        #     if create_organization:
        #         pp(api.create_organization())
