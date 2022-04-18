Broker API Models
===================

Due to the sheer number of models that the Broker API modules have they have been split out both internally
and here in the docs for ease of readability.

*Note*: Even though they are separated into submodules, all models are still accessible from ``alpaca.broker.models``
directly.

For example:

.. code-block:: python

  # Here we import a Request model directly from models module
  from alpaca.broker.models import ListAccountsRequest
  from alpaca.broker.enums import AccountEntities
  from alpaca.broker.client import BrokerClient

  accounts = client.list_accounts(
    ListAccountsRequest(
      entities=[AccountEntities.IDENTITY]
    )
  )


.. toctree::
   :caption: Here are the submodules:
   :glob:

   broker/models/*
