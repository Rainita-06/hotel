-- MySQL initialization script to fix user permissions
-- This script runs when the MySQL container is first created

-- Grant all privileges on the hotel database to hotel_user from any host
-- This ensures the user created by MYSQL_USER environment variable can connect from any IP
GRANT ALL PRIVILEGES ON hotel.* TO 'hotel_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Show grants for verification
SHOW GRANTS FOR 'hotel_user'@'%';