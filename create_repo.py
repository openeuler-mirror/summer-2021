import argparse
import logging
import os
import requests
import sys
import yaml


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename='./create_repo.log', level=logging.INFO, format=LOG_FORMAT)


def load_yaml(filepath):
    """
    Load a yaml file
    :param filepath: the path of yaml file
    :return: the content of yaml file or False with format error
    """
    filename = os.path.basename(filepath)
    try:
        result = yaml.load(open(filepath, encoding='utf-8'), Loader=yaml.Loader)
        if not result:
            logging.error('{} is a empty file'.format(filename))
            raise ValueError('yaml is empty')
    except FileNotFoundError:
        logging.error("The file {} does not exist".format(filename))
        sys.exit(1)
    except yaml.MarkedYAMLError as e:
        logging.error(e)
        sys.exit(1)
    return result


def check_repos_exist(org, access_token, repo_name):
    """
    Check whether a repo exists
    :param org: name of organization
    :param access_token: access_token
    :param repo_name: repo name
    :return: True if exists or False
    """
    repo_info_url = 'https://gitee.com/api/v5/repos/{}/{}'.format(org, repo_name)
    param = {
        "access_token": access_token,
    }
    response = requests.get(repo_info_url, params=param)
    if response.status_code != 200:
        return False
    return True


def check_and_create_repos(org, url, parameters, data, repo_path):
    """
    Add admin and member for a repo
    :param org: organization
    :param url: post url
    :param parameters: params for creating a repo
    :param data: a dict of competition question information
    :param repo_path: repo name for the competition question
    :return:
    """
    access_token = parameters['access_token']
    repo_name = parameters['name']
    if not check_repos_exist(org, access_token, repo_path):
        response = requests.post(url, params=parameters)
        if response.status_code != 201:
            logging.error('Fail to create repo {}, status_code:{}'.format(repo_name, response.status_code))
            logging.error(response.text)
            return False
        logging.info('Create repo {} successfully'.format(repo_name))
        reviewer_conf_url = 'https://gitee.com/api/v5/repos/{}/{}/reviewer'.format(org, repo_path)
        payload = {
            'access_token': access_token,
            'assignees': '',
            'testers': '',
            'assignees_number': 0,
            'testers_number': 0
        }
        r = requests.put(reviewer_conf_url, data=payload)
        if r.status_code != 200:
            logging.error('Fail to set assignees and testers')
            logging.error(r.text)
            sys.exit(1)
        add_tutor(org, data, access_token)
        add_member(org, data, access_token)
    else:
        add_tutor(org, data, access_token)
        add_member(org, data, access_token)


def add_tutor(org, data, access_token):
    """
    Add a admin for the repo
    :param org: organization
    :param data: a dict of competition question information
    :param access_token: access_token
    :return:
    """
    for user in data['tutor']:
        if user['giteeid']:
            repo = data['path'].split('/')[-1]
            gitee_id = user['giteeid']
            tutor_url = 'https://gitee.com/api/v5/repos/{}/{}/collaborators/{}'.format(org, repo, gitee_id)
            params = {
                "access_token": access_token,
                "permission": "admin"
            }
            response = requests.put(tutor_url, params=params)
            if response.status_code == 200:
                logging.info('Add admin {} for repo {}'.format(gitee_id, repo))
            else:
                logging.error('Fail to add admin {} for repo {}, ErrorMsg: {}'.format(gitee_id, repo, response.text))


def add_member(org, data, access_token):
    """
    Add a member for the repo
    :param org: organization
    :param data: a dict of competition question information
    :param access_token: access_token
    :return:
    """
    for user in data['member']:
        if user['giteeid']:
            repo = data['path'].split('/')[-1]
            gitee_id = user['giteeid']
            member_url = 'https://gitee.com/api/v5/repos/{}/{}/collaborators/{}'.format(org, repo, gitee_id)
            params = {
                "access_token": access_token,
                "permission": "push"
            }
            response = requests.put(member_url, params=params)
            if response.status_code == 200:
                logging.info('Add member {} for repo {}'.format(gitee_id, repo))
            else:
                logging.error('Fail to add member {} for repo {}, ErrorMsg: {}'.format(gitee_id, repo, response.text))


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', type=str, help='path of configure file')
    parser.add_argument('organization', type=str, help='organization')
    parser.add_argument('access_token', type=str, help='gitee access_token')
    args = parser.parse_args()
    org = args.organization
    yaml_information = load_yaml(args.filepath)
    create_url = 'https://gitee.com/api/v5/orgs/{}/repos'.format(org)
    for repository in yaml_information['repositories']:
        description = repository['description']
        name = repository['name']
        repo_path = repository['path'].split('/')[-1]
        param = {
            "access_token": args.access_token,
            "name": name,
            "description": description,
            "has_issues": 'true',
            "has_wiki": 'true',
            "can_comment": 'true',
            "org": org,
            "auto_init": 'true',
            "public": 1,
            'license_template': 'MulanPSL-2.0',
            "path": repo_path
        }
        check_and_create_repos(org, create_url, param, repository, repo_path)


if __name__ == '__main__':
    main()

