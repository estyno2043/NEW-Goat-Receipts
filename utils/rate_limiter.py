import time
import sqlite3
from datetime import datetime, timedelta
import discord
from utils.db_utils import execute_query

class ReceiptRateLimiter:
    def __init__(self):
        # Rate limiting is disabled
        pass

    def _initialize_table(self):
        """No-op function for compatibility"""
        return True

    def add_receipt(self, user_id):
        """
        No rate limiting - always allow receipts
        Returns (is_allowed, count, reset_time, remaining_time)
        """
        return True, 0, 0, 0

    def record_successful_email(self, user_id):
        """
        No rate limiting - always allow emails
        Returns (count, reset_time, remaining_time)
        """
        return 0, 0, 0

    def format_time_remaining(self, seconds):
        """Legacy function for compatibility"""
        return "now"

    def get_rate_limit_message(self, user_id):
        """No rate limiting - never return a limit message"""
        return None

    def check_review_request(self, user_id, current_count, bot, channel):
        """No review requests - disabled"""
        return False

    def reset_user_limit(self, user_id):
        """No-op function for compatibility"""
        return True

    async def _send_review_message(self, channel, user_id=None):
        """No-op function for compatibility"""
        pass