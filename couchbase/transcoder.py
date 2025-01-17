#  Copyright 2016-2022. Couchbase, Inc.
#  All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License")
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import annotations

import json
import pickle  # nosec
from abc import ABC, abstractmethod
from typing import (TYPE_CHECKING,
                    Any,
                    Tuple,
                    Union)

from couchbase.constants import (FMT_BYTES,
                                 FMT_COMMON_MASK,
                                 FMT_JSON,
                                 FMT_LEGACY_MASK,
                                 FMT_PICKLE,
                                 FMT_UTF8)
from couchbase.exceptions import InvalidArgumentException, ValueFormatException
from couchbase.serializer import DefaultJsonSerializer

if TYPE_CHECKING:
    from couchbase.serializer import Serializer

UNIFIED_FORMATS = (FMT_JSON, FMT_BYTES, FMT_UTF8, FMT_PICKLE)
LEGACY_FORMATS = tuple([x & FMT_LEGACY_MASK for x in UNIFIED_FORMATS])
COMMON_FORMATS = tuple([x & FMT_COMMON_MASK for x in UNIFIED_FORMATS])

COMMON2UNIFIED = {}
LEGACY2UNIFIED = {}

for fl in UNIFIED_FORMATS:
    COMMON2UNIFIED[fl & FMT_COMMON_MASK] = fl
    LEGACY2UNIFIED[fl & FMT_LEGACY_MASK] = fl


def get_decode_format(flags):
    """
    Returns a tuple of format, recognized
    """
    c_flags = flags & FMT_COMMON_MASK
    l_flags = flags & FMT_LEGACY_MASK

    if c_flags:
        # if unknown format, default to FMT_BYTES
        return COMMON2UNIFIED.get(c_flags, FMT_BYTES)
    else:
        # if unknown format, default to FMT_BYTES
        return LEGACY2UNIFIED.get(l_flags, FMT_BYTES)


class Transcoder(ABC):
    """Interface a Custom Transcoder must implement
    """

    @abstractmethod
    def encode_value(self,
                     value  # type: Any
                     ) -> Tuple[bytes, int]:
        raise NotImplementedError()

    @abstractmethod
    def decode_value(self,
                     value,  # type: bytes
                     flags  # type: int
                     ) -> Any:
        raise NotImplementedError()


class JSONTranscoder(Transcoder):

    def __init__(self, serializer=None  # type: Serializer
                 ):

        if not serializer:
            self._serializer = DefaultJsonSerializer()
        else:
            self._serializer = serializer

    def encode_value(self,
                     value,  # type: Any
                     ) -> Tuple[bytes, int]:

        if isinstance(value, str):
            format = FMT_JSON
        elif isinstance(value, (bytes, bytearray)):
            raise ValueFormatException(
                "The JSONTranscoder (default transcoder) does not support binary data.")
        elif isinstance(value, (list, tuple, dict, bool, int, float)) or value is None:
            format = FMT_JSON
        else:
            raise ValueFormatException(
                "Unrecognized value type {}".format(type(value)))

        if format != FMT_JSON:
            raise ValueFormatException("Unrecognized format {}".format(format))

        return self._serializer.serialize(value), FMT_JSON

    def decode_value(self,
                     value,  # type: bytes
                     flags  # type: int
                     ) -> Any:

        format = get_decode_format(flags)

        if format == FMT_BYTES:
            raise ValueFormatException(
                "The JSONTranscoder (default transcoder) does not support binary format")
        elif format == FMT_UTF8:
            raise ValueFormatException(
                "The JSONTranscoder (default transcoder) does not support string format")
        elif format == FMT_JSON:
            return self._serializer.deserialize(value)
        else:
            raise ValueFormatException(
                "Unrecognized format provided: {}".format(format))


