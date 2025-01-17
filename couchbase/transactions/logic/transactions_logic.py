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

import logging
from typing import (TYPE_CHECKING,
                    Callable,
                    Optional)

from couchbase.pycbc_core import (create_transactions,
                                  destroy_transactions,
                                  run_transaction)

if TYPE_CHECKING:
    from couchbase.logic.cluster import ClusterLogic
    from couchbase.options import TransactionConfig, TransactionOptions
    from couchbase.transactions.logic.attempt_context_logic import AttemptContextLogic

log = logging.getLogger(__name__)


class TransactionsLogic:
    def __init__(self,
                 cluster,  # type: ClusterLogic
                 config   # type: TransactionConfig
                 ):
        self._config = config
        self._loop = None
        # cluster always has a default (DefaultJSONSerializer)
        self._serializer = cluster._default_serializer
        if hasattr(cluster, "loop"):
            self._loop = cluster.loop
        self._txns = create_transactions(cluster.connection, self._config._base)
        log.info('created transactions object using config=%s, serializer=%s', self._config, self._serializer)

    def run(self,
            logic,  # type: Callable[[AttemptContextLogic], None]
            per_txn_config=None,  # type: Optional[TransactionOptions],
            **kwargs
            ):
        if per_txn_config:
            kwargs['per_txn_config'] = per_txn_config._base
        return run_transaction(txns=self._txns, logic=logic, **kwargs)

    def close(self, **kwargs):
        log.info('shutting down transactions...')
        return destroy_transactions(txns=self._txns, **kwargs)
