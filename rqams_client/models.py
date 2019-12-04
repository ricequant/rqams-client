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


from enum import Enum
from datetime import date, datetime
from numbers import Real
from typing import Sequence, List, Optional

from .cls import DictProxy, property_class, DictConvertMixin

__all__ = [
    "Direction",
    "Portfolio",
    "Product",
    "Position",
    "SettlementInfo",
    "AssetUnit",
    "Broker",
    "Account",
]


class Direction(Enum):
    LONG = "long"
    SHORT = "short"


class Side(Enum):
    BUY = "buy"
    SELL = "sell"

    BUY_OPEN = "buy_open"
    BUY_CLOSE = "buy_close"
    BUY_CLOSE_TODAY = "buy_close_today"
    SELL_OPEN = "sell_open"
    SELL_CLOSE = "sell_close"
    SELL_CLOSE_TODAY = "sell_close_today"


@property_class
class Trade(DictConvertMixin):
    exec_id: str
    datetime: datetime
    order_book_id: str
    side: Side
    last_quantity: float
    last_price: float
    transaction_cost: float


@property_class
class Portfolio(DictConvertMixin):
    id: str
    name: str

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    @property
    def trades(self) -> DictProxy[str, Trade]:
        return DictProxy(update_func=lambda trades: self._client.req(
            "POST", f"/portfolios/{self.id}/trades:append_multi_json",
            json={"trades": [t.to_dict() for t in trades.values()]}
        ))


@property_class
class Product(DictConvertMixin):
    id: str
    name: str
    case_num: str


@property_class
class Position:
    order_book_id: str
    direction: Direction
    quantity: Real


@property_class
class SettlementInfo:
    date: date
    total_equity: Real
    cash: Real
    positions: Sequence[Position]


@property_class
class AssetUnit(DictConvertMixin):
    id: str
    name: str

    @property
    def portfolios(self) -> DictProxy[str, Portfolio]:
        return DictProxy(get_func=lambda: {
            i["id"]: Portfolio.from_dict(i, client=self._client) for i in self._get_detail()["portfolios"]
        })

    @property
    def product(self) -> Product:
        detail = self._get_detail()
        if "product" in detail:
            return Product.from_dict(detail["product"])

    @property
    def cash_in_outs(self) -> DictProxy[date, Real]:
        return DictProxy(update_func=lambda cash_in_outs: self._client.req(
            "POST", f"/asset_units/{self._id}/cash_in_outs", data={
                "cash_in_outs": [{"date": k, "amount": v} for k, v in cash_in_outs.items()]
            }
        ))

    @property
    def settlement_info(self) -> DictProxy[date, SettlementInfo]:
        return DictProxy(update_func=lambda settlement_info: self._client.req("POST", f"/settlement_info", data={
            "settlement_info": [s.to_doc() for s in settlement_info.values()]
        }))

    def _get_detail(self):
        return self._client.req("GET", f"/asset_units/{self.id}").json()["asset_unit"]


@property_class
class Broker(DictConvertMixin):
    id: str
    name: str
    broker_id: str
    trade_frontend_urls: List[str]
    user_product_info: str
    auth_code: str
    app_id: str


@property_class
class Account(DictConvertMixin):
    name: str
    account: str
    broker: Broker
    portfolio: Portfolio
    asset_unit: AssetUnit
    product: Product

    def _before_set__portfolio(self, portfolio: Portfolio):
        if not isinstance(portfolio, Portfolio):
            raise TypeError(f"attribution portfolio must be an instance of Portfolio, not {type(portfolio)}")
        if not self._client:
            raise AttributeError("can't set attribute portfolio")
        self._client.req("PATCH", f"/accounts/{self.account}", json={"account": {"portfolio": portfolio.id}})
