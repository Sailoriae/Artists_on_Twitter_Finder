#!/usr/bin/python3
# coding: utf-8

from socketserver import ThreadingMixIn
from http.server import HTTPServer


"""
Pour faire du multi-thread du serveur HTTP
Source : https://pymotw.com/2/BaseHTTPServer/index.html#threading-and-forking
"""
class Threaded_HTTP_Server ( ThreadingMixIn, HTTPServer ) :
    """Handle requests in a separate thread."""
