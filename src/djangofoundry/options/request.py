"""*****************************************************************************
*                                                                             *
* Metadata:                                                                   *
*                                                                             *
* 	File: request.py                                                           *
* 	Project: django-foundry                                                    *
* 	Created: 08 Jun 2023                                                       *
* 	Author: Jess Mann                                                          *
* 	Email: jmann@osc.ny.gov                                                    *
*                                                                             *
* 	-----                                                                      *
*                                                                             *
* 	Last Modified: Thu Oct 19 2023                                             *
* 	Modified By: Jess Mann                                                     *
*                                                                             *
* 	-----                                                                      *
*                                                                             *
* 	Copyright (c) 2023 NYS Office of the State Comptroller                     *
****************************************************************************"""

from enum import Enum


class RequestType(Enum):
    """
    Valid types of HTTP Requests
    """

    GET = "GET"
    POST = "POST"
    SOAP = "SOAP"
