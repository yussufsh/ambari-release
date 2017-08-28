"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from ambari_commons.os_check import OSCheck
from resource_management.libraries.resources.repository import Repository
from resource_management.core.logger import Logger
import ambari_simplejson as json # simplejson is much faster comparing to Python 2.6 json module and has the same functions set.
import platform

def _is_powerpc():
  return platform.processor() == 'powerpc' or platform.machine().startswith('ppc')

# components_lits = repoName + postfix
_UBUNTU_REPO_COMPONENTS_POSTFIX = ["main"]

def _alter_repo(action, repo_string, repo_template):
  """
  @param action: "delete" or "create"
  @param repo_string: e.g. "[{\"baseUrl\":\"http://public-repo-1.hortonworks.com/HDP/centos6/2.x/updates/2.0.6.0\",\"osType\":\"centos6\",\"repoId\":\"HDP-2.0._\",\"repoName\":\"HDP\",\"defaultBaseUrl\":\"http://public-repo-1.hortonworks.com/HDP/centos6/2.x/updates/2.0.6.0\"}]"
  """
  repo_dicts = json.loads(repo_string)

  if not isinstance(repo_dicts, list):
    repo_dicts = [repo_dicts]

  if 0 == len(repo_dicts):
    Logger.info("Repository list is empty. Ambari may not be managing the repositories.")
  else:
    Logger.info("Initializing {0} repositories".format(str(len(repo_dicts))))

  for repo in repo_dicts:
    if not 'baseUrl' in repo:
      repo['baseUrl'] = None
    if not 'mirrorsList' in repo:
      repo['mirrorsList'] = None
    # TODO : CUSTOM CODE
    # hybrid (ppc) code goes here
    # need to edit the repo file if os arch is ppc
    Logger.info("Check if ppc and rhel7")
    if _is_powerpc() and OSCheck.is_redhat_family():
      if repo['repoName'] == "HDP":
        repo['baseUrl'] = repo['baseUrl'].replace('centos7','centos7-ppc')
        Logger.info("changed hdp url to {0}".format(str(repo['baseUrl'])))
      if repo['repoName'] == "HDP-UTILS":
        repo['baseUrl'] = repo['baseUrl'].replace('centos7', 'ppc64le')
        Logger.info("changed hdputils url to {0}".format(str(repo['baseUrl'])))
    # hybrid (ppc) code ends here
    
    ubuntu_components = [ repo['repoName'] ] + _UBUNTU_REPO_COMPONENTS_POSTFIX
    
    Repository(repo['repoId'],
               action = action,
               base_url = repo['baseUrl'],
               mirror_list = repo['mirrorsList'],
               repo_file_name = repo['repoName'],
               repo_template = repo_template,
               components = ubuntu_components, # ubuntu specific
    )

def install_repos():
  import params
  if params.host_sys_prepped:
    return

  template = params.repo_rhel_suse if OSCheck.is_suse_family() or OSCheck.is_redhat_family() else params.repo_ubuntu
  _alter_repo("create", params.repo_info, template)
  if params.service_repo_info:
    _alter_repo("create", params.service_repo_info, template)
