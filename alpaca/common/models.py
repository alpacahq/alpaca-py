from pydantic import BaseModel
import pprint


class ValidateBaseModel(BaseModel, validate_assignment=True):
    """
    This model simply sets up BaseModel with the validate_assignment flag to True, so we don't have to keep specifying
    it or forget to specify it in our models where we want assignment validation
    """

    def __repr__(self):
        return pprint.pformat(self.dict(), indent=4)
