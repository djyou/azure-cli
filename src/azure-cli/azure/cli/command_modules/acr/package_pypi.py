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
    RegistryException,
    PackageType,
    PackageAccessTokenPermission
)


logger = get_logger(__name__)


def acr_package_pypi_get_credential(cmd,
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
    permission = PackageAccessTokenPermission.METADATA_READ

    if pull:
        permission = '{},{}'.format(permission, PackageAccessTokenPermission.PULL)
    if push:
        permission = '{},{}'.format(permission, PackageAccessTokenPermission.PUSH)
    if delete:
        permission = '{},{}'.format(permission, PackageAccessTokenPermission.DELETE)

    loginServer, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        package_type=PackageType.PYPI,
        repository=package_name,
        permission=permission)

    token_info = {
        "endpoint": 'https://{}/pkg/v1/pypi'.format(loginServer),
        "username": username,
        "password": password
    }

    return token_info


def acr_package_pypi_list(cmd,
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
        path=_get_package_pypi_path(package_name),
        username=username,
        password=password)[0]

    print(html)


def _get_package_pypi_path(package_name):
    return '/pkg/v1/pypi/{}'.format(package_name) if package_name else '/pkg/v1/pypi'