class RawJSONTranscoder(Transcoder):

    def encode_value(self,
                     value  # type: Union[str,bytes,bytearray]
                     ) -> Tuple[bytes, int]:

        if isinstance(value, str):
            return value.encode("utf-8"), FMT_JSON
        elif isinstance(value, (bytes, bytearray)):
            if isinstance(value, bytearray):
                value = bytes(value)
            return value, FMT_JSON
        else:
            raise ValueFormatException(
                "Only binary and string data supported by RawJSONTranscoder")

    def decode_value(self,
                     value,  # type: bytes
                     flags  # type: int
                     ) -> Union[str, bytes]:

        format = get_decode_format(flags)

        if format == FMT_BYTES:
            raise ValueFormatException(
                "Binary format type not supported by RawJSONTranscoder")
        elif format == FMT_UTF8:
            raise ValueFormatException(
                "String format type not supported by RawJSONTranscoder")
        elif format == FMT_JSON:
            if isinstance(value, str):
                return value.decode("utf-8")
            elif isinstance(value, (bytes, bytearray)):
                if isinstance(value, bytearray):
                    value = bytes(value)
                return value
            else:
                raise ValueFormatException(
                    "Only binary and string data supported by RawJSONTranscoder")
        else:
            raise InvalidArgumentException("Unexpected flags value.")


class RawStringTranscoder(Transcoder):

    def encode_value(self,
                     value  # type: str
                     ) -> Tuple[bytes, int]:

        if isinstance(value, str):
            return value.encode("utf-8"), FMT_UTF8
        else:
            raise ValueFormatException(
                "Only string data supported by RawStringTranscoder")

    def decode_value(self,
                     value,  # type: bytes
                     flags  # type: int
                     ) -> Union[str, bytes]:

        format = get_decode_format(flags)

        if format == FMT_BYTES:
            raise ValueFormatException(
                "Binary format type not supported by RawStringTranscoder")
        elif format == FMT_UTF8:
            return value.decode("utf-8")
        elif format == FMT_JSON:
            raise ValueFormatException(
                "JSON format type not supported by RawStringTranscoder")
        else:
            raise InvalidArgumentException("Unexpected flags value.")


class RawBinaryTranscoder(Transcoder):
    def encode_value(self,
                     value  # type: Union[bytes,bytearray]
                     ) -> Tuple[bytes, int]:

        if isinstance(value, (bytes, bytearray)):
            if isinstance(value, bytearray):
                value = bytes(value)
            return value, FMT_BYTES
        else:
            raise ValueFormatException(
                "Only binary data supported by RawBinaryTranscoder")

    def decode_value(self,
                     value,  # type: bytes
                     flags  # type: int
                     ) -> bytes:

        format = get_decode_format(flags)

        if format == FMT_BYTES:
            if isinstance(value, bytearray):
                value = bytes(value)
            return value
        elif format == FMT_UTF8:
            raise ValueFormatException(
                "String format type not supported by RawBinaryTranscoder")
        elif format == FMT_JSON:
            raise ValueFormatException(
                "JSON format type not supported by RawBinaryTranscoder")
        else:
            raise InvalidArgumentException("Unexpected flags value.")


class LegacyTranscoder(Transcoder):

    def encode_value(self,
                     value  # type: Any
                     ) -> Tuple[bytes, int]:

        if isinstance(value, str):
            format = FMT_UTF8
        elif isinstance(value, (bytes, bytearray)):
            format = FMT_BYTES
        elif isinstance(value, (list, tuple, dict, bool, int, float)) or value is None:
            format = FMT_JSON
        else:
            format = FMT_PICKLE

        if format == FMT_BYTES:
            if isinstance(value, bytes):
                pass
            elif isinstance(value, bytearray):
                value = bytes(value)
            else:
                raise ValueFormatException("Expected bytes")

            return value, format

        elif format == FMT_UTF8:
            return value.encode('utf-8'), format

        elif format == FMT_PICKLE:
            return pickle.dumps(value), FMT_PICKLE

        elif format == FMT_JSON:
            return json.dumps(value, ensure_ascii=False).encode("utf-8"), FMT_JSON

        else:
            raise ValueFormatException("Unrecognized format {}".format(format))

    def decode_value(self,
                     value,  # type: bytes
                     flags  # type: int
                     ) -> Any:

        format = get_decode_format(flags)

        if format == FMT_BYTES:
            return value
        elif format == FMT_UTF8:
            return value.decode("utf-8")
        elif format == FMT_JSON:
            try:
                return json.loads(value.decode('utf-8'))
            except Exception:
                # if error encountered, assume return bytes
                return value
        elif format == FMT_PICKLE:
            return pickle.loads(value)  # nosec
        else:
            # default to returning bytes
            return value
