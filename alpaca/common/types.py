from typing import Any, Dict, List, Optional, Tuple, Union

RawData = Dict[str, Any]

# TODO: Refine this type
HTTPResult = Union[dict, List[dict], Any]
Credentials = Tuple[Optional[str], Optional[str], Optional[str]]
