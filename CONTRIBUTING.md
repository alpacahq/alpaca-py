Contributing to Alpaca-Py
=========================


Thank you for taking the time to contribute!
Alpaca-Py is currently in an early alpha phase, but we are very open to taking contributions!

## How do I file a bug/Ask a question/Request a feature?

We track these here on Github via our [issues](https://github.com/alpacahq/alpaca-py/issues/new/choose), with a template
for each of these cases that will ask you to fill out some information to better help us solve your issue.
(Note that not filling out the template or skipping questions is likely to just delay us being able to solve your issue
and will result in us having to ask you to fill out the missing information or close out your issue for being invalid.)

> **NOTE** that we can only solve issues with the SDK, if you are trying to report an issue with the API itself, then
> please open an issue over [here](https://github.com/alpacahq/Alpaca-API) instead.

## How do I contribute code?

1. Please fork this repo and create a branch for your changes
2. Please read the README steps on setting up the dev environment so that things like git pre-commit hooks are run on
   your code. This is to help prevent your PR getting rejected by the lint CI actions when you open your PR.
3. Code away
4. Open a PR with your changes!

That's the high level flow of it. Note that this repo uses merge commits so don't feel the need to squash your commits
before your pr.

### Dev setup

This project is managed via poetry so setup should be just running `poetry install`.

This repo is using [`pre-commit`](https://pre-commit.com/) to setup some checks to happen at commit time to keep the
repo clean. To set these up after you've run `poetry install` just run `poetry run pre-commit install` to have
pre-commit setup these hooks

## Coding Guidelines

### Formatting

This repo is using [Black](https://github.com/psf/black) as our formatter and style enforcer, if you're unsure if your
code will fit our style guide simply run

`poetry run black .`

from the root of the repo and Black will take care of formatting your code correctly for you.

### Conventions

We only have a few conventions we follow.

[//]: # (In the future put commit conventions here if we ever embrace them, ie conventional commits)

#### Models

We use [Pydantic](https://pydantic-docs.helpmanual.io/) for our models and for representing request objects. This lets
us add both type and custom validations to the models. If your PR needs to add a new model for some reason please make
sure it extends the `alpaca.common.models.ValidateBaseModel` class and implements a pydantic validator if needed to
ensure that models are always in a consistent state.

If what you're adding is a model for a request, IE `GetNewThingRequest` then please make sure it instead extends the
`alpaca.common.models.NonEmptyRequest` class. This class is a helper that extends the ValidateBaseModel to also add a
method called `to_request_fields` that eases the conversion of fields to safe HTTP request values.

#### Request Methods

Our request methods try to stick to a simple formula.

For example, lets take the Trading api method `remove_symbol_from_watchlist_by_id` and reverse engineer the naming here.
The url for this request is `DELETE /v2/watchlists/{watchlist_id}/{symbol}`

1. All url parameters shall be full parameters in the resulting method. So for our example we'll have a `watchlist_id`
   and `symbol` parameters.

2. Any GET/POST/PATCH/PUT parameters that a request can take should be turned into a new class that extends
   `alpaca.common.models.NonEmptyRequest`. Doing so will not only make the request method easier to write but also
   ensures that we have validation for the user almost for free from Pydantic. This also helps ensure that the addition
   of new fields here wont result in a breaking change.

   Our example doesn't have any DELETE parameters but if it did take any we would have a final parameter of a new type
   named `RemoveSymbolFromWatchlistRequest`.

3. Naming of the request method should be pretty obvious in most cases (`create_order`, `get_clock`, etc). But in
   certain cases, especially in the Broker module or when a request has multiple url parameters we try to follow a
   naming convention like the following:
   `{verb}_{noun}_by_{value}` or `{verb}_{noun1}_(for, from, to, etc)_{noun2}`or `{verb}_{noun1}_for_{noun2}_by_{value}`

   - step 1: is to get the verb we need. In this case its DELETE but for a more semantic name we'll use remove
   - step 2: what are the nouns we're working on, in this case its Watchlists and Symbols
   - step 3: The main noun in this case is Watchlist, and we specify which Watchlist we wish to update via its id, so we
     will add on a `by_id` to the end.

   and thus we end up with `remove_symbol_from_watchlist_by_id`.

> **NOTE**: Currently during the alpha phase of alpaca-py we haven't been strict on the above naming scheme. However,
> this **_will_** change in the future before we hit 1.0.0

And so the final method looks like:

```python
def remove_symbol_from_watchlist_by_id(self, watchlist_id: UUID, symbol: str) -> Watchlist:
```
