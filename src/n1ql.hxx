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

#include "client.hxx"
#include "result.hxx"

streamed_result*
handle_n1ql_query(PyObject* self, PyObject* args, PyObject* kwargs);

template<typename scan_consistency_type>
scan_consistency_type
str_to_scan_consistency_type(std::string consistency)
{
    if (consistency.compare("not_bounded") == 0) {
        return scan_consistency_type::not_bounded;
    }
    if (consistency.compare("request_plus") == 0) {
        return scan_consistency_type::request_plus;
    }

    // TODO: better exception
    PyErr_SetString(PyExc_ValueError, fmt::format("Invalid Scan Consistency type {}", consistency).c_str());
    return {};
}

std::string
scan_consistency_type_to_string(couchbase::query_scan_consistency consistency);

std::vector<couchbase::mutation_token>
get_mutation_state(PyObject* pyObj_mutation_state);

std::string
profile_mode_to_str(couchbase::query_profile_mode profile_mode);

couchbase::query_profile_mode
str_to_profile_mode(std::string profile_mode);
