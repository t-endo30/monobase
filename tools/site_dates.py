#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日付表示に使うサイト共通の日本時間。"""
from datetime import datetime
from zoneinfo import ZoneInfo


def today_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()
