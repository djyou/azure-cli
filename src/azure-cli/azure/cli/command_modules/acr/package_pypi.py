# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
from six.moves.urllib.request import urlopen  # pylint: disable=import-error

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.util import in_cloud_console

from ._utils import user_confirmation

from ._docker_utils import (
    get_access_credentials,
    request_data_from_registry,
    PackageType,
    PackageAccessTokenPermission
)


logger = get_logger(__name__)


def acr_pypi_get_credential(cmd,
                            registry_name,
                            package_name=None,
                            tenant_suffix=None,
                            pull=False,
                            push=False,
                            delete=False):
    if package_name and not (pull or push or delete):
        raise CLIError('Usage error: --package-name must be used with one or more --pull --push --delete')
    if not package_name and (pull or push or delete):
        raise CLIError('Usage error: --pull --push --delete must be used with --package-name')

    # always add metadata read
    permission = PackageAccessTokenPermission.METADATA_READ.value

    if pull:
        permission = '{},{}'.format(permission, PackageAccessTokenPermission.PULL.value)
    if push:
        permission = '{},{}'.format(permission, PackageAccessTokenPermission.PUSH.value)
    if delete:
        permission = '{},{}'.format(permission, PackageAccessTokenPermission.DELETE.value)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        package_type=PackageType.PYPI,
        repository=package_name,
        permission=permission)

    token_info = {
        "endpoint": '{}/pkg/v1/pypi'.format(login_server), # TODO: get the endpoint from RP
        "username": username,
        "password": password
    }

    return token_info


def acr_pypi_list(cmd,
                  registry_name,
                  package_name=None,
                  tenant_suffix=None,
                  username=None,
                  password=None):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        package_type=PackageType.PYPI,
        repository=package_name,
        permission=PackageAccessTokenPermission.METADATA_READ.value)

    html = request_data_from_registry(
        http_method='get',
        login_server=login_server,
        path=_get_pypi_path(package_name),
        username=username,
        password=password)[0]

    print(html)


def acr_pypi_upload(cmd,
                    registry_name,
                    package_name,
                    file_path,
                    tenant_suffix=None,
                    username=None,
                    password=None):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        package_type=PackageType.PYPI,
        repository=package_name,
        permission=PackageAccessTokenPermission.PUSH.value)

    from subprocess import Popen
    p = Popen(['python', '-m', 'twine', 'upload',
               '--username', username,
               '--password', password,
               '--repository-url', 'https://{}/pkg/v1/pypi'.format(login_server), # TODO: get the endpoint from RP
               file_path])
    p.wait()


def acr_pypi_delete(cmd,
                    registry_name,
                    package_name,
                    version,
                    tenant_suffix=None,
                    username=None,
                    password=None,
                    yes=False):
    message = "This operation will delete the package '{}' version '{}'".format(package_name, version)
    user_confirmation("{}.\nAre you sure you want to continue?".format(message), yes)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        package_type=PackageType.PYPI,
        repository=package_name,
        permission=PackageAccessTokenPermission.DELETE.value)

    return request_data_from_registry(
        http_method='delete',
        login_server=login_server,
        path=_get_pypi_path(package_name, version),
        username=username,
        password=password)[0]


def _get_pypi_path(package_name, version=None):
    if not package_name:
        return '/pkg/v1/pypi'
    if not version:
        return '/pkg/v1/pypi/{}'.format(package_name)

    return '/pkg/v1/pypi/{}/{}'.format(package_name, version)
