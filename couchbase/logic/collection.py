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

from typing import (TYPE_CHECKING,
                    Any,
                    Dict,
                    Iterable,
                    Optional,
                    Union)

from couchbase.exceptions import InvalidArgumentException
from couchbase.logic.options import DeltaValueBase, SignedInt64Base
from couchbase.options import forward_args
from couchbase.pycbc_core import (binary_operation,
                                  kv_operation,
                                  operations,
                                  subdoc_operation)
from couchbase.result import (CounterResult,
                              ExistsResult,
                              GetResult,
                              LookupInResult,
                              MutateInResult,
                              MutationResult)
from couchbase.subdocument import (Spec,
                                   StoreSemantics,
                                   SubDocOp)
from couchbase.transcoder import Transcoder

if TYPE_CHECKING:
    from datetime import timedelta

    from couchbase._utils import JSONType
    from couchbase.options import (AppendOptions,
                                   DecrementOptions,
                                   ExistsOptions,
                                   IncrementOptions,
                                   InsertOptions,
                                   MutateInOptions,
                                   PrependOptions,
                                   RemoveOptions,
                                   ReplaceOptions,
                                   TouchOptions,
                                   UnlockOptions,
                                   UpsertOptions)


class CollectionLogic:
    def __init__(self, scope, name):
        if not scope:
            raise InvalidArgumentException(message="Collection must be given a scope")
        # if not scope.connection:
        #     raise RuntimeError("No connection provided")
        self._scope = scope
        self._collection_name = name
        self._connection = scope.connection

    @property
    def default_transcoder(self) -> Optional[Transcoder]:
        return self._scope.default_transcoder

    @property
    def name(self) -> str:
        """
            str: The name of this :class:`~.Collection` instance.
        """
        return self._collection_name

    def _set_connection(self):
        """
        **INTERNAL**
        """
        self._connection = self._scope.connection

    def _get_connection_args(self) -> Dict[str, Any]:
        return {
            "conn": self._connection,
            "bucket": self._scope.bucket_name,
            "scope": self._scope.name,
            "collection_name": self.name
        }

    def get(
        self,
        key,  # type: str
        **kwargs,  # type: Dict[str, Any]
    ) -> Optional[GetResult]:
        """**INTERNAL**

        Key-Value *get* operation.  Should only be called by classes that inherit from the base
            class :class:`~couchbase.logic.CollectionLogic`.

        Args:
            key (str): document key
            opts (:class:`~.options.GetOptions`): options to provide
                for _get_ KV operation
            kwargs (Dict[str, Any]): keyword arguments that can be used in place or to
                overrride provided :class:`~.options.GetOptions`

        Raises:
            :class:`~.exceptions.InvalidArgumentException`: When attempting a get projection
                operation with more than 16 projections.
            :class:`~.exceptions.DocumentNotFoundException`: If the provided document key does not exist.
        """
        projections = kwargs.get("project")
        if isinstance(projections, list) and len(projections) > 16:
            raise InvalidArgumentException(
                f"Maximum of 16 projects allowed. Provided {len(projections)}"
            )
        op_type = operations.GET.value
        return kv_operation(**self._get_connection_args(),
                            **kwargs,
                            key=key,
                            op_type=op_type)

    def exists(
        self,
        key,  # type: str
        *opts,  # type: ExistsOptions
        **kwargs,  # type: Any
    ) -> Optional[ExistsResult]:
        op_type = operations.EXISTS.value
        return kv_operation(
            **self._get_connection_args(), **forward_args(kwargs, *opts), key=key, op_type=op_type
        )

    def insert(
        self,
        key,  # type: str
        value,  # type: JSONType
        *opts,  # type: InsertOptions
        **kwargs,  # type: Any
    ) -> Optional[MutationResult]:
        final_args = forward_args(kwargs, *opts)
        transcoder = final_args.pop('transcoder', self.default_transcoder)
        transcoded_value = transcoder.encode_value(value)
        op_type = operations.INSERT.value
        return kv_operation(
            **self._get_connection_args(),
            **final_args,
            key=key,
            value=transcoded_value,
            op_type=op_type,
        )

    def upsert(
        self,
        key,  # type: str
        value,  # type: JSONType
        *opts,  # type: UpsertOptions
        **kwargs,  # type: Any
    ) -> Optional[MutationResult]:
        final_args = forward_args(kwargs, *opts)
        transcoder = final_args.pop('transcoder', self.default_transcoder)
        transcoded_value = transcoder.encode_value(value)

        op_type = operations.UPSERT.value
        return kv_operation(
            **self._get_connection_args(),
            **final_args,
            key=key,
            value=transcoded_value,
            op_type=op_type,
        )

    def replace(self,
                key,  # type: str
                value,  # type: JSONType
                *opts,  # type: ReplaceOptions
                **kwargs,  # type: Any
                ) -> Optional[MutationResult]:
        final_args = forward_args(kwargs, *opts)
        expiry = final_args.get("expiry", None)
        preserve_expiry = final_args.get("preserve_expiry", False)
        if expiry and preserve_expiry is True:
            raise InvalidArgumentException(
                "The expiry and preserve_expiry options cannot both be set for replace operations."
            )

        transcoder = final_args.pop('transcoder', self.default_transcoder)
        transcoded_value = transcoder.encode_value(value)

        op_type = operations.REPLACE.value
        return kv_operation(
            **self._get_connection_args(),
            **final_args,
            key=key,
            value=transcoded_value,
            op_type=op_type,
        )

    def remove(self,
               key,  # type: str
               *opts,  # type: RemoveOptions
               **kwargs,  # type: Any
               ) -> Optional[MutationResult]:
        op_type = operations.REMOVE.value
        return kv_operation(
            **self._get_connection_args(), **forward_args(kwargs, *opts), key=key, op_type=op_type
        )

    def touch(self,
              key,  # type: str
              expiry,  # type: timedelta
              *opts,  # type: TouchOptions
              **kwargs,  # type: Any
              ) -> Optional[MutationResult]:
        kwargs["expiry"] = expiry
        op_type = operations.TOUCH.value
        return kv_operation(
            **self._get_connection_args(), **forward_args(kwargs, *opts), key=key, op_type=op_type
        )

    def get_and_touch(self,
                      key,  # type: str
                      **kwargs,  # type: Any
                      ) -> Optional[GetResult]:
        op_type = operations.GET_AND_TOUCH.value
        return kv_operation(
            **self._get_connection_args(), **kwargs, key=key, op_type=op_type
        )

    def get_and_lock(self,
                     key,  # type: str
                     **kwargs,  # type: Any
                     ) -> Optional[GetResult]:
        op_type = operations.GET_AND_LOCK.value
        return kv_operation(
            **self._get_connection_args(), **kwargs, key=key, op_type=op_type
        )

    def unlock(self,
               key,  # type: str
               cas,  # type: int
               *opts,  # type: UnlockOptions
               **kwargs,  # type: Any
               ) -> None:
        op_type = operations.UNLOCK.value
        return kv_operation(
            **self._get_connection_args(),
            **forward_args(kwargs, *opts),
            key=key,
            cas=cas,
            op_type=op_type,
        )

    def lookup_in(self,
                  key,  # type: str
                  spec,  # type: Iterable[Spec]
                  **kwargs,  # type: Any
                  ) -> Optional[LookupInResult]:
        op_type = operations.LOOKUP_IN.value
        return subdoc_operation(
            **self._get_connection_args(),
            **kwargs,
            key=key,
            spec=spec,
            op_type=op_type,
        )

    def mutate_in(
        self,
        key,  # type: str
        spec,  # type: Iterable[Spec]
        *opts,  # type: MutateInOptions
        **kwargs,  # type: Any
    ) -> Optional[MutateInResult]:
        # no tc for sub-doc, use default JSON
        final_args = forward_args(kwargs, *opts)
        transcoder = final_args.pop('transcoder', self.default_transcoder)

        expiry = final_args.get('expiry', None)
        preserve_expiry = final_args.get('preserve_expiry', False)

        spec_ops = [s[0] for s in spec]
        if SubDocOp.DICT_ADD in spec_ops and preserve_expiry is True:
            raise InvalidArgumentException(
                'The preserve_expiry option cannot be set for mutate_in with insert operations.')

        if SubDocOp.REPLACE in spec_ops and expiry and preserve_expiry is True:
            raise InvalidArgumentException(
                'The expiry and preserve_expiry options cannot both be set for mutate_in with replace operations.')

        """
            @TODO(jc): document that the kwarg will override option:
            await cb.mutate_in(key,
                (SD.upsert('new_path', 'im new'),),
                MutateInOptions(store_semantics=SD.StoreSemantics.INSERT),
                upsert_doc=True)

                will set store_semantics to be UPSERT
        """

        insert_semantics = final_args.pop('insert_doc', None)
        upsert_semantics = final_args.pop('upsert_doc', None)
        replace_semantics = final_args.pop('replace_doc', None)
        if insert_semantics is not None and (upsert_semantics is not None or replace_semantics is not None):
            raise InvalidArgumentException("Cannot set multiple store semantics.")
        if upsert_semantics is not None and (insert_semantics is not None or replace_semantics is not None):
            raise InvalidArgumentException("Cannot set multiple store semantics.")

        if insert_semantics is not None:
            final_args["store_semantics"] = StoreSemantics.INSERT
        if upsert_semantics is not None:
            final_args["store_semantics"] = StoreSemantics.UPSERT
        if replace_semantics is not None:
            final_args["store_semantics"] = StoreSemantics.REPLACE

        final_spec = []
        for s in spec:
            if len(s) == 6:
                new_value = transcoder.encode_value(s[5])
                tmp = list(s[:5])
                # no need to propagate the flags
                tmp.append(new_value[0])
                final_spec.append(tuple(tmp))
            else:
                final_spec.append(s)

        op_type = operations.MUTATE_IN.value
        return subdoc_operation(
            **self._get_connection_args(),
            **final_args,
            key=key,
            spec=final_spec,
            op_type=op_type,
        )

    def _validate_delta_initial(self, delta=None, initial=None) -> None:
        # @TODO: remove deprecation next .minor
        # from couchbase.collection import DeltaValueDeprecated, SignedInt64Deprecated
        if delta is not None:
            if not DeltaValueBase.is_valid(delta):
                raise InvalidArgumentException("Argument is not valid DeltaValue")
        if initial is not None:
            if not SignedInt64Base.is_valid(initial):
                raise InvalidArgumentException("Argument is not valid SignedInt64")

    def _get_and_validate_delta_initial(self, final_args):
        initial = final_args.get('initial', None)
        delta = final_args.get('delta', None)
        if not initial:
            initial = SignedInt64Base(0)
        if not delta:
            delta = DeltaValueBase(1)

        self._validate_delta_initial(delta=delta, initial=initial)

        return delta, initial

    def increment(
        self,
        key,  # type: str
        *opts,  # type: IncrementOptions
        **kwargs,  # type: Any
    ) -> Optional[CounterResult]:
        final_args = forward_args(kwargs, *opts)
        if not final_args.get('initial', None):
            final_args['initial'] = SignedInt64Base(0)
        if not final_args.get('delta', None):
            final_args['delta'] = DeltaValueBase(1)

        self._validate_delta_initial(delta=final_args['delta'],
                                     initial=final_args['initial'])

        op_type = operations.INCREMENT.value
        return binary_operation(**self._get_connection_args(),
                                **final_args,
                                key=key,
                                op_type=op_type)

    def decrement(
        self,
        key,  # type: str
        *opts,  # type: DecrementOptions
        **kwargs,  # type: Any
    ) -> Optional[CounterResult]:
        final_args = forward_args(kwargs, *opts)
        if not final_args.get('initial', None):
            final_args['initial'] = SignedInt64Base(0)
        if not final_args.get('delta', None):
            final_args['delta'] = DeltaValueBase(1)

        self._validate_delta_initial(delta=final_args['delta'],
                                     initial=final_args['initial'])

        op_type = operations.DECREMENT.value
        return binary_operation(**self._get_connection_args(),
                                **final_args,
                                key=key,
                                op_type=op_type)

    def append(
        self,
        key,  # type: str
        value,  # type: Union[str,bytes,bytearray]
        *opts,  # type: AppendOptions
        **kwargs,  # type: Any
    ) -> Optional[MutationResult]:
        final_args = forward_args(kwargs, *opts)
        if isinstance(value, str):
            value = value.encode("utf-8")
        elif isinstance(value, bytearray):
            value = bytes(value)

        if not isinstance(value, bytes):
            raise ValueError(
                "The value provided must of type str, bytes or bytearray.")

        op_type = operations.APPEND.value
        return binary_operation(**self._get_connection_args(),
                                **final_args,
                                key=key,
                                op_type=op_type,
                                value=value)

    def prepend(
        self,
        key,  # type: str
        value,  # type: Union[str,bytes,bytearray]
        *opts,  # type: PrependOptions
        **kwargs,  # type: Any
    ) -> Optional[MutationResult]:
        final_args = forward_args(kwargs, *opts)
        if isinstance(value, str):
            value = value.encode("utf-8")
        elif isinstance(value, bytearray):
            value = bytes(value)

        if not isinstance(value, bytes):
            raise ValueError(
                "The value provided must of type str, bytes or bytearray.")

        op_type = operations.PREPEND.value
        return binary_operation(**self._get_connection_args(),
                                **final_args,
                                key=key,
                                op_type=op_type,
                                value=value)
