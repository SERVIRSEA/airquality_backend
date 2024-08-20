from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
import string
import random
import hashlib
from django.utils.timezone import now

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

class City(models.Model):
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    worldcity = models.BooleanField(default=False) 
    megacity = models.BooleanField(default=False)
    lat = models.DecimalField(max_digits=9, decimal_places=6)  
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    meganame = models.CharField(max_length=100)
    idc = models.IntegerField()
    def __str__(self):
        return self.city

class country_table(models.Model):
    adm0_gid = models.CharField(max_length=10)
    adm0_id = models.IntegerField()
    adm0_name = models.CharField(max_length=100)
    lat = models.DecimalField(max_digits=9, decimal_places=4, default=0)  
    lon = models.DecimalField(max_digits=9, decimal_places=4, default=0)
    def __str__(self):
        return f"{self.adm0_id} - {self.adm0_name}"
    
class province_table(models.Model):
    adm0_gid = models.CharField(max_length=10)
    adm0_name = models.CharField(max_length=100)
    adm1_gid = models.CharField(max_length=10)
    adm1_id = models.IntegerField()
    adm1_name = models.CharField(max_length=100)
    lat = models.DecimalField(max_digits=9, decimal_places=4, default=0)  
    lon = models.DecimalField(max_digits=9, decimal_places=4, default=0)
    majorcity = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.adm1_id} - {self.adm1_name}"
 
class district_table(models.Model):
    adm0_gid = models.CharField(max_length=10)
    adm0_id = models.IntegerField()
    adm0_name = models.CharField(max_length=100)
    adm1_gid = models.CharField(max_length=10)
    adm1_id = models.IntegerField()
    adm1_name = models.CharField(max_length=100)
    adm2_gid = models.CharField(max_length=15)
    adm2_id = models.IntegerField()
    adm2_name = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.adm2_id} - {self.adm2_name}"
    
class CityPM25(models.Model):
    idc = models.IntegerField(default=False)  
    pm25 = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Store PM2.5 values.
    init_date = models.DateField(default=False) 
    forecast_time = models.CharField(default=False) 
    def __str__(self):
        return f"{self.idc.city} PM2.5 Data" 

class CityNO2(models.Model):
    idc = models.IntegerField(default=False)  
    no2 = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Store PM2.5 values.
    init_date = models.DateField(default=False) 
    time = models.CharField(default=False) 
    def __str__(self):
        return f"{self.idc.city} PM2.5 Data"  
    
class Firm24h(models.Model):
    adm_lvl = models.CharField(max_length=10)  # Added max_length
    area_id = models.IntegerField(default=False)  # Added max_length
    area_name = models.CharField(max_length=100)  # Added max_length
    firmcount = models.IntegerField(default=False)  
    init_date = models.DateField(default=False) 
    def __str__(self):
        return f"{self.adm_lvl} - {self.area_name} - {self.init_date}"
    
class Firm48h(models.Model):
    adm_lvl = models.CharField(max_length=10)  # Added max_length
    area_id = models.IntegerField(default=False)  # Added max_length
    area_name = models.CharField(max_length=100)  # Added max_length
    firmcount = models.IntegerField(default=False)  
    init_date = models.DateField(default=False) 
    def __str__(self):
        return f"{self.adm_lvl} - {self.area_name} - {self.init_date}"
    
class Firmsingle(models.Model):
    adm_lvl = models.CharField(max_length=10)  # Added max_length
    area_id = models.IntegerField(default=False)  # Added max_length
    area_name = models.CharField(max_length=100)  # Added max_length
    firmcount = models.IntegerField(default=False)  
    init_date = models.DateField(default=False) 
    def __str__(self):
        return f"{self.adm_lvl} - {self.area_name} - {self.init_date}"
    
class PM25(models.Model):
    adm_lvl = models.CharField(max_length=10)  # Added max_length
    area_id = models.IntegerField(default=False)  # Added max_length
    area_name = models.CharField(max_length=100)  # Added max_length
    min = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    max = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    init_date = models.DateField()  # Removed default value
    forecast_time = models.DateTimeField()  # Changed to DateTimeField for accurate datetime storage

    class Meta:
        unique_together = ('adm_lvl', 'area_id', 'init_date', 'forecast_time')  # Added unique constraint

    def __str__(self):
        return f"{self.adm_lvl} - {self.area_name} - {self.init_date} - {self.forecast_time}"
  
class RequestData(models.Model):
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    purpose = models.CharField(max_length=300)
    data = models.CharField(max_length=50, default='')
    date = models.DateTimeField(default=now, null=True, blank=True)

    def __str__(self):
        return f"{self.name} from {self.organization}"