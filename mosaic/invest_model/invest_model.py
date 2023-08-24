import pydantic
import typing
from ..core import ObjMOSAIC



class InvestModelBase(ObjMOSAIC):
    pass


class InvestLongModel(InvestModelBase):

    buy_quote_rate: float = pydantic.Field(
        1, description="Fraction of quote portfolio to be used to buy asset")

    sell_base_rate: float = pydantic.Field(
        1, description="Fraction of base portfolio to be used to sell asset")

    def get_buy_quote_amount(self, portfolio):
        return (portfolio.quote_amount +
                portfolio.quote_exposed)*self.buy_quote_rate

    def get_sell_base_amount(self, portfolio):
        return portfolio.base_amount*self.sell_base_rate
