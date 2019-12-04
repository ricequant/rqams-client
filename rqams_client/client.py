# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。


from typing import Type
from functools import wraps
from urllib.parse import urljoin

import requests
from logbook import Logger, DEBUG, INFO

from .cls import DictProxy
from .models import AssetUnit, Account, Broker
from .utils import ReqestException, jsonable


def retry(times: int = 3, error: Type[Exception] = Exception):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for i in range(1, times + 1):
                try:
                    return f(*args, **kwargs)
                except error:
                    if i == times:
                        raise
                    continue
        return wrapper
    return decorator


class RQAMSClient:
    def __init__(
        self, username: str = None, password: str = None, sid: str = None,
        server_url: str = "https://www.ricequant.com", debug=False, requests_timeout: int = 10, logger=None
    ):
        self._server_url = urljoin(server_url, "/api/rqams_open/v1")
        self._requests_timeout = requests_timeout
        self._logger = logger or Logger("RQAMS_CLIENT")
        self._logger.level = DEBUG if debug else INFO

        self._username = username
        if sid:
            self._sid = sid
        else:
            rsp = self.req("POST", "/login", need_logged_in=False, json={"username": username, "password": password})
            self._sid = rsp.cookies["sid"]
            self._user_id = rsp.json()["user_id"]

    @property
    def user_id(self):
        try:
            return self._user_id
        except AttributeError:
            raise AttributeError(f"{self.__class__.__name__} object has no attribute user_id")

    @property
    def sid(self):
        return self._sid

    @property
    def asset_units(self) -> DictProxy[str, AssetUnit]:
        return DictProxy(get_func=lambda: {i["id"]: AssetUnit.from_dict(
            i, client=self
        ) for i in self.req("GET", "/asset_units").json()["asset_units"]})

    @property
    def accounts(self) -> DictProxy[str, Account]:
        return DictProxy(
            get_func=lambda: {
                i["account"]: Account.from_dict(i, client=self) for i in self.req("GET", "/accounts").json()["accounts"]
            },
            del_func=lambda account: self.req("DELETE", f"/accounts/{account}"),
            set_func=lambda k, v: self.req("POST", f"/accounts", json={"account": {
                "name": v.name,
                "account": v.account,
                "broker": v.broker.id,
                "asset_unit": v.asset_unit.id,
                "portfolio": v.portfolio.id
            }})
        )

    @property
    def brokers(self) -> DictProxy[str, Broker]:
        return DictProxy(get_func=lambda: {
            i["id"]: Broker.from_dict(i) for i in self.req("GET", "/brokers").json()["brokers"]
        })

    @retry(3, requests.exceptions.RequestException)
    def req(self, method, url, need_logged_in=True, **kwargs) -> requests.Response:
        # TODO use session for each thread
        if "data" in kwargs:
            kwargs["data"] = jsonable(kwargs["data"])
        if "json" in kwargs:
            kwargs["json"] = jsonable(kwargs["json"])
        if need_logged_in:
            kwargs.update({"cookies": {"sid": self._sid}})
        self._logger.debug(self._server_url + url)
        response = requests.request(method, self._server_url + url, timeout=self._requests_timeout, **kwargs)
        self._logger.debug(f"\"{method} {self._server_url + url}\" {response.status_code}")
        if response.status_code != 200:
            raise ReqestException(
                f"request rqams failed:{self._server_url + url}, {response.status_code}, {response.text}", response
            )
        return response
