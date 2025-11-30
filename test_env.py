import os

print("DB_NAME:", os.environ.get('DB_NAME', 'NOT SET'))
print("DB_USER:", os.environ.get('DB_USER', 'NOT SET'))
print("DB_PASSWORD:", os.environ.get('DB_PASSWORD', 'NOT SET'))
print("DB_HOST:", os.environ.get('DB_HOST', 'NOT SET'))
print("DB_PORT:", os.environ.get('DB_PORT', 'NOT SET'))