/*
 *   Copyright 2016-2022. Couchbase, Inc.
 *   All Rights Reserved.
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

#pragma once

#include "../client.hxx"

#include <couchbase/operations/management/analytics.hxx>

class AnalyticsManagementOperations
{
  public:
    enum OperationType {
        UNKNOWN,
        CREATE_DATAVERSE,
        CREATE_DATASET,
        CREATE_INDEX,
        GET_ALL_DATASETS,
        GET_ALL_INDEXES,
        DROP_DATAVERSE,
        DROP_DATASET,
        DROP_INDEX,
        GET_PENDING_MUTATIONS,
        LINK_CREATE,
        LINK_CONNECT,
        GET_ALL_LINKS,
        LINK_DISCONNECT,
        LINK_REPLACE,
        DROP_LINK
    };

    AnalyticsManagementOperations()
      : AnalyticsManagementOperations{ UNKNOWN }
    {
    }
    constexpr AnalyticsManagementOperations(AnalyticsManagementOperations::OperationType op)
      : operation{ op }
    {
    }

    operator OperationType() const
    {
        return operation;
    }
    // lets prevent the implicit promotion of bool to int
    explicit operator bool() = delete;
    constexpr bool operator==(AnalyticsManagementOperations op) const
    {
        return operation == op.operation;
    }
    constexpr bool operator!=(AnalyticsManagementOperations op) const
    {
        return operation != op.operation;
    }

    static const char* ALL_OPERATIONS(void)
    {
        const char* ops = "CREATE_DATAVERSE "
                          "CREATE_DATASET "
                          "CREATE_INDEX "
                          "GET_ALL_DATASETS "
                          "GET_ALL_INDEXES "
                          "DROP_DATAVERSE "
                          "DROP_DATASET "
                          "DROP_INDEX "
                          "GET_PENDING_MUTATIONS "
                          "LINK_CREATE "
                          "LINK_CONNECT "
                          "GET_ALL_LINKS "
                          "LINK_DISCONNECT "
                          "LINK_REPLACE "
                          "DROP_LINK ";

        return ops;
    }

  private:
    OperationType operation;
};

struct analytics_mgmt_options {
    PyObject* op_args;
    AnalyticsManagementOperations::OperationType op_type = AnalyticsManagementOperations::UNKNOWN;
    std::chrono::milliseconds timeout_ms = couchbase::timeout_defaults::management_timeout;
};

PyObject*
handle_analytics_mgmt_op(connection* conn, struct analytics_mgmt_options* options, PyObject* pyObj_callback, PyObject* pyObj_errback);

void
add_analytics_mgmt_ops_enum(PyObject* pyObj_module, PyObject* pyObj_enum_class);
