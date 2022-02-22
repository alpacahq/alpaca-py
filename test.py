from alpaca.broker.client import BrokerClient
from alpaca.broker.enums import AgreementType
from alpaca.broker.models import (Account, AccountCreationRequest, Agreement,
                                  Contact, Disclosures, Identity)
from alpaca.common.time import TimeFrame, TimeFrameUnit
from alpaca.data.clients import HistoricalDataClient
from alpaca.data.models import Bar, BarSet

disclosures = Disclosures(is_control_person=False, is_affiliated_exchange_or_finra=False, is_politically_exposed=False, immediate_family_exposed=False)
contact = Contact(email_address="ema3255@example.com", phone_number="+13477431078", street_address=["201 Main Street"], city="New York", state="NY")
identity = Identity(given_name="John", family_name="Doe", date_of_birth="1990-01-01", country_of_tax_residence="USA")
agreements = [Agreement(agreement=AgreementType.MARGIN, signed_at="2020-09-11T18:09:33Z", ip_address="185.13.21.99", revision="16.2021.05"),
              Agreement(agreement=AgreementType.ACCOUNT, signed_at="2020-09-11T18:09:33Z", ip_address="185.13.21.99", revision="16.2021.05"),
              Agreement(agreement=AgreementType.CUSTOMER, signed_at="2020-09-11T18:09:33Z", ip_address="185.13.21.99", revision="16.2021.05")]

account = AccountCreationRequest(contact=contact, identity=identity, disclosures=disclosures, agreements=agreements)


API_KEY = "CK495EVK05W87K06WL8D"
API_SECRET = "XXpICYAGoyxAn8KI6v74vhbzpWuiSRGKdftDDDxc"


client  = BrokerClient(API_KEY, API_SECRET, sandbox=True)

# client.create_account(account)

bar = {
          "t": "2021-04-01T00:00:00Z",
          "x": "CBSE",
          "o": 58800.01,
          "h": 58838,
          "l": 58756.07,
          "c": 58837.71,
          "v": 9.43435863,
          "n": 375,
          "vw": 58792.3224699778
      }

symbol = "BTCUSD"
barset = {
  "bars": [
      {
          "t": "2021-04-01T00:00:00Z",
          "x": "CBSE",
          "o": 58800.01,
          "h": 58838,
          "l": 58756.07,
          "c": 58837.71,
          "v": 9.43435863,
          "n": 375,
          "vw": 58792.3224699778
      },
      {
          "t": "2021-04-01T00:00:00Z",
          "x": "CBSE",
          "o": 32330.01,
          "h": 3338,
          "l": 38756.07,
          "c": 38837.71,
          "v": 3.43435863,
          "n": 975,
          "vw": 38792.3224699778
      }

  ],
  "symbol": "BTCUSD",
  "next_page_token": "QlRDVVNEfE18MjAyMS0wNC0wMVQxNjozOTowMC4wMDAwMDAwMDBafENCU0U="
}
# timeframe = TimeFrame.Minute
# timeframe = TimeFrame(1, TimeFrameUnit.Minute)
# TimeFrame.Hour = TimeFrame(1, TimeFrameUnit.Hour)
# TimeFrame.Day = TimeFrame(1, TimeFrameUnit.Day)
timeframe = '1Day'
# b = Bar(symbol=symbol, timeframe=timeframe, bar=bar)

api = "PK38CVGIP2DEWNQJSRDM"
secret = "BnXTibq13smhlqqPwHi0OBvqBzF0dYkLdosQf9oI"

s = HistoricalDataClient(api_key=api, secret_key=secret)

b = s.get_bars("SPY", timeframe, "2022-02-01")

print(b)

# bs = BarSet(barset['symbol'], timeframe, barset['bars'])

# print(bs)

# print(bs[0])