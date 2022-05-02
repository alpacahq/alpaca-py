from alpaca.broker.models import W8BenDocument


def create_dummy_w8ben_document() -> W8BenDocument:
    return W8BenDocument(
        country_citizen="Canada",
        date="2022-02-02",
        date_of_birth="2022-02-02",
        full_name="Beans",
        ip_address="192.168.1.1",
        permanent_address_city_state="Ontario",
        permanent_address_country="Canada",
        permanent_address_street="12345 Fake St",
        revision="123123",
        signer_full_name="Fake Name",
        timestamp="2022-04-29T09:30:00-04:00",
        tax_id_ssn="fake ssn",
    )
