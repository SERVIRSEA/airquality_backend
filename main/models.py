from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
import string
import random
import hashlib

class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key_name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Check if key is already set, and if so, do not generate a new key
        if not self.key:
            # Generate a new complex API key based on key_name if it's provided
            if self.key_name:
                self.key = self.generate_complex_api_key(f"{str(self.user.username)}.")

        super(APIKey, self).save(*args, **kwargs)

    def generate_complex_api_key(self, prefix, length=64):
        # Define character set for random characters
        characters = string.ascii_letters + string.digits

        # Calculate the number of random characters needed
        num_random_chars = length - len(prefix)

        if num_random_chars <= 0:
            raise ValueError("API key length must be greater than the length of the prefix")

        # Generate random characters
        random_chars = ''.join(random.choice(characters) for _ in range(num_random_chars))

        # Combine prefix and random characters to create the API key
        api_key = prefix + random_chars

        return api_key

    def set_raw_api_key(self, raw_api_key):
        # Set the raw API key value (used on the frontend)
        self.raw_api_key = raw_api_key

    def save_hashed_api_key(self):
        # Hash the raw API key and store it as the hashed API key
        if hasattr(self, 'raw_api_key') and self.raw_api_key:
            self.key = self.hash_api_key(self.raw_api_key)
        else:
            raise ValueError("Raw API key is missing")

    def hash_api_key(self, input_str):
        # Hash the input string using a strong cryptographic hash function (e.g., SHA-256)
        return hashlib.sha256(input_str.encode()).hexdigest()
